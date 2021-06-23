import os
import unittest

from mockito import unstub, when, mock

import dragoneye
from dragoneye.cloud_scanner.gcp.gcp_credentials_factory import GcpCredentialsFactory


class TestGcpCredentialsFactory(unittest.TestCase):
    def tearDown(self) -> None:
        unstub()

    @staticmethod
    def _get_service_account_path():
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources', 'service_account_file.json')

    def test_from_service_info_ok(self):
        # Arrange
        info = {'google_key': 'google_value'}

        credentials_mock = mock()
        when(GcpCredentialsFactory).test_connectivity(credentials_mock).thenReturn(None)
        when(dragoneye.cloud_scanner.gcp.gcp_credentials_factory.service_account.Credentials)\
            .from_service_account_info(info, scopes=GcpCredentialsFactory._SCOPES).thenReturn(credentials_mock)

        # Act
        credentials = GcpCredentialsFactory.from_service_account_info(info)
        # Assert
        self.assertEqual(credentials, credentials_mock)

    def test_from_service_info_fail(self):
        # Arrange
        info = {'google_key': 'google_value'}

        credentials_mock = mock()
        when(GcpCredentialsFactory).test_connectivity(credentials_mock).thenRaise(Exception('My Exception'))
        when(dragoneye.cloud_scanner.gcp.gcp_credentials_factory.service_account.Credentials)\
            .from_service_account_info(info, scopes=GcpCredentialsFactory._SCOPES).thenReturn(credentials_mock)

        # Act / Assert
        with self.assertRaisesRegex(Exception, 'My Exception'):
            GcpCredentialsFactory.from_service_account_info(info)

    def test_from_service_file_ok(self):
        # Arrange
        service_account_path = self._get_service_account_path()

        credentials_mock = mock()
        when(GcpCredentialsFactory).test_connectivity(credentials_mock).thenReturn(None)
        when(dragoneye.cloud_scanner.gcp.gcp_credentials_factory.service_account.Credentials)\
            .from_service_account_file(service_account_path, scopes=GcpCredentialsFactory._SCOPES).thenReturn(credentials_mock)

        # Act
        credentials = GcpCredentialsFactory.from_service_account_file(service_account_path)
        # Assert
        self.assertEqual(credentials, credentials_mock)

    def test_from_service_file_fail(self):
        # Arrange
        service_account_path = self._get_service_account_path()

        credentials_mock = mock()
        when(GcpCredentialsFactory).test_connectivity(credentials_mock).thenRaise(Exception('My Exception'))
        when(dragoneye.cloud_scanner.gcp.gcp_credentials_factory.service_account.Credentials)\
            .from_service_account_file(service_account_path, scopes=GcpCredentialsFactory._SCOPES).thenReturn(credentials_mock)

        # Act / Assert
        with self.assertRaisesRegex(Exception, 'My Exception'):
            GcpCredentialsFactory.from_service_account_file(service_account_path)

    def test_get_default_credentials_ok(self):
        # Arrange
        credentials_mock = mock()
        when(GcpCredentialsFactory).test_connectivity(credentials_mock).thenReturn(None)
        when(dragoneye.cloud_scanner.gcp.gcp_credentials_factory.GoogleCredentials)\
            .get_application_default().thenReturn(credentials_mock)

        # Act
        credentials = GcpCredentialsFactory.get_default_credentials()
        # Assert
        self.assertEqual(credentials, credentials_mock)

    def test_get_default_credentials_fail(self):
        # Arrange
        credentials_mock = mock()
        when(GcpCredentialsFactory).test_connectivity(credentials_mock).thenRaise(Exception('My Exception'))
        when(dragoneye.cloud_scanner.gcp.gcp_credentials_factory.GoogleCredentials) \
            .get_application_default().thenReturn(credentials_mock)

        # Act / Assert
        with self.assertRaisesRegex(Exception, 'My Exception'):
            GcpCredentialsFactory.get_default_credentials()
