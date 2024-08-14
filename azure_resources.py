import os
import uuid
import datetime
from azure.identity import ClientSecretCredential
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.containerregistry import ContainerRegistryManagementClient
from azure.mgmt.keyvault import KeyVaultManagementClient
from azure.mgmt.storage import StorageManagementClient
from azure.mgmt.containerservice import ContainerServiceClient
from azure.storage.fileshare import ShareServiceClient

# Fetch credentials from environment variables
subscription_id = os.getenv('AZURE_SUBSCRIPTION_ID')
tenant_id = os.getenv('AZURE_TENANT_ID')
client_id = os.getenv('AZURE_CLIENT_ID')
client_secret = os.getenv('AZURE_CLIENT_SECRET')

if not all([subscription_id, tenant_id, client_id, client_secret]):
    raise EnvironmentError("One or more Azure credentials are not set in the environment variables.")

location = 'eastus'
tags = {
    'DateOfCommission': datetime.datetime.now().strftime("%Y-%m-%d"),
    'DateOfDecommission': 'TBD',
    'CreatedBy': 'YourName',
    'PurposeOfCreation': 'Testing'
}
vnet_address_space = '10.4.0.0/20'
custom_vnet_address_space = None  # Set this to customize VNET address space

# Generate a consistent UUID
unique_id = uuid.uuid4().hex[:5]

# Authenticate using service principal
credential = ClientSecretCredential(tenant_id, client_id, client_secret)

def get_supported_aks_versions(aks_client, location):
    try:
        orchestrators = aks_client.container_services.list_orchestrators(location, resource_type='managedClusters')
        versions = [version.orchestrator_version for version in orchestrators.orchestrators]
        versions.sort(key=lambda x: list(map(int, x.split('.'))))  # Sort versions
        return versions
    except Exception as e:
        print(f"Failed to get AKS versions: {e}")
        exit(1)

def create_resource_group(resource_client, resource_group_name):
    try:
        resource_group_params = {'location': location, 'tags': tags}
        resource_group = resource_client.resource_groups.create_or_update(resource_group_name, resource_group_params)
        print(f"Resource group '{resource_group_name}' created.")
        return resource_group
    except Exception as e:
        print(f"Failed to create resource group: {e}")
        exit(1)

def create_virtual_network(network_client, resource_group_name, vnet_name, custom_vnet_address_space):
    try:
        vnet_params = {
            'location': location,
            'address_space': {
                'address_prefixes': [custom_vnet_address_space or vnet_address_space]
            }
        }
        vnet_result = network_client.virtual_networks.begin_create_or_update(resource_group_name, vnet_name, vnet_params).result()
        print(f"Virtual network '{vnet_name}' created.")
        return vnet_result
    except Exception as e:
        print(f"Failed to create virtual network: {e}")
        exit(1)

def create_subnet(network_client, resource_group_name, vnet_name, subnet_name):
    try:
        subnet_params = {'address_prefix': '10.4.0.0/24'}
        subnet_result = network_client.subnets.begin_create_or_update(resource_group_name, vnet_name, subnet_name, subnet_params).result()
        print(f"Subnet '{subnet_name}' created.")
        return subnet_result
    except Exception as e:
        print(f"Failed to create subnet: {e}")
        exit(1)

def create_container_registry(acr_client, resource_group_name, acr_name):
    try:
        acr_params = {
            'location': location,
            'sku': {'name': 'Basic'},
            'admin_user_enabled': True,
            'tags': tags
        }
        acr_result = acr_client.registries.begin_create(resource_group_name, acr_name, acr_params).result()
        print(f"Container registry '{acr_name}' created.")
        return acr_result
    except Exception as e:
        print(f"Failed to create container registry: {e}")
        exit(1)

def create_key_vault(key_vault_client, resource_group_name, kv_name):
    try:
        kv_params = {
            'location': location,
            'properties': {
                'sku': {'family': 'A', 'name': 'standard'},
                'tenant_id': tenant_id,
                'access_policies': []
            },
            'tags': tags
        }
        kv_result = key_vault_client.vaults.begin_create_or_update(resource_group_name, kv_name, kv_params).result()
        print(f"Key Vault '{kv_name}' created.")
        return kv_result
    except Exception as e:
        print(f"Failed to create key vault: {e}")
        exit(1)

def create_storage_account(storage_client, resource_group_name, storage_account_name, vnet_name, subnet_name):
    try:
        storage_params = {
            'location': location,
            'sku': {'name': 'Standard_LRS'},
            'kind': 'StorageV2',
            'tags': tags,
            'properties': {
                'publicNetworkAccess': 'Disabled',  # Disable public network access
                'allowBlobPublicAccess': False,  # Explicitly deny blob public access
                'networkAcls': {
                    'bypass': 'AzureServices',
                    'virtualNetworkRules': [
                        {
                            'id': f'/subscriptions/{subscription_id}/resourceGroups/{resource_group_name}/providers/Microsoft.Network/virtualNetworks/{vnet_name}/subnets/{subnet_name}'
                        }
                    ],
                    'defaultAction': 'Deny'
                }
            }
        }
        storage_account = storage_client.storage_accounts.begin_create(resource_group_name, storage_account_name, storage_params).result()
        print(f"Storage account '{storage_account_name}' created with restricted network access and no public blob access.")
        return storage_account
    except Exception as e:
        print(f"Failed to create storage account: {e}")
        exit(1)

def create_file_share(storage_client, resource_group_name, storage_account_name, file_share_name):
    try:
        share_params = {'share_quota': 5}
        file_share = storage_client.file_shares.create(resource_group_name, storage_account_name, file_share_name, share_params)
        print(f"File share '{file_share_name}' created.")
        return file_share
    except Exception as e:
        print(f"Failed to create file share: {e}")
        exit(1)

def create_aks_cluster(aks_client, resource_group_name, aks_name, subnet_result):
    try:
        supported_versions = get_supported_aks_versions(aks_client, location)
        if len(supported_versions) < 2:
            print("Not enough AKS versions available to determine n-1 version.")
            exit(1)
        
        # Select n-1 version
        kubernetes_version = supported_versions[-2]
        print(f"Using AKS version: {kubernetes_version}")

        aks_params = {
            'location': location,
            'kubernetes_version': kubernetes_version,
            'agent_pool_profiles': [{
                'name': 'nodepool1',
                'count': 3,
                'vm_size': 'Standard_E4s_v3',
                'os_type': 'Linux',
                'vnet_subnet_id': subnet_result.id,
                'mode': 'System'
            }],
            'dns_prefix': 'aksdns',
            'service_principal_profile': {
                'client_id': client_id,
                'secret': client_secret
            },
            'tags': tags
        }
        aks_result = aks_client.managed_clusters.begin_create_or_update(resource_group_name, aks_name, aks_params).result()
        print(f"AKS Cluster '{aks_name}' created.")
        return aks_result
    except Exception as e:
        print(f"Failed to create AKS cluster: {e}")
        exit(1)

# Resource Management Client
resource_client = ResourceManagementClient(credential, subscription_id)
resource_group_name = f'rg-{unique_id}'
create_resource_group(resource_client, resource_group_name)

# Network Management Client
network_client = NetworkManagementClient(credential, subscription_id)
vnet_name = f'vnet-{unique_id}'
vnet_result = create_virtual_network(network_client, resource_group_name, vnet_name, custom_vnet_address_space)

subnet_name = f'subnet-{unique_id}'
subnet_result = create_subnet(network_client, resource_group_name, vnet_name, subnet_name)

# Container Registry Management Client
acr_client = ContainerRegistryManagementClient(credential, subscription_id)
acr_name = f'acr{unique_id}'
create_container_registry(acr_client, resource_group_name, acr_name)

# Key Vault Management Client
key_vault_client = KeyVaultManagementClient(credential, subscription_id)
kv_name = f'kv-{unique_id}'
create_key_vault(key_vault_client, resource_group_name, kv_name)

# Storage Management Client
storage_client = StorageManagementClient(credential, subscription_id)
storage_account_name = f'sa{unique_id}'
storage_account = create_storage_account(storage_client, resource_group_name, storage_account_name, vnet_name, subnet_name)

file_share_name = 'tafjud'
create_file_share(storage_client, resource_group_name, storage_account_name, file_share_name)

# Container Service Client
aks_client = ContainerServiceClient(credential, subscription_id)
aks_name = f'aks-{unique_id}'
create_aks_cluster(aks_client, resource_group_name, aks_name, subnet_result)

print("Script execution completed.")
