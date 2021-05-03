import os
import unittest
from datetime import datetime
from unittest.mock import patch

from dragoneye.utils.misc_utils import snakecase, elapsed_time, get_dynamic_values_from_files, custom_serializer


class TestMisUtils(unittest.TestCase):
    resource_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources')
    
    def test_snakecase(self):
        # Arrange
        text = 'a-String-WITH-DasH'

        # Act
        snakecase_text = snakecase(text)

        # Assert
        self.assertEqual(snakecase_text, 'a_String_WITH_DasH')

    def test_elapsed_time(self):
        # Arrange
        elapsed_time_msg = 'This test function took {} seconds'

        @elapsed_time(elapsed_time_msg)
        def my_func(x):
            return x + 1

        with patch('logging.Logger.info') as log_info_mock:
            # Act
            func_res = my_func(5)
            # Assert
            call_args = '\n'.join(str(arg) for arg in log_info_mock.call_args)
            self.assertRegex(call_args, elapsed_time_msg.format('\\w+.*\\b'))
            self.assertEqual(func_res, 6)

    def test_get_dynamic_values_from_files_ok(self):
        # Arrange / Act
        names = get_dynamic_values_from_files('data.json|.value[].name', self.resource_path)
        multival = get_dynamic_values_from_files('data.json|.value[].multival[]', self.resource_path)
        # Assert
        self.assertListEqual(names, ['first item', 'second item'])
        self.assertListEqual(multival, [1, 2, 3, 11, 22, 33])

    def test_get_dynamic_values_from_files_non_existing_directory(self):
        names = get_dynamic_values_from_files('data.json|.value[].name', './nodir')
        self.assertListEqual(names, [])

    def test_get_dynamic_values_from_files_non_existing_file(self):
        names = get_dynamic_values_from_files('nofile.json|.value[].name', self.resource_path)
        self.assertListEqual(names, [])

    def test_custom_serializer_datetime(self):
        # Arrange
        date = datetime(2000, 10, 5, 1, 2, 3, 4)
        # Act
        result = custom_serializer(date)
        # Assert
        self.assertEqual(result, '2000-10-05T01:02:03.000004')

    def test_custom_serializer_bytes(self):
        # Arrange
        byte_data = b'bytes'
        # Act
        result = custom_serializer(byte_data)
        # Assert
        self.assertEqual(result, 'bytes')

    def test_custom_serializer_unknown_type(self):
        # Arrange
        obj = 'some string'
        # Act / Assert
        with self.assertRaises(TypeError):
            custom_serializer(obj)
