import requests
import argparse
import os
import json
from bs4 import BeautifulSoup

# Function to get the latest file from the directory based on the file name pattern
def get_latest_file_from_directory(url, file_name_pattern, auth=None, verify_ssl=True):
    print(f"Fetching contents of {url} (SSL Verification: {verify_ssl})")
    response = requests.get(url, auth=auth, verify=verify_ssl)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'html.parser')
    links = soup.find_all('a')

    # Log available files for debugging
    print("Available files in the directory:")
    for link in links:
        print(link['href'])

    # Filter files based on the pattern (relaxed matching)
    matching_files = [link['href'] for link in links if file_name_pattern in link['href']]

    if not matching_files:
        raise ValueError(f"No valid files found matching the pattern: {file_name_pattern}")

    # Sort the files to get the latest one
    matching_files.sort(reverse=True)
    print(f"Latest file found: {matching_files[0]}")
    return matching_files[0]  # Return the latest file

# Function to download the file
def download_package(url, download_dir, auth=None, verify_ssl=True):
    # Extract the filename from the URL and ensure we are not trying to save it as a directory
    local_filename = os.path.join(download_dir, url.split('/')[-1])
    
    if not local_filename:  # If the URL doesn't point to a valid file
        raise ValueError(f"Invalid URL or no filename detected: {url}")

    print(f"Downloading {url} to {local_filename} (SSL Verification: {verify_ssl})")

    # Make the HTTP request with or without credentials
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
                # Replace {{version}} and {{db_type}} with the actual values in the path and file name pattern
                package_url = package['base_url'] + package['path'].replace('{{version}}', args.version).replace('{{db_type}}', args.db_type)
                file_name_pattern = package['file_name_pattern'].replace('{{version}}', args.version).replace('{{db_type}}', args.db_type)

                # Handle credentials if required
                credentials = None
                if package.get('credentials_required', False):
                    credentials = (args.username, args.password)
                
                # Get the latest file matching the pattern
                latest_file = get_latest_file_from_directory(package_url, file_name_pattern, auth=credentials, verify_ssl=not args.ignore_ssl)
                
                # Construct the full URL for the file
                full_url = package_url + latest_file
                download_package(full_url, config['download_dir'], auth=credentials, verify_ssl=not args.ignore_ssl)

if __name__ == "__main__":
    main()
