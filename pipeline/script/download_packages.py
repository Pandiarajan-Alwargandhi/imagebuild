import requests
from bs4 import BeautifulSoup
import argparse
import os

# Function to download the file
def download_package(url, download_dir, verify_ssl):
    local_filename = os.path.join(download_dir, url.split('/')[-1])
    print(f"Downloading {url} to {local_filename}")
    with requests.get(url, stream=True, verify=verify_ssl) as r:  # Add verify=verify_ssl
        r.raise_for_status()
        with open(local_filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
    print(f"Downloaded {local_filename}")

# Function to filter the packages for a given database type and only `.zip` files
def filter_packages(links, db_type):
    filtered = []
    for link in links:
        # Ensure we are filtering for the exact db_type (e.g., -pos-) but not variations like -pos-aws-
        filename = link.split('/')[-1]
        if f"-{db_type}-" in filename and not f"-{db_type}-aws-" in filename and filename.endswith('.zip'):
            filtered.append(link)
    return filtered

# Main logic to fetch the page, filter the packages, and download the latest one
def main():
    parser = argparse.ArgumentParser(description="Download the latest package for a given database type")
    parser.add_argument('--config', required=True, help="Path to the packages_config.json file")
    parser.add_argument('--product_groups', required=True, help="Comma-separated list of product groups to download")
    parser.add_argument('--version', required=True, help="Version of the packages to download")
    parser.add_argument('--db_type', required=True, help="Database type for T24 (e.g., pos, sql, etc.)")

    args = parser.parse_args()

    with open(args.config, 'r') as f:
        config = json.load(f)

    for product in config['products']:
        if product['name'] in args.product_groups.split(','):
            print(f"Processing product: {product['name']}")
            for package in product['packages']:
                # Replace {{version}} and {{db_type}} in the URL
                package_url = replace_version_and_db_type_in_url(package, args.version, args.db_type)

                # Determine if SSL verification is required
                verify_ssl = not package.get('credentials_required', False)

                # Download the package
                try:
                    response = requests.get(package_url, verify=verify_ssl)
                    if response.status_code != 200:
                        print(f"Failed to fetch URL content, status code: {response.status_code}")
                        continue
                    print(f"Fetched URL: {package_url}")
                except requests.exceptions.SSLError:
                    print(f"SSL Error while trying to access {package_url}")
                    continue

if __name__ == "__main__":
    main()
