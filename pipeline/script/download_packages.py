import requests
import argparse
import os
import json
from bs4 import BeautifulSoup

# Function to download the file
def download_package(url, download_dir, credentials=None, verify_ssl=True):
    # Extract the filename from the URL and ensure we are not trying to save it as a directory
    local_filename = os.path.join(download_dir, url.split('/')[-1])
    
    if not local_filename or os.path.isdir(local_filename):  # Validate the path
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

# Function to find the actual file link in the directory URL
def find_file_in_directory(url, db_type, credentials=None, verify_ssl=True):
    auth = (credentials['username'], credentials['password']) if credentials else None
    response = requests.get(url, auth=auth, verify=verify_ssl)
    
    if response.status_code != 200:
        raise ValueError(f"Failed to fetch URL content, status code: {response.status_code}")

    # Parse HTML to find links
    soup = BeautifulSoup(response.content, 'html.parser')
    links = [a['href'] for a in soup.find_all('a', href=True)]

    # Filter the links to find the file you're looking for
    filtered_links = [link for link in links if db_type in link and link.endswith('.zip')]  # Adjust the extension as needed

    if not filtered_links:
        raise ValueError(f"No valid file found for db_type {db_type} in directory: {url}")

    # Assume the last file is the one to download (usually the newest or most relevant one)
    return url + filtered_links[-1]

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
                
                # Find the actual file to download within the directory
                file_url = find_file_in_directory(package_url, args.db_type, credentials, verify_ssl=not args.ignore_ssl)

                # Download the package
                download_package(file_url, config['download_dir'], credentials=credentials, verify_ssl=not args.ignore_ssl)

if __name__ == "__main__":
    main()
