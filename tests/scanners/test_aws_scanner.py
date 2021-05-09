import json
import os
import tempfile
import unittest
from unittest.mock import ANY, patch

from botocore.exceptions import ClientError
from mockito import when, unstub, mock

import dragoneye
from dragoneye.cloud_scanner.aws.aws_scanner import AwsScanner, AwsCloudScanSettings
from dragoneye.utils.misc_utils import init_directory, make_directory


class TestAwsScanner(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.account_name = 'test-account'

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.aws_settings = AwsCloudScanSettings(
            commands_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources', 'aws_scan_commands.yaml'),
            account_name=self.account_name,
            should_clean_before_scan=False,
            output_path=self.temp_dir.name,
            default_region='us-east-1'
        )
        self.session = mock()
        self.mock_ec2_client = mock()
        when(self.mock_ec2_client).describe_regions().thenReturn({
            'Regions': [
                {
                    'Endpoint': 'ec2.us-east-1.amazonaws.com',
                    'RegionName': 'us-east-1',
                    'OptInStatus': 'opt-in-not-required'
                },
                {
                    'Endpoint': 'ec2.eu-west-1.amazonaws.com',
                    'RegionName': 'eu-west-1',
                    'OptInStatus': 'opt-in-not-required'
                }
            ]
        })
        self.regions = ['us-east-1', 'eu-west-1']
        self.scanner = AwsScanner(self.session, self.aws_settings)
        self.handler_config = self.scanner.handler_config
        self.mock_handler = mock({'meta': mock({'service_model': mock({'service_name': 'serviceName'})})})

        when(self.mock_handler).can_paginate(ANY).thenReturn(False)

        when(self.session).get_available_regions("service1").thenReturn(self.regions)
        when(self.session).get_available_regions("service2").thenReturn(self.regions)
        when(self.session).client('ec2', region_name=self.aws_settings.default_region).thenReturn(self.mock_ec2_client)
        when(self.session).client('service1', region_name='eu-west-1', config=self.handler_config).thenReturn(self.mock_handler)
        when(self.session).client('service1', region_name='us-east-1', config=self.handler_config).thenReturn(self.mock_handler)
        when(self.session).client('service2', region_name='eu-west-1', config=self.handler_config).thenReturn(self.mock_handler)
        when(self.session).client('service2', region_name='us-east-1', config=self.handler_config).thenReturn(self.mock_handler)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()
        unstub()

    def test_scan_ok(self):
        # Arrange
        request1_response = {'Items': [{'Key1': 'Value1', 'Key2': 'Value2'}]}
        request2_response = {'Items': [{'Key2': 'Value2'}]}
        request3_response = {'Items': [{'Key3': 'Value3'}]}

        when(self.mock_handler).request1().thenReturn(request1_response)
        when(self.mock_handler).request2(Key1='Value1').thenReturn(request2_response)
        when(self.mock_handler).request3(Key1='Value1', Key2='Value2').thenReturn(request3_response)

        # Act
        output_path = self.scanner.scan()
        account_data_dir = os.path.join(output_path, self.account_name)

        # Assert
        self.assertTrue(os.path.isfile(os.path.join(account_data_dir, 'describe-regions.json')))

        for region in self.regions:
            self.assertTrue(os.path.isfile(os.path.join(account_data_dir, region, 'service1-request1.json')))
            self.assertTrue(os.path.isfile(os.path.join(account_data_dir, region, 'service1-request2', 'Key1-Value1.json')))
            self.assertTrue(os.path.isfile(os.path.join(account_data_dir, region, 'service2-request3', 'Key1-Value1_Key2-Value2.json')))

        for region in self.regions:
            with open(os.path.join(account_data_dir, region, 'service1-request1.json'), 'r') as result_file:
                results = json.load(result_file)
                self.assertEqual(request1_response, results)

            with open(os.path.join(account_data_dir, region, 'service1-request2', 'Key1-Value1.json'), 'r') as result_file:
                results = json.load(result_file)
                self.assertEqual(request2_response, results)

            with open(os.path.join(account_data_dir, region, 'service2-request3', 'Key1-Value1_Key2-Value2.json'), 'r') as result_file:
                results = json.load(result_file)
                self.assertEqual(request3_response, results)

    def test_scan_file_created_on_available_regions(self):
        # Arrange
        request1_response = {'Items': []}

        when(self.mock_handler).request1().thenReturn(request1_response)
        when(self.session).get_available_regions("service1").thenReturn([self.regions[0]])

        # Act
        output_path = self.scanner.scan()
        account_data_dir = os.path.join(output_path, self.account_name)

        # Assert
        self.assertTrue(os.path.isfile(os.path.join(account_data_dir, self.regions[0], 'service1-request1.json')))
        self.assertFalse(os.path.isfile(os.path.join(account_data_dir, self.regions[1], 'service1-request1.json')))

    @patch('logging.Logger.warning')
    def test_scan_boto_raises_exception_on_command(self, patched_logger):
        # Arrange
        when(self.mock_handler).request1().thenRaise(ClientError({'Error': {'Code': 100, 'Message': 'Msg'}}, 'operation_name'))

        # Act
        self.scanner.scan()

        # Assert
        call_args = '\n'.join(str(arg) for arg in patched_logger.call_args)

        self.assertIn('serviceName.request1({}): An error occurred (100) when calling the operation_name operation: Msg', call_args)

    @patch('logging.Logger.warning')
    def test_scan_skips_previously_scanned_request(self, patched_logger):
        # Arrange
        when(self.mock_handler).request1().thenReturn({'Items': []})

        account_data_dir = init_directory(self.aws_settings.output_path, self.account_name, False)
        filepath_previously_scanned = os.path.join(account_data_dir, self.regions[0], 'service1-request1.json')
        filepath_new_scanned = os.path.join(account_data_dir, self.regions[1], 'service1-request1.json')

        make_directory(os.path.join(account_data_dir, self.regions[0]))
        with open(filepath_previously_scanned, 'w+') as file:
            file.write('{ "Items": [] }')

        # Act
        self.scanner.scan()

        # Assert
        call_args = '\n'.join(str(arg) for arg in patched_logger.call_args)

        self.assertIn(f'Response already present at {filepath_previously_scanned}', call_args)
        self.assertNotIn(f'Response already present at {filepath_new_scanned}', call_args)

    def test_scan_regions_filter(self):
        # Arrange
        self.aws_settings.regions_filter = self.regions[0]
        when(self.mock_handler).request1().thenReturn({'Items': []})

        output_path = self.scanner.scan()
        account_data_dir = os.path.join(output_path, self.account_name)

        # Assert
        self.assertTrue(os.path.isfile(os.path.join(account_data_dir, self.regions[0], 'service1-request1.json')))
        self.assertFalse(os.path.isfile(os.path.join(account_data_dir, self.regions[1], 'service1-request1.json')))

    @patch('dragoneye.cloud_scanner.aws.aws_scanner.time.sleep')
    @patch('logging.Logger.warning')
    def test_scan_command_check_fails(self, patched_logger, unused_patch_sleep):
        # Arrange
        self.aws_settings.regions_filter = self.regions[0]
        scan_command = [{
            'Service': 'service1',
            'Request': 'request1',
            'Check': [{
                'Name': 'FieldName',
                'Value': 'FieldValue'
            }]}]
        when(dragoneye.cloud_scanner.aws.aws_scanner).load_yaml(self.aws_settings.commands_path).thenReturn(scan_command)
        when(self.mock_handler).request1().thenReturn({'FieldName': 'UnmatchedFieldValue'})

        # Act
        self.scanner.scan()

        # Assert
        call_args = '\n'.join(str(arg) for arg in patched_logger.call_args)

        self.assertIn('serviceName.request1({}): One of the following checks has repeatedly failed: FieldName=FieldValue', call_args)

    @patch('logging.Logger.warning')
    def test_scan_command_check_passes(self, patched_logger):
        # Arrange
        self.aws_settings.regions_filter = self.regions[0]
        scan_command = [{
            'Service': 'service1',
            'Request': 'request1',
            'Check': [{
                'Name': 'FieldName',
                'Value': 'FieldValue'
            }]}]
        when(dragoneye.cloud_scanner.aws.aws_scanner).load_yaml(self.aws_settings.commands_path).thenReturn(scan_command)
        when(self.mock_handler).request1().thenReturn({'FieldName': 'FieldValue'})

        # Act
        self.scanner.scan()

        # Assert
        if patched_logger.called:
            call_args = '\n'.join(str(arg) for arg in patched_logger.call_args)
            self.assertNotIn('serviceName.request1({}): One of the following checks has repeatedly failed: FieldName=FieldValue', call_args)
