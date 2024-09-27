import requests
from bs4 import BeautifulSoup
import argparse
import os
import json


# Function to download the file
def download_package(url, download_dir, credentials=None):
    local_filename = os.path.join(download_dir, url.split('/')[-1])
    print(f"Downloading {url} to {local_filename}")

    headers = {}
    if credentials:
        headers = {'Authorization': f'Basic {credentials}'}

    with requests.get(url, headers=headers, stream=True) as r:
        r.raise_for_status()
        with open(local_filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
    print(f"Downloaded {local_filename}")


# Function to filter packages based on database type for T24 or any other product requiring filtering
def filter_packages(links, db_type):
    filtered = []
    for link in links:
        filename = link.split('/')[-1]
        if f"-{db_type}-" in filename and not f"-{db_type}-aws-" in filename and filename.endswith('.zip'):
            filtered.append(link)
    return filtered


# Main logic to fetch the page, filter the packages, and download the latest one
def main():
    parser = argparse.ArgumentParser(description="Download packages based on product, version, and database type")
    parser.add_argument('--config', required=True, help="Path to the JSON configuration file")
    parser.add_argument('--product_groups', required=True, help="Comma-separated list of product groups (e.g., T24,FCM)")
    parser.add_argument('--db_type', required=False, help="Database type for T24 (e.g., pos, sql)")
    parser.add_argument('--version', required=True, help="Version of the product to download")

    args = parser.parse_args()

    # Load the JSON configuration file
    with open(args.config, 'r') as f:
        config = json.load(f)

    download_dir = config.get('download_dir', '/tmp/downloads')
    os.makedirs(download_dir, exist_ok=True)

    # Split product groups into a list
    selected_products = args.product_groups.split(',')

    for product in config['products']:
        if product['name'] in selected_products:
            print(f"Processing product: {product['name']}")
            for package in product['packages']:
                version = args.version  # use Jenkins-passed version
                db_type = args.db_type if package.get('db_filter') else None

                # Build the download URL
                package_url = f"{package['base_url']}/{version}{package['path']}"
                print(f"Fetching contents of {package_url}")

                response = requests.get(package_url)
                if response.status_code != 200:
                    print(f"Failed to fetch URL content, status code: {response.status_code}")
                    continue

                soup = BeautifulSoup(response.content, 'html.parser')
                links = [a['href'] for a in soup.find_all('a', href=True)]
                print(f"Found {len(links)} links on the page")

                if db_type:
                    filtered_packages = filter_packages(links, db_type)
                else:
                    filtered_packages = [link for link in links if link.endswith(('.zip', '.war', '.jar'))]

                if not filtered_packages:
                    print(f"No valid packages found for {package['package_name']}")
                    continue

                # Select the latest package
                latest_package = sorted(filtered_packages)[-1]
                if not latest_package.startswith('http'):
                    download_url = package_url + latest_package
                else:
                    download_url = latest_package

                # If credentials are needed
                credentials = None
                if package.get('credentials_required'):
                    credentials = package['jenkins_credentials_id']  # Placeholder for Jenkins credentials
                    print(f"Using credentials: {credentials}")

                # Download the package
                download_package(download_url, download_dir, credentials)


if __name__ == "__main__":
    main()
