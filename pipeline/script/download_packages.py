import requests
import argparse
import os
import json
from bs4 import BeautifulSoup

# Function to download the file
def download_package(base_url, file_name, download_dir, auth=None, verify_ssl=True):
    # Construct the full URL using base_url and file_name (which contains only the relative path or file name)
    full_url = base_url.rstrip('/') + '/' + file_name

    # Local file path to save the file
    local_filename = os.path.join(download_dir, file_name.split('/')[-1])
    
    print(f"Downloading {full_url} to {local_filename} (SSL Verification: {verify_ssl})")

    # Make the HTTP request with or without credentials
    with requests.get(full_url, stream=True, auth=auth, verify=verify_ssl) as r:
        r.raise_for_status()  # Check for HTTP errors
        with open(local_filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

    print(f"Downloaded {local_filename}")

# Function to get the latest file from a directory listing
def get_latest_file_from_directory(url, file_name_pattern, auth=None, verify_ssl=True):
    print(f"Fetching contents of {url} (SSL Verification: {verify_ssl})")
    response = requests.get(url, auth=auth, verify=verify_ssl)
    response.raise_for_status()  # Raise an error for bad HTTP responses
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # List files matching the pattern
    files = [a['href'] for a in soup.find_all('a') if file_name_pattern in a['href']]
    
    if not files:
        raise ValueError(f"No valid files found matching the pattern: {file_name_pattern}")
    
    # Sort the files to ensure the latest one comes last (you can adjust the logic if needed)
    files.sort()
    
    print("Available files in the directory:")
    for file in files:
        print(file)
    
    latest_file = files[-1]  # The last file is the latest
    print(f"Latest file found: {latest_file}")
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

    args = parser.parse_args()

    # Load the config file
    with open(args.config) as f:
        config = json.load(f)

    # Loop through the products in the config
    for product in config['products']:
        if product['name'] == args.product_groups:
            print(f"Processing product: {product['name']}")
            for package in product['packages']:
                # Replace placeholders in the base_url and path
                base_url = package['base_url']
                package_url = base_url + package['path'].replace('{{version}}', args.version)

                # Pattern to find the file
                file_name_pattern = package['file_name_pattern'].replace('{{version}}', args.version).replace('{{db_type}}', args.db_type)
                
                # Handle credentials if required
                credentials = None
                if package.get('credentials_required', False):
                    credentials = (args.username, args.password)

                # Fetch the latest file based on the pattern
                latest_file = get_latest_file_from_directory(package_url, file_name_pattern, auth=credentials, verify_ssl=not args.ignore_ssl)

                # Download the latest file
                download_package(package_url, latest_file, config['download_dir'], auth=credentials, verify_ssl=not args.ignore_ssl)

if __name__ == "__main__":
    main()
