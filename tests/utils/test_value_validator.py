import os
import unittest
import uuid

from dragoneye.utils.value_validator import validate_uuid, validate_path


class TestValueValidator(unittest.TestCase):

    def test_validate_uuid_valid_value(self):
        # Arrange
        uuid1 = str(uuid.uuid1())
        uuid3 = str(uuid.uuid3(uuid.NAMESPACE_DNS, 'dragoneye'))
        uuid4 = str(uuid.uuid4())
        uuid5 = str(uuid.uuid5(uuid.NAMESPACE_DNS, 'dragoneye'))
        # Act / Assert
        validate_uuid(uuid1)
        validate_uuid(uuid3)
        validate_uuid(uuid4)
        validate_uuid(uuid5)

    def test_validate_uuid_invalid_value(self):
        # Arrange
        # First part doesnt contain 8 characters
        invalid_uuid1_1 = '1234567-1234-1234-1234-123456789012'
        invalid_uuid1_2 = '123456789-1234-1234-1234-123456789012'
        # Second part doesnt contain 4 characters
        invalid_uuid2_1 = '12345678-123-1234-1234-123456789012'
        invalid_uuid2_2 = '12345678-12345-1234-1234-123456789012'
        # Third part doesnt contain 4 characters
        invalid_uuid3_1 = '12345678-1234-123-1234-123456789012'
        invalid_uuid3_2 = '12345678-1234-12345-1234-123456789012'
        # Fourth part doesnt contain 4 characters
        invalid_uuid4_1 = '12345678-1234-1234-123-123456789012'
        invalid_uuid4_2 = '12345678-1234-1234-12345-123456789012'
        # Last part doesnt contain 12 characters
        invalid_uuid5_1 = '12345678-1234-123-1234-12345678901'
        invalid_uuid5_2 = '12345678-1234-123-1234-1234567890123'
        for invalid_uuid in (invalid_uuid1_1, invalid_uuid1_2,
                             invalid_uuid2_1, invalid_uuid2_2,
                             invalid_uuid3_1, invalid_uuid3_2,
                             invalid_uuid4_1, invalid_uuid4_2,
                             invalid_uuid5_1, invalid_uuid5_2):
            with self.assertRaises(ValueError):
                validate_uuid(invalid_uuid)

    def test_validate_path_valid_path(self):
        # Arrange
        filepath = os.path.abspath(__file__)
        dirpath = os.path.dirname(filepath)
        # Act / Assert
        validate_path(filepath)
        validate_path(dirpath)

    def test_validate_path_invalid_path(self):
        path1 = 'a-non-existent-directory'
        path2 = 'a-non-existent-file.json'
        path3 = '/a/non/existent/directory'
        path4 = '/a/non/existent/file.json'
        path5 = 'C:/non/existent/directory'
        path6 = 'C:/non/existent/file.json'
        for path in (path1, path2, path3, path4, path5, path6):
            with self.assertRaises(ValueError):
                validate_path(path)
