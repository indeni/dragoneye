import json
import os
from abc import abstractmethod
from enum import Enum
from queue import Queue
from dragoneye.utils.app_logger import logger

class CloudProvider(str, Enum):
    AWS = 'aws'
    AZURE = 'azure'
    GCP = 'gcp'


class CloudScanSettings:
    def __init__(self,
                 cloud_provider: CloudProvider,
                 account_name: str,
                 should_clean_before_scan: bool,
                 output_path: str,
                 commands_path: str):
        self.cloud_provider: CloudProvider = cloud_provider
        self.account_name: str = account_name
        self.clean: bool = should_clean_before_scan
        self.output_path: str = output_path
        self.commands_path: str = commands_path


class BaseCloudScanner:
    def __init__(self):
        self.account_data_dir: str = None
        self.summary: Queue = Queue()

    @abstractmethod
    def scan(self) -> str:
        pass

    @staticmethod
    def _write_failures_report(directory, failures):
        with open(os.path.join(directory, 'failures-report.json'), 'w+') as failures_report:
            failures_report.write(json.dumps(failures, default=str))

    def _print_summary(self):
        logger.info("--------------------------------------------------------------------")
        failures = []
        for call_summary in self.summary.queue:
            if 'error' in call_summary or 'exception' in call_summary:
                failures.append(call_summary)

        logger.info("Summary: {} APIs called. {} errors".format(len(self.summary.queue), len(failures)))
        if len(failures) > 0:
            logger.warning("Failures:")
            for call_summary in failures:
                logger.warning(f"  {self._parse_error(call_summary)}")

        self._write_failures_report(os.path.join(self.account_data_dir, '..'), failures)

    @staticmethod
    @abstractmethod
    def _parse_error(call_summary: dict) -> str:
        pass
