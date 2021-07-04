import collections
import itertools
import json
import os
from functools import lru_cache
from typing import List, Deque, Optional
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from dragoneye.cloud_scanner.base_cloud_scanner import BaseCloudScanner
from dragoneye.cloud_scanner.gcp.gcp_scan_settings import GcpCloudScanSettings
from dragoneye.config import config
from dragoneye.utils.misc_utils import elapsed_time, init_directory, custom_serializer, get_dynamic_values_from_files
from dragoneye.utils.threading_utils import ThreadedFunctionData, execute_parallel_functions_in_threads
from dragoneye.utils.app_logger import logger


class GcpScanner(BaseCloudScanner):
    def __init__(self, credentials, settings: GcpCloudScanSettings):
        super().__init__(settings)
        self.credentials = credentials
        self.services: list = []
        self.project_id = settings.project_id

    @elapsed_time('Scanning GCP live environment took {} seconds')
    def scan(self) -> str:
        self.account_data_dir = init_directory(self.settings.output_path, self.settings.account_name, self.settings.clean)

        dependent_commands, independent_commands = self._get_scan_commands()

        non_dependable_tasks: List[ThreadedFunctionData] = []
        dependable_tasks: List[ThreadedFunctionData] = []
        deque_tasks: Deque[List[ThreadedFunctionData]] = collections.deque()

        for independent_command in independent_commands:
            non_dependable_tasks.append(ThreadedFunctionData(
                self._execute_scan_commands,
                (independent_command,),
                'exception on command {}'.format(independent_command)))

        deque_tasks.append(non_dependable_tasks)

        for dependent_command in dependent_commands:
            dependable_tasks.append(ThreadedFunctionData(
                self._execute_scan_commands,
                (dependent_command,),
                'exception on command {}'.format(dependent_command)))

        for dependable_task in dependable_tasks:
            deque_tasks.append([dependable_task])
        execute_parallel_functions_in_threads(deque_tasks, config.get('MAX_WORKERS'))

        self._print_summary()

        for service in self.services:
            service.close()

        return os.path.abspath(os.path.join(self.account_data_dir, '..'))

    def _execute_scan_commands(self, scan_command: dict) -> None:
        service_name = scan_command['ServiceName']
        api_version = scan_command['ApiVersion']
        resource_type = scan_command['ResourceType']
        method = scan_command['Method']
        output_file = os.path.join(self.account_data_dir, f'{service_name}-{api_version}-{resource_type}-{method}.json')
        if os.path.isfile(output_file):
            # Data already scanned, so skip
            logger.warning('Response already present at {}'.format(output_file))
            return

        service = self._create_service(service_name, api_version)
        resource_response = getattr(service, resource_type)()

        all_parameters = self._get_parameters(scan_command, self.account_data_dir)
        all_items = []
        all_call_summary = []
        call_summary = {
            "service": service_name,
            "api_version": api_version,
            "resource_type": resource_type,
            'method': method
        }

        if all_parameters is not None:
            for parameters in all_parameters:
                updated_call_summary = call_summary.copy()
                updated_call_summary['parameters'] = parameters
                all_items.extend(self._get_results(updated_call_summary, resource_response))
                all_call_summary.append(updated_call_summary)
        else:
            updated_call_summary = call_summary.copy()
            updated_call_summary['parameters'] = {}
            all_items.extend(self._get_results(updated_call_summary, resource_response))
            all_call_summary.append(updated_call_summary)

        with open(output_file, "w") as file:
            json.dump({'value': all_items}, file, indent=4, default=custom_serializer)

        for call_summary in all_call_summary:
            self.summary.put_nowait(call_summary)
            if any(x in call_summary for x in ('error', 'exception')):
                logger.error(self._parse_error(call_summary))
            else:
                logger.info(f'Results from {self._get_call_representation(call_summary)} were saved to {output_file}')

    @lru_cache(maxsize=None)
    def _create_service(self, service_name: str, version: str):
        service = build(service_name, version, credentials=self.credentials)
        self.services.append(service)
        return service

    def _get_parameters(self, scan_command: dict, account_data_dir: str) -> Optional[List[dict]]:
        if not scan_command.get('Parameters'):
            return None  # No parameters required

        multi_params = []
        single_param_product = []
        single_param_data = {}
        multi_param_data = {}

        for parameter in scan_command.get('Parameters', []):
            param_names = parameter['Name']
            param_dynamic_value = parameter['Value']
            param_real_values = get_dynamic_values_from_files(param_dynamic_value, account_data_dir)
            # Multiple parameters from same object
            if ' ' in param_names:
                for param_real_value in param_real_values:
                    zipped = zip(param_names.split(' '), param_real_value.split(' '))
                    for param, value in zipped:
                        if param not in multi_param_data:
                            multi_param_data[param] = []
                        if value not in multi_param_data[param]:
                            multi_param_data[param].append(value)
            # One parameter from same object
            else:
                if '$project' in param_dynamic_value:
                    single_param_data[param_names] = [param_dynamic_value.replace('$project', self.project_id)]
                else:
                    single_param_data[param_names] = param_real_values

        keys = single_param_data.keys()
        for product in itertools.product(*single_param_data.values()):
            if product:
                single_param_product.append(dict(zip(keys, product)))

        multi_param_length = len(next(iter(multi_param_data.values()), []))
        for index in range(multi_param_length - 1):
            multi_param = {}
            for key, items in multi_param_data.items():
                multi_param[key] = items[index]
            multi_params.append(multi_param)

        if multi_params and single_param_product:
            stitched_params = []
            for multi_param in multi_params:
                for single_param in single_param_product:
                    multi_param_copy = multi_param.copy()
                    multi_param_copy.update(single_param)
                    stitched_params.append(multi_param_copy)
            return stitched_params
        else:
            return multi_params or single_param_product

    def _get_results(self, call_summary: dict, resource_response):
        all_items = []
        try:
            logger.info(f'Invoking {self._get_call_representation(call_summary)}')
            method_name = call_summary['method']
            method_name_next = f'{method_name}_next'
            method = getattr(resource_response, method_name)
            request = method(**call_summary['parameters'])

            while request is not None:
                response = request.execute()
                if 'list' in method_name or 'nextPageToken' in response:
                    for values in response.values():
                        if isinstance(values, list):
                            all_items.extend(values)
                            break

                    request = getattr(resource_response, method_name_next)(previous_request=request, previous_response=response)
                else:
                    if response:
                        all_items.append(response)
                    break
        except HttpError as ex:
            call_summary['error'] = json.loads(ex.content.decode('utf-8'))['error']
        except Exception as ex:
            call_summary['exception'] = str(ex)

        return all_items

    @staticmethod
    def _get_call_representation(call_summary: dict) -> str:
        parameters_text = ', '.join(f'{key}={value}' for key, value in call_summary['parameters'].items())
        return f'{call_summary["service"]}.{call_summary["api_version"]}.{call_summary["resource_type"]}.{call_summary["method"]}({parameters_text})'

    @staticmethod
    def _parse_error(call_summary: dict) -> str:
        if 'error' in call_summary:
            error_code = call_summary['error']['code']
            error_msg = call_summary['error']['message']
            return f'{GcpScanner._get_call_representation(call_summary)}: {error_code} - {error_msg}'
        else:
            return f'{GcpScanner._get_call_representation(call_summary)}: {call_summary["exception"]}'
