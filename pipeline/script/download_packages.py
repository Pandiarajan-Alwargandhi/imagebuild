import requests
import argparse
import os
import json
from bs4 import BeautifulSoup

# Function to download a package
def download_package(url, download_dir, credentials=None, verify_ssl=True):
    local_filename = os.path.join(download_dir, url.split('/')[-1])
    auth = None

    if credentials:
        print(f"Downloading with credentials: {credentials['username']}")
        auth = (credentials['username'], credentials['password'])

    print(f"Downloading {url} to {local_filename} (SSL Verification: {verify_ssl})")
    
    try:
        with requests.get(url, stream=True, auth=auth, verify=verify_ssl) as r:
            r.raise_for_status()
            with open(local_filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
        print(f"Downloaded {local_filename}")
    except requests.exceptions.HTTPError as e:
        print(f"Failed to download {url}: {str(e)}")

# Function to filter the packages for a given database type and only `.zip` files
def filter_packages(links, db_type):
    filtered = []
    for link in links:
        filename = link.split('/')[-1]
        if f"-{db_type}-" in filename and not f"-{db_type}-aws-" in filename and filename.endswith('.zip'):
            filtered.append(link)
    return filtered

# Main logic to fetch the page, filter the packages, and download the latest one
def main():
    parser = argparse.ArgumentParser(description="Download the latest package for a given product group")
    parser.add_argument('--config', required=True, help="Path to the config JSON")
    parser.add_argument('--product_groups', required=True, help="Product groups to download (comma-separated)")
    parser.add_argument('--version', required=True, help="Version of the product to download")
    parser.add_argument('--db_type', required=False, help="Database type for filtering preimage kits")
    parser.add_argument('--ignore_ssl', action='store_true', help="Ignore SSL certificate verification")
    parser.add_argument('--username', help="Username for authentication (from Jenkins credentials)")
    parser.add_argument('--password', help="Password for authentication (from Jenkins credentials)")

    args = parser.parse_args()
    verify_ssl = not args.ignore_ssl

    # Load the configuration file
    with open(args.config, 'r') as f:
        config = json.load(f)

    product_groups = args.product_groups.split(',')

    for product in config['products']:
        if product['name'] in product_groups:
            print(f"Processing product: {product['name']}")
            for package in product['packages']:
                # Construct the download URL
                package_url = f"{package['base_url']}/{args.version}/{package['path']}"
                print(f"Fetching contents of {package_url} (SSL Verification: {verify_ssl})")

                if package.get('db_filter', False) and args.db_type:
                    # Fetch and filter preimage kits based on db_type
                    response = requests.get(package_url, verify=verify_ssl)
                    if response.status_code != 200:
                        print(f"Failed to fetch URL content, status code: {response.status_code}")
                        continue

                    page_content = response.content
                    soup = BeautifulSoup(page_content, 'html.parser')
                    links = [a['href'] for a in soup.find_all('a', href=True)]
                    print(f"Found {len(links)} links on the page")

                    filtered_packages = filter_packages(links, args.db_type)
                    print("Filtered packages:")
                    for pkg in filtered_packages:
                        print(pkg)

                    # Download the last filtered package
                    if filtered_packages:
                        latest_package = filtered_packages[-1]
                        download_package(latest_package, config['download_dir'], verify_ssl=verify_ssl)
                else:
                    # Handle packages that do not need db filtering
                    if package.get('credentials_required', False):
                        credentials = {
                            'username': args.username,
                            'password': args.password
                        }
                        download_package(package_url, config['download_dir'], credentials=credentials, verify_ssl=verify_ssl)
                    else:
                        download_package(package_url, config['download_dir'], verify_ssl=verify_ssl)

if __name__ == "__main__":
    main()
