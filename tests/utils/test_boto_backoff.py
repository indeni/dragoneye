import unittest
from unittest.mock import MagicMock, patch

from botocore.exceptions import ClientError

from dragoneye.utils.boto_backoff import rate_limiter


class TestBotoBackoff(unittest.TestCase):
    def test_rate_limiter_not_throttled(self):
        # Arrange
        @rate_limiter()
        def func(a, b):
            return a + b

        # Act
        result = func(1, 2)

        # Assert
        self.assertEqual(result, 3)

    @patch('dragoneye.utils.boto_backoff.time.sleep')
    def test_rate_limiter_error_code_throttling(self, unused_patched_sleep):
        # Arrange
        max_attempts = 3

        func_mock = MagicMock(side_effect=ClientError(
            {'Error': {
                'Type': 'Sender',
                'Code': 'Throttling',
                'Message': 'Unknown'}
             }, 'operationName'))

        # Act / Assert
        with self.assertRaises(ClientError):
            rate_limiter(max_attempts)(func_mock)()

        self.assertEqual(func_mock.call_count, max_attempts)

    @patch('dragoneye.utils.boto_backoff.time.sleep')
    def test_rate_limiter_error_code_too_many_requests(self, unused_patched_sleep):
        # Arrange
        max_attempts = 3

        func_mock = MagicMock(side_effect=ClientError(
            {'Error': {
                'Type': 'Sender',
                'Code': 'TooManyRequestsException',
                'Message': 'Unknown'}
             }, 'operationName'))

        # Act / Assert
        with self.assertRaises(ClientError):
            rate_limiter(max_attempts)(func_mock)()

        self.assertEqual(func_mock.call_count, max_attempts)

    @patch('dragoneye.utils.boto_backoff.time.sleep')
    def test_rate_limiter_error_message_rate_exceeded(self, unused_patched_sleep):
        # Arrange
        max_attempts = 3

        func_mock = MagicMock(side_effect=ClientError(
            {'Error': {
                'Type': 'Sender',
                'Code': 'Unknown',
                'Message': 'Rate exceeded'}
             }, 'operationName'))

        # Act / Assert
        with self.assertRaises(ClientError):
            rate_limiter(max_attempts)(func_mock)()

        self.assertEqual(func_mock.call_count, max_attempts)