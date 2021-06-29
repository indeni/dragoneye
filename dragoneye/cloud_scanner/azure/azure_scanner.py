import collections
import os
from typing import List, Deque

import json

from requests import Response

from dragoneye.cloud_scanner.azure.azure_scan_settings import AzureCloudScanSettings
from dragoneye.cloud_scanner.base_cloud_scanner import BaseCloudScanner
from dragoneye.config import config
from dragoneye.utils.misc_utils import elapsed_time, invoke_get_request, init_directory, get_dynamic_values_from_files, custom_serializer
from dragoneye.utils.app_logger import logger
from dragoneye.utils.threading_utils import ThreadedFunctionData, execute_parallel_functions_in_threads


class AzureScanner(BaseCloudScanner):

    def __init__(self, auth_header: str, settings: AzureCloudScanSettings):
        super().__init__(settings)
        self.auth_header = auth_header
        self.subscription_id = settings.subscription_id

    @elapsed_time('Scanning Azure live environment took {} seconds')
    def scan(self) -> str:
        headers = {
            'Authorization': self.auth_header
        }

        self.account_data_dir = init_directory(self.settings.output_path, self.settings.account_name, self.settings.clean)
        resource_groups = self._get_resource_groups(headers)

        dependent_commands, independent_commands = self._get_scan_commands()

        non_dependable_tasks: List[ThreadedFunctionData] = []
        dependable_tasks: List[ThreadedFunctionData] = []
        deque_tasks: Deque[List[ThreadedFunctionData]] = collections.deque()

        for independent_command in independent_commands:
            non_dependable_tasks.append(ThreadedFunctionData(
                self._execute_scan_commands,
                (independent_command, headers, resource_groups),
                'exception on command {}'.format(independent_command)))

        deque_tasks.append(non_dependable_tasks)

        for dependent_command in dependent_commands:
            dependable_tasks.append(ThreadedFunctionData(
                self._execute_scan_commands,
                (dependent_command, headers, resource_groups),
                'exception on command {}'.format(dependent_command)))

        for dependable_task in dependable_tasks:
            deque_tasks.append([dependable_task])
        execute_parallel_functions_in_threads(deque_tasks, config.get('MAX_WORKERS'))

        self._print_summary()

        return os.path.abspath(os.path.join(self.account_data_dir, '..'))

    def _execute_scan_commands(self, scan_command: dict, headers: dict, resource_groups: List[str]) -> None:
        try:
            output_file = self._get_result_file_path(self.account_data_dir, scan_command['Name'])
            if os.path.isfile(output_file):
                # Data already scanned, so skip
                logger.warning('Response already present at {}'.format(output_file))
                return

            request = scan_command['Request']
            parameters = scan_command.get('Parameters', [])
            base_url = request.replace('{subscriptionId}', self.subscription_id)
            results = self._get_results(base_url, headers, parameters, self.account_data_dir, resource_groups)
            self._save_result(results, output_file)
            for url in results['urls']:
                logger.info(f'Results from {url} were saved to {output_file}')
        except Exception as ex:
            logger.exception('Exception occurred: {} while running command {}'.format(ex, scan_command))

    def _save_result(self, result: dict, filepath: str) -> None:
        self._add_resource_group(result)
        with open(filepath, "w") as file:
            json.dump(result, file, indent=4, default=custom_serializer)

    @staticmethod
    def _build_urls(_url: str, parameters: List[dict], account_data_dir: str, resource_groups: List[str]):
        urls_with_params = []
        if parameters:
            for parameter in parameters:
                param_names = parameter['Name']
                param_dynamic_value = parameter['Value']
                param_real_values = get_dynamic_values_from_files(param_dynamic_value, account_data_dir)

                for param_real_value in param_real_values:
                    modified_url = _url
                    zipped = zip(param_names.split(' '), param_real_value.split(' '))
                    for param, value in zipped:
                        modified_url = modified_url.replace('{{{0}}}'.format(param), value)

                    urls_with_params.append(modified_url)
        else:
            urls_with_params.append(_url)

        complete_urls = []

        for _url in urls_with_params:
            if '/{resourceGroupName}/' in _url:
                for resource_group in resource_groups:
                    complete_urls.append(_url.replace('{{{0}}}'.format('resourceGroupName'), resource_group))
            else:
                complete_urls.append(_url)

        return complete_urls

    def _get_results(self, base_url: str, headers: dict, parameters: List[dict], account_data_dir: str, resource_groups: List[str]) -> dict:
        results = {'value': []}
        urls = AzureScanner._build_urls(base_url, parameters, account_data_dir, resource_groups)
        for url in urls:
            logger.info(f'Invoking {url}')
            call_summary = {
                'request': url
            }
            response = invoke_get_request(url, headers, on_giveup=self._default_on_backoff_giveup)
            if response.status_code == 200:
                AzureScanner._concat_results(results, response)
            else:
                call_summary['error'] = json.loads(response.content.decode('utf-8'))['error']
                logger.error(self._parse_error(call_summary))
            self.summary.put_nowait(call_summary)
        results['urls'] = urls
        return results

    @staticmethod
    def _default_on_backoff_giveup(details: dict) -> None:
        logger.error('Given up on request for {args[0]} after {tries} tries'.format(**details))

    @staticmethod
    def _concat_results(results: dict, response: Response) -> None:
        if response.status_code == 200:
            result = json.loads(response.text)
            if 'value' in result:
                results['value'].extend(result['value'])
            else:
                if isinstance(result, list):
                    results['value'].extend(result)
                else:
                    results['value'].append(result)

    def _get_resource_groups(self, headers: dict) -> List[str]:
        url = f'https://management.azure.com/subscriptions/{self.subscription_id}/resourcegroups?api-version=2020-09-01'
        results = self._get_results(url, headers, [], self.account_data_dir, [])
        output_file = self._get_result_file_path(self.account_data_dir, 'resource-groups')
        self._save_result(results, output_file)
        logger.info(f'Results from {url} were saved to {output_file}')
        return get_dynamic_values_from_files('resource-groups.json|.value[].name', self.account_data_dir)

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

    @staticmethod
    def _parse_error(call_summary: dict):
        error_code = call_summary['error']['code']
        error_msg = call_summary['error']['message']
        return f'{call_summary["request"]}: {error_code} - {error_msg}'
