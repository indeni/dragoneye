![Dragoneye](dragoneye_header.png)

![CD](https://github.com/indeni/dragoneye/actions/workflows/cd.yaml/badge.svg) 
![PyPI](https://img.shields.io/badge/python-3.7+-blue.svg)
![GitHub license](https://img.shields.io/badge/license-MIT-brightgreen.svg)
![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)

# dragoneye
dragoneye is a Python tool that is used to collect data about a cloud environment using the cloud provider's APIs. It is intended to function as component in other tools who have the need to collect data quickly (multi-threaded), or as a command line to collect a snapshot of a cloud account.

dragoneye currently supports AWS (AssumeRole and AccessKey based collection) and Azure (with client secret).

# Setup
Clone this git repository, navigate to the root directory where `setup.py` is located and run:
```
pip install .
```
(note the period at the end of the command)

We recommend doing this within a virtual environment, like so:
```
python3.9 -m venv ./venv
. ./venv/bin/activate
pip install .
```

# Usage

## Programmatic Usage
Create an instance of one of the CollectRequest classes, such as AwsAccessKeyCollectRequest, AwsAssumeRoleCollectRequest, AzureCollectRequest and call the `collect` function. For example:

```python
from dragoneye import AwsScanner, AwsCloudScanSettings, AwsSessionFactory, AzureScanner, AzureCloudScanSettings, AzureAuthorizer, GcpCloudScanSettings, GcpCredentialsFactory, GcpScanner

### AWS ###
aws_settings = AwsCloudScanSettings(
    commands_path='/Users/dev/python/dragoneye/aws_commands_example.yaml',
    account_name='default', default_region='us-east-1', regions_filter=['us-east-1']
)

#### Using environment variables
session = AwsSessionFactory.get_session(profile_name=None, region='us-east-1')  # Raises exception if authentication is unsuccessful
aws_scan_output_directory = AwsScanner(session, aws_settings).scan()

#### Using an AWS Profile
session = AwsSessionFactory.get_session(profile_name='MyProfile', region='us-east-1')  # Raises exception if authentication is unsuccessful
aws_scan_output_directory = AwsScanner(session, aws_settings).scan()

#### Assume Role
session = AwsSessionFactory.get_session_using_assume_role(external_id='...',
                                                          role_arn="...",
                                                          region='us-east-1')
aws_scan_output_directory = AwsScanner(session, aws_settings).scan()

### Azure ###
azure_settings = AzureCloudScanSettings(
    commands_path='/Users/dev/python/dragoneye/azure_commands_example.yaml',
    subscription_id='...',
    account_name='my-account'
)

#### Using a registered application in Azure AD
token = AzureAuthorizer.get_authorization_token(
    tenant_id='...',
    client_id='...',
    client_secret='...'
)  # Raises exception if authentication is unsuccessful
azure_scan_output_directory = AzureScanner(token, azure_settings).scan()

### GCP ###
gcp_settings = GcpCloudScanSettings(commands_path='/Users/dev/python/dragoneye/gcp_commands_example.yaml',
                                    account_name='gcp', project_id='project-id')

# Authenticating by GCP default auth mechanism:
#    Checks environment in order of precedence:
#    - Environment variable GOOGLE_APPLICATION_CREDENTIALS pointing to
#      a file with stored credentials information.
#    - Stored "well known" file associated with `gcloud` command line tool.
#    - Google App Engine (production and testing)
#    - Google Compute Engine production environment.
default_credentials = GcpCredentialsFactory.get_default_credentials()
# Using a file that contains the service account credentials 
service_account_file_credentials = GcpCredentialsFactory.from_service_account_file('filepath.json')
# Using a dictionary that contains the service account credentials (the content of the file from above example)
service_account_dict_credentials = GcpCredentialsFactory.from_service_account_info({'...': '...'})
# Using impersonation method (service_account_A allowing service_account_B to generate short-lived credentials of service_account_A)
impersonation_credentials = GcpCredentialsFactory.impersonate(default_credentials, 'client_email@google.com', ['https://www.googleapis.com/auth/compute.readonly'])
# Authenticating from an AWS resource via a credentials config file defined by the 'Workload Identity Federation'
wif_credentials = GcpCredentialsFactory.from_aws_credentials_config_file('filepath.json')
# Same as above, but with the content of the above file
wif_credentials = GcpCredentialsFactory.from_aws_credentials_config_info({'...': '...'})

gcp_scan_output_directory = GcpScanner(default_credentials, gcp_settings)
```

## CLI usage

### For collecting data from AWS
Dragoneye will use the same mechanisms boto3 uses for authentication. It will generally look for 
AWS_ACCESS_KEY_ID, etc. as environment variables.
```
dragoneye aws
```

### For collecting data from Azure
You can authenticate in one of two ways:
1. `az login`, which will allow dragoneye to use credentials loaded through Azure CLI.
2. With client id and secret of an application registered in your Azure AD.
```
dragoneye azure
```

### For collecting data from GP
You can authenticate in several ways:
1. `gcloud auth application-default login`, which will allow dragoneye to use credentials loaded through GCP CLI.
2. With service account credentials - either a file, or its content.
3. With impersonation mechanism; service_account_A allowing service_account_B to generate short-lived credentials of service_account_A
4. With Workload Identity Federation mechanism, authenticating from AWS.
```
dragoneye gcp
```