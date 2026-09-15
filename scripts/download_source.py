import requests
from pathlib import Path
import argparse
import sys


# --------------------------------------------------
# Check command-line arguments
# --------------------------------------------------

parser = argparse.ArgumentParser(description="Download a source page and save it as HTML.")
parser.add_argument("concept", help="The concept name (e.g., array, acid-properties)")
parser.add_argument("url", help="The URL to download")
parser.add_argument("--domain", default="dsa", help="The knowledge domain (e.g., dsa, dbms, os)")

args = parser.parse_args()
concept = args.concept
url = args.url
domain = args.domain

# --------------------------------------------------
# Output path
# --------------------------------------------------

output_folder = Path(f"data/raw/{domain}")
output_folder.mkdir(parents=True, exist_ok=True)

output_file = output_folder / f"{concept}.html"


# --------------------------------------------------
# Download
# --------------------------------------------------

print(f"Downloading: {concept} in domain: {domain}")
print(f"URL: {url}")
print()

response = requests.get(
    url,
    headers={
        "User-Agent": "Mozilla/5.0"
    },
    timeout=30
)

response.raise_for_status()

output_file.write_text(
    response.text,
    encoding="utf-8"
)

print("Downloaded successfully.")
print("Saved to:", output_file)
print("Status code:", response.status_code)
