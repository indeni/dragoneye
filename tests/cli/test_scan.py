import os
import shutil
import unittest
import uuid
from typing import List
from unittest.mock import patch

from click.testing import CliRunner
from mockito import when, unstub, mock

import dragoneye
from dragoneye import AzureAuthorizer, AwsSessionFactory, GcpCredentialsFactory
from dragoneye.scan import scan_cli


class TestScan(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.runner = CliRunner()

    @classmethod
    def tearDownClass(cls) -> None:
        try:
            shutil.rmtree('./account-data')
        except Exception:
            pass

    def tearDown(self) -> None:
        unstub()

    @patch.object(AzureAuthorizer, 'get_authorization_token')
    def test_azure_ok_all_options(self, mock_azure_authorizer):
        # Arrange
        mock_azure_authorizer.return_value = 'token'
        when(dragoneye.cloud_scanner.azure.azure_scanner.AzureScanner).scan().thenReturn('/path/to/results')
        # Act
        result = self.runner.invoke(scan_cli, ['azure',
                                               os.path.join(self._current_dir(), 'resources', 'azure_commands_example.yaml'),
                                               '--subscription-id', str(uuid.uuid4()),
                                               '--tenant-id', str(uuid.uuid4()),
                                               '--client-id', str(uuid.uuid4()),
                                               '--client-secret', str(uuid.uuid4())])
        # Assert
        self.assertEqual(result.exit_code, 0)
        self.assertTrue('/path/to/results' in result.output)

    @patch.object(AzureAuthorizer, 'get_authorization_token')
    def test_azure_ok_minimal_options(self, mock_azure_authorizer):
        # Arrange
        mock_azure_authorizer.return_value = 'token'
        when(dragoneye.cloud_scanner.azure.azure_scanner.AzureScanner).scan().thenReturn('/path/to/results')
        # Act
        result = self.runner.invoke(scan_cli, ['azure',
                                               os.path.join(self._current_dir(), 'resources', 'azure_commands_example.yaml'),
                                               '--subscription-id', str(uuid.uuid4())])
        # Assert
        self.assertEqual(result.exit_code, 0)
        self.assertTrue('/path/to/results' in result.output)

    def test_azure_invalid_subscription_id(self):
        # Act
        result = self.runner.invoke(scan_cli, ['azure',
                                               os.path.join(self._current_dir(), 'resources', 'azure_commands_example.yaml'),
                                               '--subscription-id', 'non-uuid-value',
                                               '--tenant-id', str(uuid.uuid4()),
                                               '--client-id', str(uuid.uuid4()),
                                               '--client-secret', str(uuid.uuid4())])
        # Assert
        self.assertEqual(result.exit_code, 1)
        self._assert_exception(result.exception, ValueError, 'Invalid subscription id')

    def test_azure_invalid_tenant_id(self):
        # Act
        result = self.runner.invoke(scan_cli, ['azure',
                                               os.path.join(self._current_dir(), 'resources', 'azure_commands_example.yaml'),
                                               '--subscription-id', str(uuid.uuid4()),
                                               '--tenant-id', 'non-uuid-value',
                                               '--client-id', str(uuid.uuid4()),
                                               '--client-secret', str(uuid.uuid4())])
        # Assert
        self.assertEqual(result.exit_code, 1)
        self._assert_exception(result.exception, ValueError, 'Invalid tenant id')

    def test_azure_invalid_client_id(self):
        # Act
        result = self.runner.invoke(scan_cli, ['azure',
                                               os.path.join(self._current_dir(), 'resources', 'azure_commands_example.yaml'),
                                               '--subscription-id', str(uuid.uuid4()),
                                               '--tenant-id', str(uuid.uuid4()),
                                               '--client-id', 'non-uuid-value',
                                               '--client-secret', str(uuid.uuid4())])
        # Assert
        self.assertEqual(result.exit_code, 1)
        self._assert_exception(result.exception, ValueError, 'Invalid client id')

    def test_azure_invalid_scan_commands_path(self):
        # Act
        result = self.runner.invoke(scan_cli, ['azure',
                                               os.path.join(self._current_dir(), 'non-existing-file.yaml'),
                                               '--subscription-id', str(uuid.uuid4()),
                                               '--tenant-id', str(uuid.uuid4()),
                                               '--client-id', str(uuid.uuid4()),
                                               '--client-secret', str(uuid.uuid4())])
        # Assert
        self.assertEqual(result.exit_code, 1)
        self._assert_invalid_scan_commands_path_exception(result.exception, ['Could not find file: ', 'non-existing-file.yaml'])

    @patch.object(AwsSessionFactory, 'get_session')
    def test_aws_no_profile_ok(self, mock_aws_session_factory):
        # Arrange
        mock_aws_session_factory.return_value = mock({'region_name': 'us-east-1'})
        when(dragoneye.cloud_scanner.aws.aws_scanner.AwsScanner).scan().thenReturn('/path/to/results')
        # Act
        result = self.runner.invoke(scan_cli, ['aws', os.path.join(self._current_dir(), 'resources', 'aws_commands_example.yaml')])
        # Assert
        self.assertEqual(result.exit_code, 0)
        self.assertTrue('/path/to/results' in result.output)

    @patch.object(AwsSessionFactory, 'get_session')
    def test_aws_with_profile_ok(self, mock_aws_session_factory):
        # Arrange
        mock_aws_session_factory.return_value = mock({'region_name': 'us-east-1'})
        when(dragoneye.cloud_scanner.aws.aws_scanner.AwsScanner).scan().thenReturn('/path/to/results')
        # Act
        result = self.runner.invoke(scan_cli, ['aws', os.path.join(self._current_dir(), 'resources', 'aws_commands_example.yaml'),
                                               '--profile', 'profile-name'])
        # Assert
        self.assertEqual(result.exit_code, 0)
        self.assertTrue('/path/to/results' in result.output)

    def test_aws_invalid_scan_commands_path(self):
        # Act
        result = self.runner.invoke(scan_cli, ['aws', os.path.join(self._current_dir(), 'non-existing-file.yaml')])
        # Assert
        self.assertEqual(result.exit_code, 1)
        self._assert_invalid_scan_commands_path_exception(result.exception, ['Could not find file: ', 'non-existing-file.yaml'])

    @patch.object(GcpCredentialsFactory, 'from_service_account_file')
    def test_gcp_ok_with_credentials(self, mock_azure_authorizer):
        # Arrange
        mock_azure_authorizer.return_value = mock()
        when(dragoneye.cloud_scanner.gcp.gcp_scanner.GcpScanner).scan().thenReturn('/path/to/results')
        # Act
        result = self.runner.invoke(scan_cli, ['gcp',
                                               os.path.join(self._current_dir(), 'resources', 'gcp_commands_example.yaml'),
                                               '--credentials-path',
                                               os.path.join(self._current_dir(), 'resources', 'service_account_credentials.json')])
        # Assert
        self.assertEqual(result.exit_code, 0)
        self.assertTrue('/path/to/results' in result.output)

    @patch.object(GcpCredentialsFactory, 'get_default_credentials')
    def test_gcp_ok_without_credentials(self, mock_azure_authorizer):
        # Arrange
        mock_azure_authorizer.return_value = mock()
        when(dragoneye.cloud_scanner.gcp.gcp_scanner.GcpScanner).scan().thenReturn('/path/to/results')
        # Act
        result = self.runner.invoke(scan_cli, ['gcp',
                                               os.path.join(self._current_dir(), 'resources', 'gcp_commands_example.yaml')])
        # Assert
        self.assertEqual(result.exit_code, 0)
        self.assertTrue('/path/to/results' in result.output)

    @patch.object(GcpCredentialsFactory, 'get_default_credentials')
    def test_gcp_invalid_scan_commands_path(self, mock_azure_authorizer):
        # Arrange
        mock_azure_authorizer.return_value = mock()
        when(dragoneye.cloud_scanner.gcp.gcp_scanner.GcpScanner).scan().thenReturn('/path/to/results')
        # Act
        result = self.runner.invoke(scan_cli, ['gcp',
                                               os.path.join(self._current_dir(), 'non-existing-file.yaml')])
        # Assert
        self.assertEqual(result.exit_code, 1)
        self._assert_invalid_scan_commands_path_exception(result.exception, ['Could not find file: ', 'non-existing-file.yaml'])

    def _assert_exception(self, exception, ex_type, ex_message):
        self.assertEqual(type(exception), ex_type)
        self.assertEqual(exception.args, ex_type(ex_message).args)

    def _assert_invalid_scan_commands_path_exception(self, exception, substrings: List[str]):
        self.assertEqual(type(exception), ValueError)
        for substring in substrings:
            self.assertTrue(any(substring in exception_arg for exception_arg in exception.args))

    @staticmethod
    def _current_dir():
        return os.path.dirname(os.path.abspath(__file__))
