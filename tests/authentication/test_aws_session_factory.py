import unittest

from mockito import unstub, when, mock

import dragoneye
from dragoneye.cloud_scanner.aws.aws_session_factory import AwsSessionFactory


class TestAwsSessionFactory(unittest.TestCase):

    def tearDown(self) -> None:
        unstub()

    def test_get_session_ok(self):
        for args in [
            {'profile_name': None, 'region': None},
            {'profile_name': 'profile', 'region': None},
            {'profile_name': 'profile', 'region': 'us-east-1'},
            {'profile_name': None, 'region': 'us-east-1'}
        ]:
            # Arrange
            session_params = {}
            if args['region']:
                session_params["region_name"] = args['region']
            if args['profile_name']:
                session_params["profile_name"] = args['profile_name']

            session_mock = mock()
            when(AwsSessionFactory).test_connectivity(session_mock).thenReturn(None)
            when(dragoneye.cloud_scanner.aws.aws_session_factory.boto3).Session(**session_params).thenReturn(session_mock)

            # Act
            session = AwsSessionFactory.get_session(**args)

            # Assert
            self.assertEqual(session, session_mock)

    def test_get_session_connectivity_fails(self):
        # Arrange
        session_mock = mock()
        when(dragoneye.cloud_scanner.aws.aws_session_factory.boto3).Session().thenReturn(session_mock)
        when(AwsSessionFactory).test_connectivity(session_mock).thenRaise(Exception('My Exception'))

        # Act / Assert
        with self.assertRaisesRegex(Exception, 'My Exception'):
            AwsSessionFactory.get_session()

    def test_get_session_using_assume_role_ok(self):
        for region_arg in ['us-east-1', None]:
            # Arrange
            role_arn = 'role_arn'
            duration_seconds = 10
            external_id = 'external_id'

            session_mock = mock()
            sts_mock = mock()

            response = {
                'Credentials': {
                    'AccessKeyId': 'access_key_id',
                    'SecretAccessKey': 'secret_access_key',
                    'SessionToken': 'session_token'
                }
            }

            credentials = response['Credentials']
            session_params = {
                "aws_access_key_id": credentials['AccessKeyId'],
                "aws_secret_access_key": credentials['SecretAccessKey'],
                "aws_session_token": credentials['SessionToken']
            }
            if region_arg:
                session_params['region_name'] = region_arg

            when(AwsSessionFactory).test_connectivity(session_mock).thenReturn(None)
            when(dragoneye.cloud_scanner.aws.aws_session_factory.boto3).client('sts').thenReturn(sts_mock)
            when(sts_mock).assume_role(RoleArn=role_arn, RoleSessionName='DragoneyeSession', DurationSeconds=duration_seconds, ExternalId=external_id)\
                .thenReturn(response)
            when(dragoneye.cloud_scanner.aws.aws_session_factory.boto3).Session(**session_params).thenReturn(session_mock)

            # Act
            session = AwsSessionFactory.get_session_using_assume_role(role_arn, external_id, region_arg, duration_seconds)

            # Assert
            self.assertEqual(session, session_mock)

    def test_get_session_using_assume_role_connectivity_fails(self):
        for region_arg in ['us-east-1', None]:
            # Arrange
            role_arn = 'role_arn'
            duration_seconds = 10
            external_id = 'external_id'

            session_mock = mock()
            sts_mock = mock()

            response = {
                'Credentials': {
                    'AccessKeyId': 'access_key_id',
                    'SecretAccessKey': 'secret_access_key',
                    'SessionToken': 'session_token'
                }
            }

            credentials = response['Credentials']
            session_params = {
                "aws_access_key_id": credentials['AccessKeyId'],
                "aws_secret_access_key": credentials['SecretAccessKey'],
                "aws_session_token": credentials['SessionToken']
            }
            if region_arg:
                session_params['region_name'] = region_arg

            when(AwsSessionFactory).test_connectivity(session_mock).thenRaise(Exception('My Exception'))
            when(dragoneye.cloud_scanner.aws.aws_session_factory.boto3).client('sts').thenReturn(sts_mock)
            when(sts_mock).assume_role(RoleArn=role_arn, RoleSessionName='DragoneyeSession', DurationSeconds=duration_seconds, ExternalId=external_id)\
                .thenReturn(response)
            when(dragoneye.cloud_scanner.aws.aws_session_factory.boto3).Session(**session_params).thenReturn(session_mock)

            # Act / Assert
            with self.assertRaisesRegex(Exception, 'My Exception'):
                AwsSessionFactory.get_session_using_assume_role(role_arn, external_id, region_arg, duration_seconds)
