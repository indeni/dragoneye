import os
import unittest

from mockito import unstub, when, mock

import dragoneye
from dragoneye.cloud_scanner.gcp.gcp_credentials_factory import GcpCredentialsFactory
from dragoneye.dragoneye_exception import DragoneyeException


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
            .from_service_account_info(info).thenReturn(credentials_mock)

        # Act
        credentials = GcpCredentialsFactory.from_service_account_info(info)
        # Assert
        self.assertEqual(credentials, credentials_mock)

    def test_from_service_info_fail(self):
        # Arrange
        info = {'google_key': 'google_value'}

        credentials_mock = mock()
        when(GcpCredentialsFactory).test_connectivity(credentials_mock).thenRaise(DragoneyeException('My Dragoneye Exception'))
        when(dragoneye.cloud_scanner.gcp.gcp_credentials_factory.service_account.Credentials)\
            .from_service_account_info(info).thenReturn(credentials_mock)

        # Act / Assert
        with self.assertRaisesRegex(DragoneyeException, 'My Dragoneye Exception'):
            GcpCredentialsFactory.from_service_account_info(info)

    def test_from_service_file_ok(self):
        # Arrange
        service_account_path = self._get_service_account_path()

        credentials_mock = mock()
        when(GcpCredentialsFactory).test_connectivity(credentials_mock).thenReturn(None)
        when(dragoneye.cloud_scanner.gcp.gcp_credentials_factory.service_account.Credentials)\
            .from_service_account_file(service_account_path).thenReturn(credentials_mock)

        # Act
        credentials = GcpCredentialsFactory.from_service_account_file(service_account_path)
        # Assert
        self.assertEqual(credentials, credentials_mock)

    def test_from_service_file_fail(self):
        # Arrange
        service_account_path = self._get_service_account_path()

        credentials_mock = mock()
        when(GcpCredentialsFactory).test_connectivity(credentials_mock).thenRaise(DragoneyeException('My Dragoneye Exception'))
        when(dragoneye.cloud_scanner.gcp.gcp_credentials_factory.service_account.Credentials)\
            .from_service_account_file(service_account_path).thenReturn(credentials_mock)

        # Act / Assert
        with self.assertRaisesRegex(DragoneyeException, 'My Dragoneye Exception'):
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
        when(GcpCredentialsFactory).test_connectivity(credentials_mock).thenRaise(DragoneyeException('My Dragoneye Exception'))
        when(dragoneye.cloud_scanner.gcp.gcp_credentials_factory.GoogleCredentials) \
            .get_application_default().thenReturn(credentials_mock)

        # Act / Assert
        with self.assertRaisesRegex(DragoneyeException, 'My Dragoneye Exception'):
            GcpCredentialsFactory.get_default_credentials()

    def test_impersonate_ok(self):
        # Arrange
        source_credentials_mock = mock()
        target_credentials_mock = mock()
        email = 'sa_test@google.com'

        when(GcpCredentialsFactory).test_connectivity(target_credentials_mock).thenReturn(None)
        when(dragoneye.cloud_scanner.gcp.gcp_credentials_factory.impersonated_credentials) \
            .Credentials(source_credentials=source_credentials_mock, target_principal=email, target_scopes=[]).thenReturn(target_credentials_mock)

        # Act
        credentials = GcpCredentialsFactory.impersonate(source_credentials_mock, email, [])
        # Assert
        self.assertEqual(credentials, target_credentials_mock)

    def test_impersonate_fail(self):
        # Arrange
        source_credentials_mock = mock()
        target_credentials_mock = mock()
        email = 'sa_test@google.com'

        when(GcpCredentialsFactory).test_connectivity(target_credentials_mock).thenRaise(DragoneyeException('My Dragoneye Exception'))
        when(dragoneye.cloud_scanner.gcp.gcp_credentials_factory.impersonated_credentials) \
            .Credentials(source_credentials=source_credentials_mock, target_principal=email, target_scopes=[]).thenReturn(target_credentials_mock)

        # Act / Assert
        with self.assertRaisesRegex(DragoneyeException, 'My Dragoneye Exception'):
            GcpCredentialsFactory.impersonate(source_credentials_mock, email, [])

    def test_aws_credentials_config_file_ok(self):
        # Arrange
        credentials_mock = mock()
        config_path = 'filepath.json'

        when(GcpCredentialsFactory).test_connectivity(credentials_mock).thenReturn(None)
        when(dragoneye.cloud_scanner.gcp.gcp_credentials_factory.aws.Credentials) \
            .from_file(config_path).thenReturn(credentials_mock)

        # Act
        credentials = GcpCredentialsFactory.from_aws_credentials_config_file(config_path)
        # Assert
        self.assertEqual(credentials, credentials_mock)

    def test_aws_credentials_config_file_fail(self):
        # Arrange
        credentials_mock = mock()
        config_path = 'filepath.json'

        when(GcpCredentialsFactory).test_connectivity(credentials_mock).thenRaise(DragoneyeException('My Dragoneye Exception'))
        when(dragoneye.cloud_scanner.gcp.gcp_credentials_factory.aws.Credentials) \
            .from_file(config_path).thenReturn(credentials_mock)

        # Act / Assert
        with self.assertRaisesRegex(DragoneyeException, 'My Dragoneye Exception'):
            GcpCredentialsFactory.from_aws_credentials_config_file(config_path)

    def test_aws_credentials_config_info_ok(self):
        # Arrange
        credentials_mock = mock()
        config_info = {'google_key': 'google_value'}

        when(GcpCredentialsFactory).test_connectivity(credentials_mock).thenReturn(None)
        when(dragoneye.cloud_scanner.gcp.gcp_credentials_factory.aws.Credentials) \
            .from_info(config_info).thenReturn(credentials_mock)

        # Act
        credentials = GcpCredentialsFactory.from_aws_credentials_config_info(config_info)
        # Assert
        self.assertEqual(credentials, credentials_mock)

    def test_aws_credentials_config_info_fail(self):
        # Arrange
        credentials_mock = mock()
        config_info = {'google_key': 'google_value'}

        when(GcpCredentialsFactory).test_connectivity(credentials_mock).thenRaise(DragoneyeException('My Dragoneye Exception'))
        when(dragoneye.cloud_scanner.gcp.gcp_credentials_factory.aws.Credentials) \
            .from_info(config_info).thenReturn(credentials_mock)

        # Act / Assert
        with self.assertRaisesRegex(DragoneyeException, 'My Dragoneye Exception'):
            GcpCredentialsFactory.from_aws_credentials_config_info(config_info)
