import requests
from pathlib import Path
import sys


# --------------------------------------------------
# Check command-line arguments
# --------------------------------------------------

if len(sys.argv) != 3:
    print("Usage:")
    print("python scripts\\download_dsa_sources.py <concept> <url>")
    print()
    print("Example:")
    print('python scripts\\download_dsa_sources.py array "https://www.techinterviewhandbook.org/algorithms/array/"')
    sys.exit(1)


concept = sys.argv[1]
url = sys.argv[2]


# --------------------------------------------------
# Output path
# --------------------------------------------------

output_folder = Path("data/raw/dsa")
output_folder.mkdir(parents=True, exist_ok=True)

output_file = output_folder / f"{concept}.html"


# --------------------------------------------------
# Download
# --------------------------------------------------

print(f"Downloading: {concept}")
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