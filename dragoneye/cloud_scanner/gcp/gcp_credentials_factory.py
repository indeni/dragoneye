from typing import Sequence

from google.auth.exceptions import RefreshError
from google.oauth2 import service_account
from google.auth import impersonated_credentials, aws
from googleapiclient.discovery import build
from oauth2client.client import GoogleCredentials

from dragoneye.dragoneye_exception import DragoneyeException
from dragoneye.utils.app_logger import logger


class GcpCredentialsFactory:
    @classmethod
    def from_service_account_info(cls, service_account_info: dict):
        logger.info('Will try to generate credentials from service account info...')
        credentials = service_account.Credentials.from_service_account_info(
            service_account_info)

        cls.test_connectivity(credentials)
        logger.info('Generated credentials successfully')
        return credentials

    @classmethod
    def get_default_credentials(cls):
        logger.info('Will try to generate the default credentials...')
        credentials = GoogleCredentials.get_application_default()

        cls.test_connectivity(credentials)
        logger.info('Generated credentials successfully')
        return credentials

    @classmethod
    def from_service_account_file(cls, service_account_file: str):
        logger.info('Will try to generate credentials from service account file...')
        credentials = service_account.Credentials.from_service_account_file(
            service_account_file)

        cls.test_connectivity(credentials)
        logger.info('Generated credentials successfully')
        return credentials

    @classmethod
    def impersonate(cls, credentials, email: str, scopes: Sequence[str]):
        """
        Creates and returns impersonated credentials.
        :param credentials: The credentials of the source service account
        :param email: The email address of the target service account
        :param scopes: The scopes of the created credentials
        :return: An impersonated credentials instance
        """
        logger.info(f'Will try to generate short-lived credentials for {email}...')
        credentials = impersonated_credentials.Credentials(source_credentials=credentials,
                                                           target_principal=email,
                                                           target_scopes=scopes)
        cls.test_connectivity(credentials)
        logger.info('Generated credentials successfully')
        return credentials

    @classmethod
    def from_aws_credentials_config_info(cls, info: dict):
        logger.info('Will try to generate short-lived credentials for an AWS workload identity user from credentials config info...')
        cred = aws.Credentials.from_info(info)
        cls.test_connectivity(cred)
        logger.info('Generated credentials successfully')
        return cred

    @classmethod
    def from_aws_credentials_config_file(cls, config_file_path: str):
        logger.info('Will try to generate short-lived credentials for an AWS workload identity user from credentials config file...')
        cred = aws.Credentials.from_file(config_file_path)
        cls.test_connectivity(cred)
        logger.info('Generated credentials successfully')
        return cred

    @staticmethod
    def test_connectivity(credentials):
        with build('compute', 'v1', credentials=credentials) as service:
            try:
                service.instances().get(project='abc', zone='us-east1-a', instance='abc').execute()
            except RefreshError as ex:
                raise DragoneyeException('Unable to invoke GCP API with given credentials', str(ex))
            except Exception:
                pass
