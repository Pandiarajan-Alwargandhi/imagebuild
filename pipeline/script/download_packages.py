import requests
import argparse
import os
import json
from bs4 import BeautifulSoup
import urllib3

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Function to download the file
def download_package(full_url, download_dir, auth=None, verify_ssl=True):
    local_filename = os.path.join(download_dir, full_url.split('/')[-1])

    print(f"Downloading {full_url} to {local_filename} (SSL Verification: {verify_ssl})")

    # Make the HTTP request with or without credentials
    with requests.get(full_url, stream=True, auth=auth, verify=verify_ssl) as r:
        r.raise_for_status()  # Check for HTTP errors
        with open(local_filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

    print(f"Downloaded {local_filename}")

# Function to get the latest file from a directory listing
def get_latest_file_from_directory(url, file_name_pattern, auth=None, verify_ssl=True, extension=".zip", is_utp_url=False):
    print(f"Fetching contents of {url} (SSL Verification: {verify_ssl})")
    response = requests.get(url, auth=auth, verify=verify_ssl)
    response.raise_for_status()  # Raise an error for bad HTTP responses
    soup = BeautifulSoup(response.text, 'html.parser')

    # List files matching the pattern and ensure only the required extension is included
    files = [a['href'] for a in soup.find_all('a') if file_name_pattern in a['href'] and a['href'].endswith(extension)]

    if not files:
        raise ValueError(f"No valid files found matching the pattern: {file_name_pattern} with extension {extension}")

    files.sort()

    print("Available files in the directory:")
    for file in files:
        print(file)

    latest_file = files[-1]  # The last file is the latest
    print(f"Latest file found: {latest_file}")

    # Return the full file URL for UTP URLs
    if is_utp_url:
        latest_file = url + latest_file.split('/')[-1]

    return latest_file

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
    parser.add_argument('--token', help="Token for authenticated downloads")  # New argument for token

    args = parser.parse_args()

    # Load the config file
    with open(args.config) as f:
        config = json.load(f)

    # Loop through the products in the config
    for product in config['products']:
        if product['name'] == args.product_groups:
            print(f"Processing product: {product['name']}")
            for package in product['packages']:
                base_url = package['base_url']
                package_url = base_url + package['path'].replace('{{version}}', args.version)
                
                # Handle credentials if required
                credentials = None
                if package.get('credentials_required', False):
                    if args.token:
                        credentials = (args.username, args.token)
                    elif args.password:
                        credentials = (args.username, args.password)
                    else:
                        raise ValueError("Authentication required but no token or password provided")

                # Pattern to find the file
                file_name_pattern = package['file_name_pattern'].replace('{{version}}', args.version).replace('{{db_type}}', args.db_type)

                # Use extension from JSON
                extension = package.get('file_extension', '.zip')
                is_utp_url = package.get('is_utp_url', False)

                # Fetch the latest file based on the pattern
                latest_file = get_latest_file_from_directory(package_url, file_name_pattern, auth=credentials, verify_ssl=not args.ignore_ssl, extension=extension, is_utp_url=is_utp_url)

                # Download the latest file
                download_package(latest_file, config['download_dir'], auth=credentials, verify_ssl=not args.ignore_ssl)

if __name__ == "__main__":
    main()
