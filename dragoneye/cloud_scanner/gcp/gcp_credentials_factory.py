from google.auth.exceptions import RefreshError
from google.oauth2 import service_account
from googleapiclient.discovery import build
from oauth2client.client import GoogleCredentials

from dragoneye.dragoneye_exception import DragoneyeException
from dragoneye.utils.app_logger import logger


class GcpCredentialsFactory:
    _SCOPES = [
        # TODO: What other scopes are needed?
        'https://www.googleapis.com/auth/compute.readonly',
        'https://www.googleapis.com/auth/devstorage.read_only',
        'https://www.googleapis.com/auth/cloud-platform.read-only',
        'https://www.googleapis.com/auth/cloudplatformprojects.readonly'
    ]

    @classmethod
    def from_service_account_info(cls, service_account_info: dict):
        logger.info('Will try to generate credentials from service account info...')
        credentials = service_account.Credentials.from_service_account_info(
            service_account_info, scopes=cls._SCOPES)

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
            service_account_file, scopes=cls._SCOPES)

        cls.test_connectivity(credentials)
        logger.info('Generated credentials successfully')
        return credentials

    @staticmethod
    def test_connectivity(credentials):
        with build('compute', 'v1', credentials=credentials) as service:
            try:
                service.instances().get(project='abc', zone='us-east1-a', instance='abc').execute()
            except RefreshError as ex:
                raise DragoneyeException('Unable to invoke GCP API with given credentials', str(ex))
            except Exception:
                pass
