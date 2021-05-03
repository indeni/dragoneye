import os
from typing import List, Optional

from dragoneye.cloud_scanner.base_cloud_scanner import CloudScanSettings, CloudProvider


class AwsCloudScanSettings(CloudScanSettings):
    def __init__(self,
                 commands_path: str,
                 account_name: str,
                 regions_filter: List[str] = None,
                 max_attempts: int = 10,
                 max_pool_connections: int = 50,
                 command_timeout: int = 600,
                 output_path: str = os.getcwd(),
                 should_clean_before_scan: bool = True,
                 default_region: Optional[str] = None):
        """
        The settings that the AwsScanner uses for aws scanning.

            :param commands_path: The path of a YAML file that describes the scan commands to be used.
            :param account_name: A name for the scan results.
            :param regions_filter: A list of regions to scan resources on.
            :param max_attempts: The amount of times that the boto client will attempt to call AWS's api before giving up.
            :param max_pool_connections: The maximum number of connections to keep in a connection pool.
            :param command_timeout: The timeout period for a single scan command.
            :param output_path: The directory where results will be saved. Defaults to current working directory.
            :param should_clean_before_scan: A flag that determines if prior results of this specific account (identified by account_name)
                should be deleted before scanning.
            :param default_region: The region to be used for making requests for universal services.
                If not specified, the session's default region will be used.
        """
        super().__init__(CloudProvider.AWS, account_name, should_clean_before_scan, output_path, commands_path)
        self.regions_filter: str = ','.join(regions_filter) if regions_filter else ''
        self.max_attempts: int = max_attempts
        self.max_pool_connections: int = max_pool_connections
        self.command_timeout: int = command_timeout
        self.default_region: Optional[str] = default_region
