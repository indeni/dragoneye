import os

from dragoneye.cloud_scanner.base_cloud_scanner import CloudScanSettings, CloudProvider


class GcpCloudScanSettings(CloudScanSettings):
    def __init__(self,
                 commands_path: str,
                 account_name: str,
                 project_id: str,
                 output_path: str = os.getcwd(),
                 should_clean_before_scan: bool = True):
        """
        The settings that the AwsScanner uses for aws scanning.

            :param commands_path: The path of a YAML file that describes the scan commands to be used.
            :param account_name: A name for the scan results.
            :param project_id: The project ID of the project to scan.
            :param output_path: The directory where results will be saved. Defaults to current working directory.
            :param should_clean_before_scan: A flag that determines if prior results of this specific account (identified by account_name)
                should be deleted before scanning.
        """
        super().__init__(CloudProvider.GCP, account_name, should_clean_before_scan, output_path, commands_path)
        self.project_id: str = project_id
