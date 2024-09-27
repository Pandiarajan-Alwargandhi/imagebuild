import requests
from bs4 import BeautifulSoup
import argparse
import os
import json

# Function to download the file
def download_package(url, download_dir, credentials=None, verify_ssl=True):
    local_filename = os.path.join(download_dir, url.split('/')[-1])
    auth = (credentials['username'], credentials['password']) if credentials else None

    print(f"Downloading {url} to {local_filename} (SSL Verification: {verify_ssl})")
    
    with requests.get(url, stream=True, auth=auth, verify=verify_ssl) as r:
        r.raise_for_status()  # Raise an error if the download fails
        with open(local_filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
    print(f"Downloaded {local_filename}")

# Function to filter the packages for a given database type and only `.zip` files
def filter_packages(links, db_type):
    filtered = []
    for link in links:
        filename = link.split('/')[-1]
        # Ensure we are filtering for the exact db_type (e.g., -pos-) but not variations like -pos-aws-
        if f"-{db_type}-" in filename and not f"-{db_type}-aws-" in filename and filename.endswith('.zip'):
            filtered.append(link)
    return filtered

# Main logic to fetch the page, filter the packages, and download the latest one
def main():
    parser = argparse.ArgumentParser(description="Download the latest packages based on configuration")
    parser.add_argument('--config', required=True, help="Path to the config JSON file")
    parser.add_argument('--product_groups', required=True, help="Comma-separated list of product groups to download (e.g., T24,FCM)")
    parser.add_argument('--version', required=True, help="Version of the product (e.g., 202409)")
    parser.add_argument('--db_type', required=True, help="Database type for the APP package (e.g., pos, pos-aws)")
    parser.add_argument('--ignore_ssl', action='store_true', help="Ignore SSL verification")
    parser.add_argument('--username', help="Username for authentication (used for credentialed downloads)")
    parser.add_argument('--password', help="Password for authentication (used for credentialed downloads)")

    args = parser.parse_args()

    # Parse product groups
    product_groups = args.product_groups.split(',')

    # Load the configuration file
    with open(args.config, 'r') as f:
        config = json.load(f)

    download_dir = config['download_dir']
    verify_ssl = not args.ignore_ssl

    # Ensure the download directory exists
    os.makedirs(download_dir, exist_ok=True)

    # Iterate through product groups
    for product in config['products']:
        if product['name'] in product_groups:
            print(f"Processing product: {product['name']}")

            # Iterate through the packages
            for package in product['packages']:
                package_url = f"{package['base_url']}/{args.version}/{package['path']}"
                print(f"Fetching contents of {package_url} (SSL Verification: {verify_ssl})")

                # Make request to the package URL
                response = requests.get(package_url, verify=verify_ssl)
                if response.status_code != 200:
                    print(f"Failed to fetch URL content, status code: {response.status_code}")
                    continue

                # Parse the HTML
                soup = BeautifulSoup(response.content, 'html.parser')
                links = [a['href'] for a in soup.find_all('a', href=True)]
                print(f"Found {len(links)} links on the page")

                # Apply filtering if db_type is required
                if package.get('db_filter', False):
                    filtered_packages = filter_packages(links, args.db_type)
                else:
                    filtered_packages = [link for link in links if link.endswith('.war') or link.endswith('.jar') or link.endswith('.zip')]

                print("Filtered packages:")
                for pkg in filtered_packages:
                    print(pkg)

                # Download the latest filtered package, if available
                if filtered_packages:
                    latest_package = filtered_packages[-1]  # Get the last one as it's often the latest
                    if not latest_package.startswith('http'):
                        latest_package = package_url + latest_package

                    # Prepare credentials if required
                    credentials = None
                    if package.get('credentials_required', False):
                        credentials = {
                            'username': args.username,
                            'password': args.password
                        }
                        print(f"Downloading with credentials: {args.username}")

                    # Download the package
                    try:
                        download_package(latest_package, download_dir, credentials=credentials, verify_ssl=verify_ssl)
                    except Exception as e:
                        print(f"Failed to download {package['package_name']} from {package_url}: {e}")
                else:
                    print(f"No valid packages found for {package['package_name']} at {package_url}")

if __name__ == "__main__":
    main()
