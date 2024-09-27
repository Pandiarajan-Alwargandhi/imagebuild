import requests
from bs4 import BeautifulSoup
import argparse
import os

# Function to download the file
def download_package(url, download_dir, credentials=None, verify_ssl=True):
    # Ensure that the URL contains a file, not a directory
    filename = url.split('/')[-1]
    
    # If filename is empty or ends with '/', this indicates it's a directory and not a file
    if not filename or filename.endswith('/'):
        print(f"Error: URL {url} does not point to a valid file.")
        return

    local_filename = os.path.join(download_dir, filename)

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

# Function to fetch and filter links
def filter_packages(links, db_type):
    filtered = []
    for link in links:
        filename = link.split('/')[-1]
        # Filter for correct db_type and exclude variations like -pos-aws-
        if f"-{db_type}-" in filename and not f"-{db_type}-aws-" in filename and filename.endswith('.zip'):
            filtered.append(link)
    return filtered

# Function to fetch links from a webpage
def fetch_page_links(url, credentials=None, verify_ssl=True):
    auth = None
    if credentials:
        print(f"Fetching contents of {url} with credentials: {credentials['username']} (SSL Verification: {verify_ssl})")
        auth = (credentials['username'], credentials['password'])
    else:
        print(f"Fetching contents of {url} (SSL Verification: {verify_ssl})")

    try:
        response = requests.get(url, verify=verify_ssl, auth=auth)
        if response.status_code != 200:
            print(f"Failed to fetch URL content, status code: {response.status_code}")
            return []
        page_content = response.content
        soup = BeautifulSoup(page_content, 'html.parser')
        links = [a['href'] for a in soup.find_all('a', href=True)]
        print(f"Found {len(links)} links on the page")
        return links
    except requests.exceptions.SSLError as e:
        print(f"SSL verification error for {url}: {e}")
        return []
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return []

def main():
    parser = argparse.ArgumentParser(description="Download the latest package for a given database type")
    parser.add_argument('--config', required=True, help="Path to the configuration JSON")
    parser.add_argument('--product_groups', required=True, help="Product groups to download (comma-separated)")
    parser.add_argument('--version', required=True, help="Version to download")
    parser.add_argument('--db_type', required=True, help="Database type (e.g., pos, h2d, etc.)")
    parser.add_argument('--ignore_ssl', action='store_true', help="Ignore SSL verification")
    parser.add_argument('--username', required=False, help="Username for credentials")
    parser.add_argument('--password', required=False, help="Password for credentials")
    args = parser.parse_args()

    # Load the configuration
    with open(args.config) as f:
        config = json.load(f)

    # Process product groups
    product_groups = args.product_groups.split(',')
    version = args.version
    db_type = args.db_type
    verify_ssl = not args.ignore_ssl

    credentials = None
    if args.username and args.password:
        credentials = {
            'username': args.username,
            'password': args.password
        }

    # Loop through the products in the config file
    for product in config['products']:
        if product['name'] in product_groups:
            print(f"Processing product: {product['name']}")
            for package in product['packages']:
                # Construct the correct package URL using version
                package_url = f"{package['base_url']}/{version}/{package['package_name']}/"
                if package.get('db_filter', False):
                    package_url = f"{package_url}{db_type}/"

                # Ensure package_url doesn't end with "//"
                package_url = package_url.rstrip('/')

                # Fetch the links on the page
                page_links = fetch_page_links(package_url, credentials=credentials if package['credentials_required'] else None, verify_ssl=verify_ssl)
                if not page_links:
                    continue

                # Filter the packages if db_filter is required
                if package.get('db_filter', False):
                    page_links = filter_packages(page_links, db_type)

                print("Filtered packages:")
                for link in page_links:
                    print(link)

                # If there are any packages, download the first valid one (change as per your logic)
                if page_links:
                    download_url = package_url + page_links[0]
                    download_package(download_url, config['download_dir'], credentials=credentials if package['credentials_required'] else None, verify_ssl=verify_ssl)

if __name__ == "__main__":
    main()
