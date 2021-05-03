import json

import requests

from dragoneye.utils.app_logger import logger
from dragoneye.dragoneye_exception import DragoneyeException


class AzureAuthorizer:
    @staticmethod
    def get_authorization_token(tenant_id: str, client_id: str, client_secret: str) -> str:
        logger.info('Will try to generate JWT bearer token...')
        response = requests.post(
            url=f'https://login.microsoftonline.com/{tenant_id}/oauth2/token',
            data={
                'grant_type': 'client_credentials',
                'client_id': client_id,
                'client_secret': client_secret,
                'resource': 'https://management.azure.com/'
            }
        )

        if response.status_code != 200:
            raise DragoneyeException(f'Failed to authenticate. status code: {response.status_code}\n'
                                     f'Reason: {response.text}')

        response_body = json.loads(response.text)
        access_token = response_body['access_token']
        logger.info('JWT bearer token generated successfully')
        return f'Bearer {access_token}'
