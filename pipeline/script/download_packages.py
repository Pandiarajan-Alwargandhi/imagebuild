import requests
from bs4 import BeautifulSoup
import argparse
import os
import json
import urllib3
from urllib.parse import urljoin

# Suppress SSL warnings if ignoring SSL verification
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# Function to download the file
def download_package(url, download_dir, credentials=None, verify_ssl=True):
    # Ensure download directory exists
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)
    
    # Extract filename from the URL
    local_filename = os.path.join(download_dir, url.split('/')[-1])

    print(f"Downloading {url} to {local_filename} (SSL Verification: {verify_ssl})")

    try:
        if credentials:
            auth = (credentials['username'], credentials['password'])
            with requests.get(url, auth=auth, stream=True, verify=verify_ssl) as r:
                r.raise_for_status()
                with open(local_filename, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
        else:
            with requests.get(url, stream=True, verify=verify_ssl) as r:
                r.raise_for_status()
                with open(local_filename, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
        print(f"Downloaded {local_filename}")
    except requests.exceptions.RequestException as e:
        print(f"Failed to download {url}: {e}")
        raise


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
    parser.add_argument('--config', required=True, help="Path to the JSON config file")
    parser.add_argument('--product_groups', required=True, help="Product groups to download (comma separated)")
    parser.add_argument('--version', required=True, help="Version of the product")
    parser.add_argument('--db_type', required=True, help="Database type (e.g., pos, h2d, etc.)")
    parser.add_argument('--ignore_ssl', action='store_true', help="Ignore SSL certificate verification")
    parser.add_argument('--username', help="Username for authentication")
    parser.add_argument('--password', help="Password for authentication")
    args = parser.parse_args()

    verify_ssl = not args.ignore_ssl
    credentials = None
    if args.username and args.password:
        credentials = {
            'username': args.username,
            'password': args.password
        }

    # Load the configuration file
    with open(args.config, 'r') as f:
        config = json.load(f)

    # Process each product group specified
    for product_group in args.product_groups.split(','):
        for product in config['products']:
            if product['name'] == product_group:
                print(f"Processing product: {product_group}")

                for package in product['packages']:
                    # Replace version in URL
                    package_url = urljoin(package['base_url'], package['path'].replace('{{version}}', args.version))

                    print(f"Fetching contents of {package_url} (SSL Verification: {verify_ssl})")

                    try:
                        response = requests.get(package_url, verify=verify_ssl)
                        if response.status_code != 200:
                            print(f"Failed to fetch URL content, status code: {response.status_code}")
                            continue

                        # Parse the HTML content
                        soup = BeautifulSoup(response.content, 'html.parser')
                        links = [a['href'] for a in soup.find_all('a', href=True)]
                        print(f"Found {len(links)} links on the page")

                        # Filter the packages for the given database type (only applies if db_filter is True)
                        filtered_packages = filter_packages(links, args.db_type) if package.get('db_filter') else links
                        print(f"Filtered packages: {filtered_packages}")

                        # If there are any packages, download the latest `.zip` one
                        if filtered_packages:
                            latest_package = filtered_packages[-1]  # Get the last `.zip` package in the filtered list

                            # Ensure the link is absolute
                            if not latest_package.startswith('http'):
                                download_url = urljoin(package_url, latest_package)
                            else:
                                download_url = latest_package

                            download_package(download_url, config['download_dir'], credentials=credentials, verify_ssl=verify_ssl)
                        else:
                            print(f"No valid packages found for {package['package_name']}")

                    except requests.exceptions.RequestException as e:
                        print(f"Failed to fetch URL content for {package['package_name']}: {e}")
                        continue


if __name__ == "__main__":
    main()
