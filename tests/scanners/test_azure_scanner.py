import json
import os
import tempfile
import unittest
from unittest.mock import patch, ANY

from dragoneye.cloud_scanner.azure.azure_scanner import AzureScanner, AzureCloudScanSettings
from mockito import when, unstub, mock
import dragoneye


class TestAzureScanner(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.token = 'token'
        cls.auth = {'Authorization': cls.token}
        cls.subscription_id = 'subscription-id'
        cls.account_name = 'test-account'
        cls.resource_groups = ['resourceGroup1', 'resourceGroup2']
        cls.resource_groups_text = json.dumps({"value": [{"name": cls.resource_groups[0]}, {"name": cls.resource_groups[1]}]})

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.azure_settings = AzureCloudScanSettings(
            commands_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources', 'azure_scan_commands.yaml'),
            subscription_id=self.subscription_id,
            account_name=self.account_name, 
            should_clean_before_scan=True,
            output_path=self.temp_dir.name
        )
        when(dragoneye.cloud_scanner.azure.azure_scanner).invoke_get_request(ANY, ANY).thenReturn(mock({'status_code': 200, 'text': '{}'}))

    def tearDown(self) -> None:
        self.temp_dir.cleanup()
        unstub()

    def test_scan_ok_with_values(self):
        # Arrange
        rg_id = "/subscriptions/{}/resourceGroups/{}"
        ### Resource Groups
        when(dragoneye.cloud_scanner.azure.azure_scanner)\
            .invoke_get_request(
            f'https://management.azure.com/subscriptions/{self.subscription_id}/resourcegroups?api-version=2020-09-01',
            self.auth) \
            .thenReturn(mock({'status_code': 200, 'text': self.resource_groups_text}))
        ### request1, resourceGroup1
        when(dragoneye.cloud_scanner.azure.azure_scanner)\
            .invoke_get_request(
            f'https://management.azure.com/subscriptions/{self.subscription_id}/resourceGroups/{self.resource_groups[0]}/providers/Microsoft.Compute/virtualMachines?api-version=2020-12-01',
            self.auth)\
            .thenReturn(mock({'status_code': 200, 'text': json.dumps({"value": [{"id": rg_id.format(self.subscription_id, self.resource_groups[0]), "vmName": f'{self.resource_groups[0]}-vm'}]})}))
        ### request1, resourceGroup2
        when(dragoneye.cloud_scanner.azure.azure_scanner) \
            .invoke_get_request(
            f'https://management.azure.com/subscriptions/{self.subscription_id}/resourceGroups/{self.resource_groups[1]}/providers/Microsoft.Compute/virtualMachines?api-version=2020-12-01',
            self.auth) \
            .thenReturn(mock({'status_code': 200, 'text': json.dumps({"value": [{"id": rg_id.format(self.subscription_id, self.resource_groups[1]), "vmName": f'{self.resource_groups[1]}-vm'}]})}))
        ### request2, vm1
        when(dragoneye.cloud_scanner.azure.azure_scanner)\
            .invoke_get_request(
            f'https://management.azure.com/subscriptions/{self.subscription_id}/resourceGroups/{self.resource_groups[0]}/providers/Microsoft.Compute/virtualMachines/{f"{self.resource_groups[0]}-vm"}?api-version=2020-12-01',
            self.auth)\
            .thenReturn(mock({'status_code': 200, 'text': json.dumps({"value": [{"id": rg_id.format(self.subscription_id, self.resource_groups[0]), "vmName": f'{self.resource_groups[0]}-vm'}]})}))
        ### request2, vm2
        when(dragoneye.cloud_scanner.azure.azure_scanner)\
            .invoke_get_request(
            f'https://management.azure.com/subscriptions/{self.subscription_id}/resourceGroups/{self.resource_groups[1]}/providers/Microsoft.Compute/virtualMachines/{f"{self.resource_groups[1]}-vm"}?api-version=2020-12-01',
            self.auth)\
            .thenReturn(mock({'status_code': 200, 'text': json.dumps({"value": [{"id": rg_id.format(self.subscription_id, self.resource_groups[1]), "vmName": f'{self.resource_groups[1]}-vm'}]})}))

        # Act
        scanner = AzureScanner(self.token, self.azure_settings)
        output_path = scanner.scan()
        account_data_dir = os.path.join(output_path, self.account_name)

        # Assert
        self.assertTrue(os.path.isfile(os.path.join(account_data_dir, 'resource-groups.json')))
        self.assertTrue(os.path.isfile(os.path.join(account_data_dir, 'request1.json')))
        self.assertTrue(os.path.isfile(os.path.join(account_data_dir, 'request2.json')))

        with open(os.path.join(account_data_dir, 'resource-groups.json'), 'r') as result_file:
            results = json.load(result_file)
            value = results['value']
            self.assertTrue(any(dic['name'] == self.resource_groups[0] for dic in value))
            self.assertTrue(any(dic['name'] == self.resource_groups[1] for dic in value))

        with open(os.path.join(account_data_dir, 'request1.json'), 'r') as result_file:
            results = json.load(result_file)
            value = results['value']
            self.assertTrue(any(dic['vmName'] == f'{self.resource_groups[0]}-vm' for dic in value))
            self.assertTrue(any(dic['vmName'] == f'{self.resource_groups[1]}-vm' for dic in value))
            self.assertTrue(any(dic['resourceGroup'] == self.resource_groups[0] for dic in value))
            self.assertTrue(any(dic['resourceGroup'] == self.resource_groups[1] for dic in value))

        with open(os.path.join(account_data_dir, 'request2.json'), 'r') as result_file:
            results = json.load(result_file)
            value = results['value']
            self.assertTrue(any(dic['vmName'] == f'{self.resource_groups[0]}-vm' for dic in value))
            self.assertTrue(any(dic['vmName'] == f'{self.resource_groups[1]}-vm' for dic in value))
            self.assertTrue(any(dic['resourceGroup'] == self.resource_groups[0] for dic in value))
            self.assertTrue(any(dic['resourceGroup'] == self.resource_groups[1] for dic in value))

    def test_scan_ok_no_resources(self):
        # Arrange
        ### Resource Groups
        when(dragoneye.cloud_scanner.azure.azure_scanner)\
            .invoke_get_request(
            f'https://management.azure.com/subscriptions/{self.subscription_id}/resourcegroups?api-version=2020-09-01',
            self.auth) \
            .thenReturn(mock({'status_code': 200, 'text': self.resource_groups_text}))
        ### request1, resourceGroup1
        when(dragoneye.cloud_scanner.azure.azure_scanner)\
            .invoke_get_request(
            f'https://management.azure.com/subscriptions/{self.subscription_id}/resourceGroups/{self.resource_groups[0]}/providers/Microsoft.Compute/virtualMachines?api-version=2020-12-01',
            self.auth)\
            .thenReturn(mock({'status_code': 200, 'text': json.dumps({"value": []})}))
        ### request1, resourceGroup2
        when(dragoneye.cloud_scanner.azure.azure_scanner) \
            .invoke_get_request(
            f'https://management.azure.com/subscriptions/{self.subscription_id}/resourceGroups/{self.resource_groups[1]}/providers/Microsoft.Compute/virtualMachines?api-version=2020-12-01',
            self.auth) \
            .thenReturn(mock({'status_code': 200, 'text': json.dumps({"value": []})}))

        # Act
        scanner = AzureScanner(self.token, self.azure_settings)
        output_path = scanner.scan()
        account_data_dir = os.path.join(output_path, self.account_name)

        # Assert
        self.assertTrue(os.path.isfile(os.path.join(account_data_dir, 'resource-groups.json')))
        self.assertTrue(os.path.isfile(os.path.join(account_data_dir, 'request1.json')))
        self.assertTrue(os.path.isfile(os.path.join(account_data_dir, 'request2.json')))

        with open(os.path.join(account_data_dir, 'resource-groups.json'), 'r') as result_file:
            results = json.load(result_file)
            value = results['value']
            self.assertTrue(any(dic['name'] == self.resource_groups[0] for dic in value))
            self.assertTrue(any(dic['name'] == self.resource_groups[1] for dic in value))

        with open(os.path.join(account_data_dir, 'request1.json'), 'r') as result_file:
            results = json.load(result_file)
            value = results['value']
            self.assertListEqual(value, list())

        with open(os.path.join(account_data_dir, 'request2.json'), 'r') as result_file:
            results = json.load(result_file)
            value = results['value']
            self.assertListEqual(value, list())

    @patch('logging.Logger.exception')
    def test_scan_failed_request(self, patched_logger):
        """
        Testing that even if a specific request raises an exception, we continue to scan and do not crash.
        """
        # Arrange
        rg_id = "/subscriptions/{}/resourceGroups/{}"
        ### Resource Groups
        when(dragoneye.cloud_scanner.azure.azure_scanner)\
            .invoke_get_request(
            f'https://management.azure.com/subscriptions/{self.subscription_id}/resourcegroups?api-version=2020-09-01',
            self.auth) \
            .thenReturn(mock({'status_code': 200, 'text': self.resource_groups_text}))
        ### request1, resourceGroup1
        when(dragoneye.cloud_scanner.azure.azure_scanner)\
            .invoke_get_request(
            f'https://management.azure.com/subscriptions/{self.subscription_id}/resourceGroups/{self.resource_groups[0]}/providers/Microsoft.Compute/virtualMachines?api-version=2020-12-01',
            self.auth)\
            .thenReturn(mock({'status_code': 200, 'text': json.dumps({"value": [{"id": rg_id.format(self.subscription_id, self.resource_groups[0]), "vmName": f'{self.resource_groups[0]}-vm'}]})}))
        ### request1, resourceGroup2
        when(dragoneye.cloud_scanner.azure.azure_scanner) \
            .invoke_get_request(
            f'https://management.azure.com/subscriptions/{self.subscription_id}/resourceGroups/{self.resource_groups[1]}/providers/Microsoft.Compute/virtualMachines?api-version=2020-12-01',
            self.auth) \
            .thenReturn(mock({'status_code': 200, 'text': json.dumps({"value": [{"id": rg_id.format(self.subscription_id, self.resource_groups[1]), "vmName": f'{self.resource_groups[1]}-vm'}]})}))
        ### request2, vm1
        when(dragoneye.cloud_scanner.azure.azure_scanner)\
            .invoke_get_request(
            f'https://management.azure.com/subscriptions/{self.subscription_id}/resourceGroups/{self.resource_groups[0]}/providers/Microsoft.Compute/virtualMachines/{f"{self.resource_groups[0]}-vm"}?api-version=2020-12-01',
            self.auth)\
            .thenReturn(mock({'status_code': 200, 'text': json.dumps({"value": [{"id": rg_id.format(self.subscription_id, self.resource_groups[0]), "vmName": f'{self.resource_groups[0]}-vm'}]})}))
        ### request2, vm2
        when(dragoneye.cloud_scanner.azure.azure_scanner)\
            .invoke_get_request(
            f'https://management.azure.com/subscriptions/{self.subscription_id}/resourceGroups/{self.resource_groups[1]}/providers/Microsoft.Compute/virtualMachines/{f"{self.resource_groups[1]}-vm"}?api-version=2020-12-01',
            self.auth)\
            .thenReturn(mock({'status_code': 200, 'text': json.dumps({"value": [{"id": rg_id.format(self.subscription_id, self.resource_groups[1]), "vmName": f'{self.resource_groups[1]}-vm'}]})}))
        ### request3
        when(dragoneye.cloud_scanner.azure.azure_scanner)\
            .invoke_get_request(
            f'https://management.azure.com/subscriptions/{self.subscription_id}/providers/Microsoft.Compute/request3?api-version=2020-12-01',
            self.auth)\
            .thenRaise(Exception('some exception'))

        # Act
        scanner = AzureScanner(self.token, self.azure_settings)
        output_path = scanner.scan()
        account_data_dir = os.path.join(output_path, self.account_name)

        # Assert
        self.assertTrue(os.path.isfile(os.path.join(account_data_dir, 'resource-groups.json')))
        self.assertTrue(os.path.isfile(os.path.join(account_data_dir, 'request1.json')))
        self.assertTrue(os.path.isfile(os.path.join(account_data_dir, 'request2.json')))
        self.assertFalse(os.path.isfile(os.path.join(account_data_dir, 'request3.json')))

        with open(os.path.join(account_data_dir, 'resource-groups.json'), 'r') as result_file:
            results = json.load(result_file)
            value = results['value']
            self.assertTrue(any(dic['name'] == self.resource_groups[0] for dic in value))
            self.assertTrue(any(dic['name'] == self.resource_groups[1] for dic in value))

        with open(os.path.join(account_data_dir, 'request1.json'), 'r') as result_file:
            results = json.load(result_file)
            value = results['value']
            self.assertTrue(any(dic['vmName'] == f'{self.resource_groups[0]}-vm' for dic in value))
            self.assertTrue(any(dic['vmName'] == f'{self.resource_groups[1]}-vm' for dic in value))
            self.assertTrue(any(dic['resourceGroup'] == self.resource_groups[0] for dic in value))
            self.assertTrue(any(dic['resourceGroup'] == self.resource_groups[1] for dic in value))

        with open(os.path.join(account_data_dir, 'request2.json'), 'r') as result_file:
            results = json.load(result_file)
            value = results['value']
            self.assertTrue(any(dic['vmName'] == f'{self.resource_groups[0]}-vm' for dic in value))
            self.assertTrue(any(dic['vmName'] == f'{self.resource_groups[1]}-vm' for dic in value))
            self.assertTrue(any(dic['resourceGroup'] == self.resource_groups[0] for dic in value))
            self.assertTrue(any(dic['resourceGroup'] == self.resource_groups[1] for dic in value))

        call_args = '\n'.join(str(arg) for arg in patched_logger.call_args)
        self.assertIn('some exception', call_args)
