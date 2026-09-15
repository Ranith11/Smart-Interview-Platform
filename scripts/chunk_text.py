from pathlib import Path
import argparse
import json

import tiktoken
from langchain_text_splitters import RecursiveCharacterTextSplitter


# --------------------------------------------------
# Parse command-line arguments
# --------------------------------------------------

parser = argparse.ArgumentParser(
    description="Chunk cleaned text into JSON with metadata."
)

parser.add_argument(
    "input_file",
    help="Path to the cleaned text file."
)

parser.add_argument(
    "--domain",
    required=True,
    help="Knowledge domain (e.g., dsa, dbms, os)."
)

parser.add_argument(
    "--source",
    required=True,
    help="Source name (e.g., tech-interview-handbook)."
)

parser.add_argument(
    "--source-url",
    required=True,
    help="URL of the source page."
)

args = parser.parse_args()


# --------------------------------------------------
# Input file
# --------------------------------------------------

input_file = Path(args.input_file)

if not input_file.exists():
    print("Input file not found:")
    print(input_file)
    raise SystemExit(1)


# --------------------------------------------------
# Derive concept name from filename
# --------------------------------------------------

concept = input_file.stem

if concept.endswith("_clean"):
    concept = concept[:-6]


# --------------------------------------------------
# Create output path
# --------------------------------------------------

parts = input_file.parts

if "raw" in parts:

    raw_index = parts.index("raw")

    relative_parts = parts[raw_index + 1:-1]

    if relative_parts:
        output_folder = (
            Path("data")
            / "processed"
            / Path(*relative_parts)
        )
    else:
        output_folder = Path("data") / "processed"

else:

    output_folder = Path("data") / "processed"


output_folder.mkdir(
    parents=True,
    exist_ok=True
)

output_file = output_folder / f"{concept}_chunks.json"


# --------------------------------------------------
# Read cleaned text
# --------------------------------------------------

text = input_file.read_text(
    encoding="utf-8"
).strip()

if not text:
    print("Input file is empty.")
    raise SystemExit(1)


# --------------------------------------------------
# Create text splitter
# --------------------------------------------------

splitter = RecursiveCharacterTextSplitter(
    chunk_size=1024,
    chunk_overlap=200,
    separators=[
        "\n\n",
        "\n",
        ". ",
        " ",
        ""
    ]
)


# --------------------------------------------------
# Create initial chunks
# --------------------------------------------------

raw_chunks = splitter.split_text(text)


# --------------------------------------------------
# Tokenizer
# --------------------------------------------------

tokenizer = tiktoken.get_encoding("cl100k_base")


# --------------------------------------------------
# Quality filtering
#
# Project requirement:
# Minimum = 50 tokens
# Maximum = 400 tokens
# --------------------------------------------------

MIN_TOKENS = 50
MAX_TOKENS = 400


valid_chunks = []
discarded_chunks = []


for chunk in raw_chunks:

    chunk = chunk.strip()

    if not chunk:
        continue

    token_count = len(
        tokenizer.encode(chunk)
    )

    if MIN_TOKENS <= token_count <= MAX_TOKENS:

        valid_chunks.append({
            "text": chunk,
            "token_count": token_count
        })

    else:

        discarded_chunks.append({
            "text": chunk,
            "token_count": token_count
        })


# --------------------------------------------------
# Create final JSON records with metadata
# --------------------------------------------------

domain = args.domain
source = args.source
source_url = args.source_url

chunk_data = []

for index, chunk in enumerate(
    valid_chunks,
    start=1
):

    chunk_data.append({
        "chunk_id": f"{domain}_{concept}_{index:03d}",
        "domain": domain,
        "concept": concept,
        "source": source,
        "source_url": source_url,
        "text": chunk["text"],
        "token_count": chunk["token_count"]
    })


# --------------------------------------------------
# Save final chunks
# --------------------------------------------------

with output_file.open(
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        chunk_data,
        file,
        indent=2,
        ensure_ascii=False
    )


# --------------------------------------------------
# Statistics
# --------------------------------------------------

print()
print("========================================")
print("       CHUNKING + QUALITY FILTER")
print("========================================")
print()

print("Input:", input_file)
print("Output:", output_file)
print("Domain:", domain)
print("Concept:", concept)
print("Source:", source)
print()

print("Initial chunks:", len(raw_chunks))
print("Valid chunks:", len(valid_chunks))
print("Discarded chunks:", len(discarded_chunks))
print()

print("Minimum tokens:", MIN_TOKENS)
print("Maximum tokens:", MAX_TOKENS)
print()

if valid_chunks:

    token_counts = [
        chunk["token_count"]
        for chunk in valid_chunks
    ]

    print(
        "Smallest valid chunk:",
        min(token_counts),
        "tokens"
    )

    print(
        "Largest valid chunk:",
        max(token_counts),
        "tokens"
    )

    print(
        "Average valid chunk:",
        round(
            sum(token_counts) / len(token_counts),
            2
        ),
        "tokens"
    )

else:

    print("WARNING: No chunks passed the quality filter.")