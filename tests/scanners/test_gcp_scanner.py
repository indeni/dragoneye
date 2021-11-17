import json
import os
import tempfile
import unittest

from googleapiclient.errors import HttpError
from mockito import when, unstub, mock

from dragoneye.cloud_scanner.gcp.gcp_scanner import GcpScanner, GcpCloudScanSettings


class TestGcpScanner(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.account_name = 'test-account'

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.gcp_settings = GcpCloudScanSettings(
            commands_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources', 'gcp_scan_commands.yaml'),
            account_name=self.account_name,
            should_clean_before_scan=False,
            output_path=self.temp_dir.name,
            project_id='projectid'
        )
        self.credentials = mock()
        self.scanner = GcpScanner(self.credentials, self.gcp_settings)

        self.service_mock = mock()
        when(self.scanner)._create_service('service', 'v1').thenReturn(self.service_mock)

        self.resource1_mock = mock()
        when(self.service_mock).resource1().thenReturn(self.resource1_mock)
        self.resource1_method_mock = mock()
        when(self.resource1_mock).list().thenReturn(self.resource1_method_mock)
        when(self.resource1_mock).list_next().thenReturn(None)
        self.res = {'value': [
            {
                'param1': 'p1val1',
                'param2': 'p2val1',
                'param3': 'p3val1'
            },
            {
                'param1': 'p1val2',
                'param2': 'p2val2',
                'param3': 'p3val2'
            },
            {
                'param1': 'p1val3',
                'param2': 'p2val3',
                'param3': 'p3val3'
            }
        ]}
        when(self.resource1_method_mock).execute().thenReturn(self.res)

        self.resource2_mock = mock()
        self.resource2_method_mock = mock()
        when(self.service_mock).resource2().thenReturn(self.resource2_mock)
        self.resource2_method_mock = mock()
        when(self.resource2_mock).get(param1='p1val1').thenReturn(self.resource2_method_mock)
        when(self.resource2_mock).get(param1='p1val2').thenReturn(self.resource2_method_mock)
        when(self.resource2_method_mock).execute().thenReturn({'id': '2'})

        self.resource3_mock = mock()
        self.resource3_method_mock = mock()
        when(self.service_mock).resource3().thenReturn(self.resource3_mock)
        self.resource3_method_mock = mock()
        when(self.resource3_mock).get(param1='p1val1', param2='p2val1').thenReturn(self.resource3_method_mock)
        when(self.resource3_mock).get(param1='p1val2', param2='p2val2').thenReturn(self.resource3_method_mock)
        when(self.resource3_method_mock).execute().thenReturn({'id': '3'})

        self.resource4_mock = mock()
        self.resource4_method_mock = mock()
        when(self.service_mock).resource4().thenReturn(self.resource4_mock)
        self.resource4_method_mock = mock()
        when(self.resource4_mock).get(param1='p1val1', param2='p2val1').thenReturn(self.resource4_method_mock)
        when(self.resource4_mock).get(param1='p1val2', param2='p2val2').thenReturn(self.resource4_method_mock)
        when(self.resource4_mock).get(param1='p1val1', param2='p2val2').thenReturn(self.resource4_method_mock)
        when(self.resource4_mock).get(param1='p1val2', param2='p2val1').thenReturn(self.resource4_method_mock)
        when(self.resource4_method_mock).execute().thenReturn({'id': '4'})

        self.resource5_mock = mock()
        self.resource5_method_mock = mock()
        when(self.service_mock).resource5().thenReturn(self.resource5_mock)
        self.resource5_method_mock = mock()
        when(self.resource5_mock).get(param1='p1val1', param2='p2val1', param3='p3val1').thenReturn(self.resource5_method_mock)
        when(self.resource5_mock).get(param1='p1val1', param2='p2val1', param3='p3val2').thenReturn(self.resource5_method_mock)
        when(self.resource5_mock).get(param1='p1val1', param2='p2val1', param3='p3val3').thenReturn(self.resource5_method_mock)
        when(self.resource5_mock).get(param1='p1val2', param2='p2val2', param3='p3val1').thenReturn(self.resource5_method_mock)
        when(self.resource5_mock).get(param1='p1val2', param2='p2val2', param3='p3val2').thenReturn(self.resource5_method_mock)
        when(self.resource5_mock).get(param1='p1val2', param2='p2val2', param3='p3val3').thenReturn(self.resource5_method_mock)
        when(self.resource5_method_mock).execute().thenReturn({'id': '5'})

    def tearDown(self) -> None:
        self.temp_dir.cleanup()
        unstub()

    def test_scan_ok(self):
        # Act
        output_path = self.scanner.scan()
        account_data_dir = os.path.join(output_path, self.account_name)

        # Assert
        self.assertTrue(os.path.isfile(os.path.join(account_data_dir, 'service-v1-resource1-list.json')))
        self.assertTrue(os.path.isfile(os.path.join(account_data_dir, 'service-v1-resource2-get.json')))
        self.assertTrue(os.path.isfile(os.path.join(account_data_dir, 'service-v1-resource3-get.json')))
        self.assertTrue(os.path.isfile(os.path.join(account_data_dir, 'service-v1-resource4-get.json')))
        self.assertTrue(os.path.isfile(os.path.join(account_data_dir, 'service-v1-resource5-get.json')))

        with open(os.path.join(account_data_dir, 'service-v1-resource1-list.json'), 'r') as result_file:
            results = json.load(result_file)
            value = results['value']
            self.assertEqual(len(value), 3)
            self.assertTrue(any(dic['param1'] == 'p1val1' for dic in value))
            self.assertTrue(any(dic['param2'] == 'p2val1' for dic in value))
            self.assertTrue(any(dic['param3'] == 'p3val1' for dic in value))
            self.assertTrue(any(dic['param1'] == 'p1val2' for dic in value))
            self.assertTrue(any(dic['param2'] == 'p2val2' for dic in value))
            self.assertTrue(any(dic['param3'] == 'p3val2' for dic in value))
            self.assertTrue(any(dic['param1'] == 'p1val3' for dic in value))
            self.assertTrue(any(dic['param2'] == 'p2val3' for dic in value))
            self.assertTrue(any(dic['param3'] == 'p3val3' for dic in value))

        with open(os.path.join(account_data_dir, 'service-v1-resource2-get.json'), 'r') as result_file:
            results = json.load(result_file)
            value = results['value']
            self.assertTrue(any(dic['id'] == '2' for dic in value))
            self.assertEqual(len(value), 2)

        with open(os.path.join(account_data_dir, 'service-v1-resource3-get.json'), 'r') as result_file:
            results = json.load(result_file)
            value = results['value']
            self.assertTrue(any(dic['id'] == '3' for dic in value))
            self.assertEqual(len(value), 2)

        with open(os.path.join(account_data_dir, 'service-v1-resource4-get.json'), 'r') as result_file:
            results = json.load(result_file)
            value = results['value']
            self.assertTrue(any(dic['id'] == '4' for dic in value))
            self.assertEqual(len(value), 4)

        with open(os.path.join(account_data_dir, 'service-v1-resource5-get.json'), 'r') as result_file:
            results = json.load(result_file)
            value = results['value']
            self.assertTrue(any(dic['id'] == '5' for dic in value))
            self.assertEqual(len(value), 6)

    def test_scan_ok_empty_values(self):
        # Arrange
        when(self.resource1_method_mock).execute().thenReturn({})

        # Act
        output_path = self.scanner.scan()
        account_data_dir = os.path.join(output_path, self.account_name)

        # Assert
        self.assertTrue(os.path.isfile(os.path.join(account_data_dir, 'service-v1-resource1-list.json')))
        self.assertTrue(os.path.isfile(os.path.join(account_data_dir, 'service-v1-resource2-get.json')))
        self.assertTrue(os.path.isfile(os.path.join(account_data_dir, 'service-v1-resource3-get.json')))
        self.assertTrue(os.path.isfile(os.path.join(account_data_dir, 'service-v1-resource4-get.json')))
        self.assertTrue(os.path.isfile(os.path.join(account_data_dir, 'service-v1-resource5-get.json')))

        with open(os.path.join(account_data_dir, 'service-v1-resource1-list.json'), 'r') as result_file:
            results = json.load(result_file)
            value = results['value']
            self.assertEqual(len(value), 0)

        with open(os.path.join(account_data_dir, 'service-v1-resource2-get.json'), 'r') as result_file:
            results = json.load(result_file)
            value = results['value']
            self.assertEqual(len(value), 0)

        with open(os.path.join(account_data_dir, 'service-v1-resource3-get.json'), 'r') as result_file:
            results = json.load(result_file)
            value = results['value']
            self.assertEqual(len(value), 0)

        with open(os.path.join(account_data_dir, 'service-v1-resource4-get.json'), 'r') as result_file:
            results = json.load(result_file)
            value = results['value']
            self.assertEqual(len(value), 0)

        with open(os.path.join(account_data_dir, 'service-v1-resource5-get.json'), 'r') as result_file:
            results = json.load(result_file)
            value = results['value']
            self.assertEqual(len(value), 0)

    def test_scan_failed_request(self):
        # Arrrange
        error_resp_mock = mock({'status_code': 404, 'reason': b'some reason'})
        when(self.resource2_method_mock).execute().thenRaise(HttpError(error_resp_mock, b'{"error": {"code": 404, "message": "some message"}}'))
        when(self.resource3_method_mock).execute().thenRaise(Exception('some message'))

        # Act
        output_path = self.scanner.scan()
        account_data_dir = os.path.join(output_path, self.account_name)

        # Assert
        self.assertTrue(os.path.isfile(os.path.join(account_data_dir, 'service-v1-resource1-list.json')))
        self.assertTrue(os.path.isfile(os.path.join(account_data_dir, 'service-v1-resource2-get.json')))
        self.assertTrue(os.path.isfile(os.path.join(account_data_dir, 'service-v1-resource3-get.json')))
        self.assertTrue(os.path.isfile(os.path.join(account_data_dir, 'service-v1-resource4-get.json')))
        self.assertTrue(os.path.isfile(os.path.join(account_data_dir, 'service-v1-resource5-get.json')))

        with open(os.path.join(account_data_dir, 'service-v1-resource1-list.json'), 'r') as result_file:
            results = json.load(result_file)
            value = results['value']
            self.assertEqual(len(value), 3)

        with open(os.path.join(account_data_dir, 'service-v1-resource2-get.json'), 'r') as result_file:
            results = json.load(result_file)
            value = results['value']
            self.assertEqual(len(value), 0)

        with open(os.path.join(account_data_dir, 'service-v1-resource3-get.json'), 'r') as result_file:
            results = json.load(result_file)
            value = results['value']
            self.assertEqual(len(value), 0)

        with open(os.path.join(account_data_dir, 'service-v1-resource4-get.json'), 'r') as result_file:
            results = json.load(result_file)
            value = results['value']
            self.assertTrue(any(dic['id'] == '4' for dic in value))
            self.assertEqual(len(value), 4)

        with open(os.path.join(account_data_dir, 'service-v1-resource5-get.json'), 'r') as result_file:
            results = json.load(result_file)
            value = results['value']
            self.assertTrue(any(dic['id'] == '5' for dic in value))
            self.assertEqual(len(value), 6)

    def test_scan_failure_is_in_report_file(self):
        # Arrange
        when(self.resource3_method_mock).execute().thenRaise(Exception('some message'))

        # Act
        output_path = self.scanner.scan()

        with open(os.path.join(output_path, 'failures-report.json')) as failures_file:
            failures = json.loads(failures_file.read())
            self.assertEqual(len(failures), 2)
            failure_summary = {'service': 'service',
                               'api_version': 'v1',
                               'resource_type': ['resource3'],
                               'method': 'get',
                               'exception': 'some message',
                               'parameters': {'param1': 'p1val1', 'param2': 'p2val1'}}
            self.assertEqual(failures[0], failure_summary)
            failure_summary['parameters'] = {'param1': 'p1val2', 'param2': 'p2val2'}
            self.assertEqual(failures[1], failure_summary)
