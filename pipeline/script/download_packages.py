import requests
import argparse
import os
import json
from bs4 import BeautifulSoup

# Function to list files in the directory and return the latest matching file based on pattern
def get_latest_file_from_directory(url, file_name_pattern, auth=None, verify_ssl=True):
    response = requests.get(url, auth=auth, verify=verify_ssl)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'html.parser')
    links = soup.find_all('a')

    # Filter files based on the pattern provided in the config
    matching_files = [link['href'] for link in links if file_name_pattern in link['href'] and link['href'].endswith('.war')]

    if not matching_files:
        raise ValueError(f"No valid files found matching the pattern: {file_name_pattern}")

    # Sort the files by name, assuming the most recent file appears later in sorting (adjust logic if necessary)
    matching_files.sort(reverse=True)
    return matching_files[0]  # Return the latest file

# Function to download the file
def download_package(url, download_dir, credentials=None, verify_ssl=True):
    local_filename = os.path.join(download_dir, url.split('/')[-1])
    
    if not local_filename:
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
                package_url = package['base_url'] + package['path'].replace('{{version}}', args.version).replace('{{db_type}}', args.db_type)
                
                credentials = None
                if package.get('credentials_required', False):
                    credentials = {'username': args.username, 'password': args.password}

                # Find the latest file in the directory if required
                if 'file_name_pattern' in package:
                    file_name_pattern = package['file_name_pattern'].replace('{{version}}', args.version).replace('{{db_type}}', args.db_type)
                    latest_file = get_latest_file_from_directory(package_url, file_name_pattern, auth=credentials, verify_ssl=not args.ignore_ssl)
                    file_url = package_url + latest_file
                else:
                    file_url = package_url + package['file_name']
                
                # Download the file
                download_package(file_url, config['download_dir'], credentials=credentials, verify_ssl=not args.ignore_ssl)

if __name__ == "__main__":
    main()
