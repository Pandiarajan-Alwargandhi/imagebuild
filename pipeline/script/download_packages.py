import requests
import argparse
import os
import json
from bs4 import BeautifulSoup

# Function to download the file
def download_package(url, download_dir, credentials=None, verify_ssl=True):
    # Extract the filename from the URL and ensure we are not trying to save it as a directory
    local_filename = os.path.join(download_dir, url.split('/')[-1])
    
    if not local_filename or os.path.isdir(download_dir):  # Validate the path
        raise ValueError(f"Invalid URL or no filename detected: {url}")
    
    print(f"Downloading {url} to {local_filename} (SSL Verification: {verify_ssl})")

    # Make the HTTP request with or without credentials
    auth = (credentials['username'], credentials['password']) if credentials else None
    with requests.get(url, stream=True, verify=verify_ssl, auth=auth) as r:
        r.raise_for_status()  # Check for HTTP errors
        with open(local_filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

    print(f"Downloaded {local_filename}")

# Function to check and ensure URL is valid
def check_url_exists(url, credentials=None, verify_ssl=True):
    auth = (credentials['username'], credentials['password']) if credentials else None
    try:
        response = requests.head(url, auth=auth, verify=verify_ssl)
        return response.status_code == 200
    except Exception as e:
        print(f"Error checking URL: {url}, Error: {e}")
        return False

# Main logic to fetch the page, filter the packages, and download them
def main():
    parser = argparse.ArgumentParser(description="Download the latest package for a given database type")
    parser.add_argument('--config', required=True, help="Path to the JSON config file")
    parser.add_argument('--product_groups', required=True, help="Product group to download (e.g., T24, FCM)")
    parser.add_argument('--version', required=True, help="Version of the product to download")
    parser.add_argument('--db_type', required=True, help="Database type (e.g., pos, h2d, etc.)")
    parser.add_argument('--ignore_ssl', action='store_true', help="Ignore SSL certificate errors")
    parser.add_argument('--username', help="Username for authenticated downloads")
    parser.add_argument('--password', help="Password for authenticated downloads")

    args = parser.parse_args()

    # Load the config file
    with open(args.config) as f:
        config = json.load(f)

    # Loop through the products in the config
    for product in config['products']:
        if product['name'] == args.product_groups:
            print(f"Processing product: {product['name']}")
            for package in product['packages']:
                # Replace {{version}} and {{db_type}} with the actual values in the path
                package_url = package['base_url'] + package['path'].replace('{{version}}', args.version).replace('{{db_type}}', args.db_type)
                
                # Handle credentials if required
                credentials = None
                if package.get('credentials_required', False):
                    credentials = {'username': args.username, 'password': args.password}
                
                # Check if URL exists before attempting to download
                if not check_url_exists(package_url, credentials, verify_ssl=not args.ignore_ssl):
                    print(f"Failed to fetch URL content, status code: 404 for {package_url}")
                    continue
                
                # Download the package
                download_package(package_url, config['download_dir'], credentials=credentials, verify_ssl=not args.ignore_ssl)

if __name__ == "__main__":
    main()
