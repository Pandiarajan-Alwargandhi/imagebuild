import os
import requests
from bs4 import BeautifulSoup
import argparse

def download_package(download_url, download_dir):
    local_filename = download_url.split('/')[-1]
    local_filepath = os.path.join(download_dir, local_filename)
    
    print(f"Downloading {download_url} to {local_filepath}")
    with requests.get(download_url, stream=True) as r:
        r.raise_for_status()
        with open(local_filepath, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    print(f"Downloaded {local_filepath}")
    return local_filepath

def fetch_and_filter_packages(url, db_type):
    print(f"Fetching contents of {url}")
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch URL content, status code: {response.status_code}")
    
    soup = BeautifulSoup(response.content, 'html.parser')
    links = soup.find_all('a')
    print(f"Found {len(links)} links on the page")

    # Filter links for the specified db_type, ensuring no db_type variation is included (e.g. pos but not pos-aws)
    filtered_links = []
    for link in links:
        href = link.get('href')
        if href and f"-{db_type}-" in href and href.endswith('.zip'):
            filtered_links.append(href)

    print(f"Filtered packages:")
    for link in filtered_links:
        print(link)

    return filtered_links

def main():
    parser = argparse.ArgumentParser(description="Download latest package from a Maven repository")
    parser.add_argument('--url', required=True, help="Base URL of the Maven repository")
    parser.add_argument('--dir', required=True, help="Directory to download the package to")
    parser.add_argument('--db_type', required=True, help="Database type to filter for (e.g., pos, sql)")

    args = parser.parse_args()

    os.makedirs(args.dir, exist_ok=True)

    packages = fetch_and_filter_packages(args.url, args.db_type)
    if not packages:
        print(f"No valid packages found for {args.db_type}")
        return

    # Sort and download the latest package based on filename (assuming the latest version is the last one)
    latest_package = sorted(packages)[-1]
    full_download_url = args.url + latest_package
    download_package(full_download_url, args.dir)

if __name__ == '__main__':
    main()
