import subprocess
import sys
import unittest
import uuid
from unittest.mock import ANY

import requests
from mockito import unstub, when, mock

from dragoneye.cloud_scanner.azure.azure_authorizer import AzureAuthorizer
from dragoneye.dragoneye_exception import DragoneyeException


class TestAzureAuthorizer(unittest.TestCase):

    def tearDown(self) -> None:
        unstub()

    def test_get_authorization_token_from_credentials_ok(self):
        # Arrange
        response_text = '{ "access_token": "the_token" }'
        when(requests).post(url=ANY, data=ANY).thenReturn(mock({'status_code': 200, 'text': response_text}))
        # Act
        token = AzureAuthorizer.get_authorization_token(str(uuid.uuid4()), str(uuid.uuid4()), 'client_secret')
        # Assert
        self.assertEqual(token, 'Bearer the_token')

    def test_get_authorization_token_from_credentials_error(self):
        # Arrange
        response_text = '{ "error": "the error message" }'
        when(requests).post(url=ANY, data=ANY).thenReturn(mock({'status_code': 401, 'text': response_text}))
        # Act / Assert
        with self.assertRaisesRegex(DragoneyeException, f'Failed to authenticate. status code: 401\nReason: {response_text}'):
            AzureAuthorizer.get_authorization_token(str(uuid.uuid4()), str(uuid.uuid4()), 'client_secret')

    def test_get_authorization_token_from_credentials_invalid_params(self):
        with self.assertRaisesRegex(ValueError, 'Invalid tenant id'):
            AzureAuthorizer.get_authorization_token(tenant_id='not_uuid', client_id=str(uuid.uuid4()), client_secret='secret')

        with self.assertRaisesRegex(ValueError, 'Invalid client id'):
            AzureAuthorizer.get_authorization_token(tenant_id=str(uuid.uuid4()), client_id='not_uuid', client_secret='secret')

    def test_get_authorization_token_from_cli_ok(self):
        # Arrange
        process_mock = mock()
        when(process_mock).__enter__().thenReturn(process_mock)
        when(process_mock).__exit__().thenReturn(process_mock)
        when(subprocess).Popen(ANY, stdout=ANY, stderr=ANY).thenReturn(process_mock)
        when(process_mock).communicate().thenReturn((b'{ "accessToken": "the_token" }', b''))
        # Act
        token = AzureAuthorizer.get_authorization_token()
        # Assert
        self.assertEqual('Bearer the_token', token)

    def test_get_authorization_token_from_cli_error(self):
        # Arrange
        error_message = b'An error occurred'
        process_mock = mock()
        when(process_mock).__enter__().thenReturn(process_mock)
        when(process_mock).__exit__().thenReturn(process_mock)
        when(subprocess).Popen(ANY, stdout=ANY, stderr=ANY).thenReturn(process_mock)
        when(process_mock).communicate().thenReturn((b'', error_message))
        # Act / Assert
        with self.assertRaisesRegex(DragoneyeException, f'Failed to authenticate.\nReason: {error_message.decode(sys.stderr.encoding)}'):
            AzureAuthorizer.get_authorization_token()
