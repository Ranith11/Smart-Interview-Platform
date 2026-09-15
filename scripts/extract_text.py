from pathlib import Path
from bs4 import BeautifulSoup
import sys


import argparse

# --------------------------------------------------
# Check command-line argument
# --------------------------------------------------

parser = argparse.ArgumentParser(description="Extract text from HTML.")
parser.add_argument("concept", help="The concept name (e.g., array)")
parser.add_argument("--domain", default="dsa", help="The knowledge domain (e.g., dsa, dbms)")

args = parser.parse_args()
concept = args.concept
domain = args.domain

# --------------------------------------------------
# File paths
# --------------------------------------------------

input_file = Path(f"data/raw/{domain}/{concept}.html")
output_file = Path(f"data/raw/{domain}/{concept}.txt")

if not input_file.exists():
    print("HTML file not found:")
    print(input_file)
    sys.exit(1)


# --------------------------------------------------
# Extract text
# --------------------------------------------------

html = input_file.read_text(encoding="utf-8")

soup = BeautifulSoup(html, "html.parser")

for tag in soup(["script", "style", "nav", "footer"]):
    tag.decompose()

text = soup.get_text(separator="\n", strip=True)

output_file.write_text(text, encoding="utf-8")

print("Text extraction completed.")
print("Saved to:", output_file)
print("Characters extracted:", len(text))