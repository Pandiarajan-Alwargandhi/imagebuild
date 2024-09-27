import requests
from bs4 import BeautifulSoup
import argparse
import os
import json  # Add this import

# Function to download the file
def download_package(url, download_dir):
    local_filename = os.path.join(download_dir, url.split('/')[-1])
    print(f"Downloading {url} to {local_filename}")
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(local_filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
    print(f"Downloaded {local_filename}")

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
    parser = argparse.ArgumentParser(description="Download packages based on a configuration file")
    parser.add_argument('--config', required=True, help="Path to the config JSON file")
    parser.add_argument('--product_groups', required=True, help="Comma-separated product groups to download")
    parser.add_argument('--version', required=True, help="Version of the product")
    parser.add_argument('--db_type', required=True, help="Database type for T24 preimage kit")

    args = parser.parse_args()

    # Load the config JSON
    with open(args.config, 'r') as f:
        config = json.load(f)

    download_dir = config.get("download_dir")
    if not download_dir:
        print("Download directory not specified in config")
        return

    # Get product groups from command-line args
    product_groups = args.product_groups.split(',')

    for product in config["products"]:
        if product["name"] in product_groups:
            print(f"Processing product: {product['name']}")
            for pkg in product["packages"]:
                package_url = pkg["base_url"] + pkg["path"].replace("{{version}}", args.version)

                # If db_filter is true, adjust URL for the database type
                if pkg.get("db_filter", False):
                    print(f"Fetching contents of {package_url}")
                    response = requests.get(package_url)
                    if response.status_code != 200:
                        print(f"Failed to fetch URL content, status code: {response.status_code}")
                        continue
                    page_content = response.content
                    soup = BeautifulSoup(page_content, 'html.parser')
                    links = [a['href'] for a in soup.find_all('a', href=True)]
                    filtered_packages = filter_packages(links, args.db_type)

                    if filtered_packages:
                        latest_package = filtered_packages[-1]
                        if not latest_package.startswith('http'):
                            download_url = package_url + latest_package
                        else:
                            download_url = latest_package

                        download_package(download_url, download_dir)
                    else:
                        print(f"No valid .zip packages found for {args.db_type}")
                else:
                    print(f"Fetching contents of {package_url}")
                    try:
                        if pkg.get("credentials_required", False):
                            # Handle credentials (assumed to be handled in Jenkins or passed externally)
                            print(f"Downloading with credentials: {pkg['jenkins_credentials_id']}")
                            download_package(package_url, download_dir)
                        else:
                            download_package(package_url, download_dir)
                    except Exception as e:
                        print(f"Failed to download {pkg['package_name']} from {package_url}: {e}")

if __name__ == "__main__":
    main()
