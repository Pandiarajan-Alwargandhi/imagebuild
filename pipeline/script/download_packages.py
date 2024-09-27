import requests
from bs4 import BeautifulSoup
import argparse
import os
import json

# Function to download the file
def download_package(url, download_dir, verify_ssl=True):
    local_filename = os.path.join(download_dir, url.split('/')[-1])
    print(f"Downloading {url} to {local_filename} (SSL Verification: {verify_ssl})")
    with requests.get(url, stream=True, verify=verify_ssl) as r:
        if r.status_code == 404:
            print(f"Failed to download {url}, status code: 404")
            return
        r.raise_for_status()
        with open(local_filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
    print(f"Downloaded {local_filename}")

# Function to fetch and filter the packages for a given database type
def fetch_and_filter_packages(base_url, db_type=None, verify_ssl=True):
    print(f"Fetching contents of {base_url} (SSL Verification: {verify_ssl})")
    response = requests.get(base_url, verify=verify_ssl)
    if response.status_code != 200:
        print(f"Failed to fetch URL content, status code: {response.status_code}")
        return []

    page_content = response.content
    soup = BeautifulSoup(page_content, 'html.parser')
    links = [a['href'] for a in soup.find_all('a', href=True)]
    print(f"Found {len(links)} links on the page")

    if db_type:
        # Filter the packages based on db_type (exact match, avoiding things like 'pos-aws')
        links = [link for link in links if f"-{db_type}-" in link.split('/')[-1] and not f"-{db_type}-aws-" in link and link.endswith('.zip')]
    else:
        # Just get the zip files or war files if db_type is not needed
        links = [link for link in links if link.endswith('.zip') or link.endswith('.war')]

    print("Filtered packages:")
    for pkg in links:
        print(pkg)

    return links

# Main logic to process the JSON config and download packages
def main():
    parser = argparse.ArgumentParser(description="Download packages based on JSON configuration")
    parser.add_argument('--config', required=True, help="Path to JSON configuration file")
    parser.add_argument('--product_groups', required=True, help="Comma-separated list of product groups to download (e.g., T24, FCM)")
    parser.add_argument('--version', required=True, help="Version to download (e.g., 202409)")
    parser.add_argument('--db_type', required=False, help="Database type (for preimage kits)")
    parser.add_argument('--ignore_ssl', action='store_true', help="Ignore SSL verification")

    args = parser.parse_args()

    # Load the configuration JSON
    with open(args.config, 'r') as f:
        config = json.load(f)

    product_groups = args.product_groups.split(',')
    version = args.version
    db_type = args.db_type
    ignore_ssl = args.ignore_ssl

    for product in config["products"]:
        if product["name"] in product_groups:
            print(f"Processing product: {product['name']}")
            for pkg in product["packages"]:
                # Fixing URL concatenation logic
                package_url = pkg["base_url"] + pkg["path"].replace("{{version}}", version)
                download_dir = config["download_dir"]

                # Use SSL verification or not based on the flag
                verify_ssl = not ignore_ssl

                # If the package has credentials, download using them
                if pkg.get("credentials_required", False):
                    print(f"Downloading with credentials: {pkg['jenkins_credentials_id']}")
                    # Add logic to pull credentials if needed (handled externally via Jenkins)
                    try:
                        download_package(package_url, download_dir, verify_ssl=verify_ssl)
                    except Exception as e:
                        print(f"Failed to download {pkg['package_name']} from {package_url}: {e}")
                else:
                    # If it's a preimage kit or any other package without credentials
                    if pkg.get("db_filter", False) and db_type:
                        package_links = fetch_and_filter_packages(package_url, db_type=db_type, verify_ssl=verify_ssl)
                    else:
                        package_links = fetch_and_filter_packages(package_url, verify_ssl=verify_ssl)

                    # Download the filtered packages
                    if package_links:
                        for link in package_links:
                            # Ensure we don't prepend the base URL twice
                            if link.startswith('http'):
                                full_url = link
                            else:
                                full_url = package_url + link
                            try:
                                download_package(full_url, download_dir, verify_ssl=verify_ssl)
                            except Exception as e:
                                print(f"Failed to download {link} from {package_url}: {e}")

if __name__ == "__main__":
    main()
