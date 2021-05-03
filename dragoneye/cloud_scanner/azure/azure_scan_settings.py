import os

from dragoneye.cloud_scanner.base_cloud_scanner import CloudScanSettings, CloudProvider


class AzureCloudScanSettings(CloudScanSettings):
    def __init__(self,
                 commands_path: str,
                 subscription_id: str,
                 account_name: str,
                 output_path: str = os.getcwd(),
                 should_clean_before_scan: bool = True
                 ):
        """
        The settings that the AzureScanner uses for azure scanning.
        :param commands_path: The path of a YAML file that describes the scan commands to be used.
        :param subscription_id: The subscription id you wish to scan.
        :param account_name: A name for the scan results.
        :param output_path: The directory where results will be saved. Defaults to current working directory.
        :param should_clean_before_scan: A flag that determines if prior results of this specific account (identified by account_name)
            should be deleted before scanning.
        """
        super().__init__(cloud_provider=CloudProvider.AZURE,
                         account_name=account_name,
                         should_clean_before_scan=should_clean_before_scan,
                         output_path=output_path,
                         commands_path=commands_path)
        self.subscription_id = subscription_id
