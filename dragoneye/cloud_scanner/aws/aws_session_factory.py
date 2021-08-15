from typing import Optional

import boto3
from botocore.exceptions import ClientError

from dragoneye.utils.app_logger import logger
from dragoneye.dragoneye_exception import DragoneyeException


class AwsSessionFactory:
    @staticmethod
    def get_session(profile_name: Optional[str] = None, region: Optional[str] = None):
        start_msg = 'Will try to create a session'
        session_data = {}
        if region:
            session_data["region_name"] = region
        if profile_name:
            session_data["profile_name"] = profile_name
            start_msg = f'{start_msg} using profile {profile_name}'
        else:
            start_msg = f'{start_msg} using AWS auth-chain'
        logger.info(f'{start_msg}...')
        try:
            session = boto3.Session(**session_data)
        except ClientError as ex:
            raise DragoneyeException(f'An exception happened while trying to create session: {str(ex)}', ex.response['Error']['Message'])
        except Exception as ex:
            raise DragoneyeException(f'An unknown exception happened while trying to create session: {str(ex)}', str(ex))
        AwsSessionFactory.test_connectivity(session)
        logger.info('Session was created successfully')
        return session

    @staticmethod
    def get_session_using_assume_role(role_arn: str, external_id: str, region: Optional[str] = None, session_duration: int = 3600):
        role_session_name = "DragoneyeSession"
        logger.info('Will try to assume role using ARN: {} and external id {}...'.format(role_arn, external_id))
        try:
            client = boto3.client('sts')
            response = client.assume_role(RoleArn=role_arn,
                                          RoleSessionName=role_session_name,
                                          DurationSeconds=session_duration,
                                          ExternalId=external_id)
            credentials = response['Credentials']
            session_data = {
                "aws_access_key_id": credentials['AccessKeyId'],
                "aws_secret_access_key": credentials['SecretAccessKey'],
                "aws_session_token": credentials['SessionToken']
            }
            if region:
                session_data['region_name'] = region
            session = boto3.Session(**session_data)
        except ClientError as ex:
            raise DragoneyeException(f'An exception happened while trying to assume role: {str(ex)}', ex.response['Error']['Message'])
        except Exception as ex:
            raise DragoneyeException(f'An unknown exception happened while trying to assume role: {str(ex)}', str(ex))
        AwsSessionFactory.test_connectivity(session)
        logger.info('Session was created successfully')
        return session

    @staticmethod
    def test_connectivity(session):
        sts = session.client("sts")
        try:
            sts.get_caller_identity()
        except ClientError as ex:
            if "InvalidClientTokenId" in str(ex):
                raise DragoneyeException('sts.get_caller_identity failed with InvalidClientTokenId. '
                                         'Likely cause is no AWS credentials are set', str(ex))
            raise DragoneyeException('Unknown exception when trying to call sts.get_caller_identity: {}'.format(ex), str(ex))
