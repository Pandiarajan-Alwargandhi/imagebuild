import requests
from bs4 import BeautifulSoup
import argparse
import os

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
    parser = argparse.ArgumentParser(description="Download the latest package for a given database type")
    parser.add_argument('--url', required=True, help="URL to fetch the package list from")
    parser.add_argument('--dir', required=True, help="Directory to download the package to")
    parser.add_argument('--db_type', required=True, help="Database type (e.g., pos, h2d, etc.)")

    args = parser.parse_args()

    print(f"Fetching contents of {args.url}")

    # Fetch the page contents
    response = requests.get(args.url)
    if response.status_code != 200:
        print(f"Failed to fetch URL content, status code: {response.status_code}")
        return
    page_content = response.content

    # Parse the HTML
    soup = BeautifulSoup(page_content, 'html.parser')
    links = [a['href'] for a in soup.find_all('a', href=True)]
    print(f"Found {len(links)} links on the page")

    # Filter the packages for the given database type and exclude non-zip files
    filtered_packages = filter_packages(links, args.db_type)
    print("Filtered packages:")
    for pkg in filtered_packages:
        print(pkg)

    # If there are any packages, download the latest `.zip` one
    if filtered_packages:
        latest_package = filtered_packages[-1]  # Get the last `.zip` package in the filtered list

        # Ensure the link is absolute
        if not latest_package.startswith('http'):
            download_url = args.url + latest_package
        else:
            download_url = latest_package

        download_package(download_url, args.dir)
    else:
        print(f"No valid .zip packages found for {args.db_type}")

if __name__ == "__main__":
    main()
