import requests
from bs4 import BeautifulSoup
import argparse
import os

def download_package(url, download_dir, credentials=None, verify_ssl=True):
    local_filename = os.path.join(download_dir, url.split('/')[-1])
    print(f"Downloading {url} to {local_filename} (SSL Verification: {verify_ssl})")
    
    auth = (credentials['username'], credentials['password']) if credentials else None

    with requests.get(url, auth=auth, stream=True, verify=verify_ssl) as r:
        if r.status_code == 404:
            print(f"Failed to fetch URL content, status code: 404")
            return
        r.raise_for_status()
        with open(local_filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
    print(f"Downloaded {local_filename}")

def main():
    parser = argparse.ArgumentParser(description="Download the latest package for a given database type")
    parser.add_argument('--config', required=True, help="Path to the config JSON")
    parser.add_argument('--product_groups', required=True, help="Product group to download")
    parser.add_argument('--version', required=True, help="Version of the product")
    parser.add_argument('--db_type', required=True, help="Database type (e.g., pos, h2d, etc.)")
    parser.add_argument('--ignore_ssl', action='store_true', help="Ignore SSL verification")
    parser.add_argument('--username', help="Username for authenticated downloads")
    parser.add_argument('--password', help="Password for authenticated downloads")

    args = parser.parse_args()

    # Read the config file
    import json
    with open(args.config) as f:
        config = json.load(f)

    # Process each product
    for product in config['products']:
        if product['name'] == args.product_groups:
            print(f"Processing product: {product['name']}")

            for package in product['packages']:
                # Construct the URL
                base_url = package['base_url']
                package_url = f"{base_url}{package['path'].replace('{{version}}', args.version)}"
                
                # Handle credentials
                credentials = None
                if package.get('credentials_required'):
                    credentials = {'username': args.username, 'password': args.password}
                
                print(f"Fetching contents of {package_url} (SSL Verification: {not args.ignore_ssl})")
                download_package(package_url, config['download_dir'], credentials=credentials, verify_ssl=not args.ignore_ssl)

if __name__ == "__main__":
    main()
