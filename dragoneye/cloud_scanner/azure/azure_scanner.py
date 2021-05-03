import collections
import os
from typing import List, Deque

import json

from requests import Response

from dragoneye.cloud_scanner.azure.azure_scan_settings import AzureCloudScanSettings
from dragoneye.cloud_scanner.base_cloud_scanner import BaseCloudScanner
from dragoneye.utils.misc_utils import elapsed_time, invoke_get_request, init_directory, load_yaml, get_dynamic_values_from_files, \
    custom_serializer
from dragoneye.utils.app_logger import logger
from dragoneye.utils.threading_utils import ThreadedFunctionData, execute_parallel_functions_in_threads


class AzureScanner(BaseCloudScanner):

    def __init__(self, auth_header: str, settings: AzureCloudScanSettings):
        self.auth_header = auth_header
        self.settings = settings

    @elapsed_time('Scanning Azure live environment took {} seconds')
    def scan(self) -> str:
        settings = self.settings
        subscription_id = self.settings.subscription_id
        account_name = settings.account_name

        headers = {
            'Authorization': self.auth_header
        }

        account_data_dir = init_directory(settings.output_path, account_name, settings.clean)
        scan_commands = load_yaml(settings.commands_path)
        resource_groups = self._get_resource_groups(headers, subscription_id, account_data_dir)

        dependable_commands = []
        non_dependable_commands = []
        for command in scan_commands:
            if "Parameters" in command:
                dependable_commands.append(command)
            else:
                non_dependable_commands.append(command)

        non_dependable_tasks: List[ThreadedFunctionData] = []
        dependable_tasks: List[ThreadedFunctionData] = []
        deque_tasks: Deque[List[ThreadedFunctionData]] = collections.deque()

        for non_dependable_command in non_dependable_commands:
            non_dependable_tasks.append(ThreadedFunctionData(
                self._execute_scan_commands,
                (non_dependable_command, subscription_id, headers, account_data_dir, resource_groups),
                'exception on command {}'.format(non_dependable_command)))

        deque_tasks.append(non_dependable_tasks)

        for dependable_command in dependable_commands:
            dependable_tasks.append(ThreadedFunctionData(
                self._execute_scan_commands,
                (dependable_command, subscription_id, headers, account_data_dir, resource_groups),
                'exception on command {}'.format(dependable_command)))

        deque_tasks.append(dependable_tasks)
        execute_parallel_functions_in_threads(deque_tasks, 20)

        return os.path.abspath(os.path.join(account_data_dir, '..'))

    def _execute_scan_commands(self, scan_command: dict, subscription_id: str, headers: dict,
                               account_data_dir: str, resource_groups: List[str]) -> None:
        try:
            output_file = self._get_result_file_path(account_data_dir, scan_command['Name'])
            if os.path.isfile(output_file):
                # Data already scanned, so skip
                logger.warning('  Response already present at {}'.format(output_file))
                return

            request = scan_command['Request']
            parameters = scan_command.get('Parameters', [])
            url = request.replace('{subscriptionId}', subscription_id)
            results = AzureScanner._get_results(url, headers, parameters, account_data_dir, resource_groups)
            self._save_result(results, output_file)
        except Exception as ex:
            logger.exception('exception on command {}'.format(scan_command), exc_info=ex)

    def _save_result(self, result: dict, filepath: str) -> None:
        self._add_resource_group(result)
        with open(filepath, "w+") as file:
            json.dump(result, file, indent=4, default=custom_serializer)

    @staticmethod
    def _get_results(url: str, headers: dict, parameters: List[dict], account_data_dir: str, resource_groups: List[str]) -> dict:
        results = {'value': []}
        if parameters:
            for parameter in parameters:
                param_names = parameter['Name']
                param_dynamic_value = parameter['Value']
                param_real_values = get_dynamic_values_from_files(param_dynamic_value, account_data_dir)

                for param_real_value in param_real_values:
                    modified_url = url
                    zipped = zip(param_names.split(' '), param_real_value.split(' '))
                    for param, value in zipped:
                        modified_url = modified_url.replace('{{{0}}}'.format(param), value)

                    AzureScanner._get_results_for_resource_groups(results, modified_url, headers, resource_groups)
        else:
            AzureScanner._get_results_for_resource_groups(results, url, headers, resource_groups)

        return results

    @staticmethod
    def _get_results_for_resource_groups(results: dict, modified_url: str, headers: dict, resource_groups: List[str]) -> None:
        if '/{resourceGroupName}/' in modified_url:
            for resource_group in resource_groups:
                response = invoke_get_request(modified_url.replace('{{{0}}}'.format('resourceGroupName'), resource_group), headers)
                AzureScanner._concat_results(results, response)
        else:
            response = invoke_get_request(modified_url, headers)
            AzureScanner._concat_results(results, response)

    @staticmethod
    def _concat_results(results: dict, response: Response) -> None:
        if response.status_code == 200:
            result = json.loads(response.text)
            if 'value' in result:
                results['value'].extend(result['value'])
            else:
                results['value'].append(result)

    def _get_resource_groups(self, headers: dict, subscription_id: str, account_data_dir: str) -> List[str]:
        results = AzureScanner._get_results(f'https://management.azure.com/subscriptions/{subscription_id}/resourcegroups?api-version=2020-09-01',
                                            headers, [], account_data_dir, [])
        output_file = self._get_result_file_path(account_data_dir, 'resource-groups')
        self._save_result(results, output_file)
        return get_dynamic_values_from_files('resource-groups.json|.value[].name', account_data_dir)

    @staticmethod
    def _add_resource_group(results: dict) -> None:
        for item in results['value']:
            if 'id' in item:
                item_id = item['id']
                try:
                    resource_group = item_id.split('resourceGroups/')[1].split('/')[0]
                    item['resourceGroup'] = resource_group
                except Exception:
                    pass

    @staticmethod
    def _get_result_file_path(account_data_dir: str, filename: str):
        return os.path.join(account_data_dir, filename + '.json')
