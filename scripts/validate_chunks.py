from pathlib import Path
import json
import sys


# --------------------------------------------------
# Check command-line argument
# --------------------------------------------------

if len(sys.argv) != 2:
    print("Usage:")
    print("python scripts\\validate_chunks.py <chunks_file>")
    print()
    print("Example:")
    print("python scripts\\validate_chunks.py data\\processed\\dsa\\array_chunks.json")
    sys.exit(1)


# --------------------------------------------------
# Get input file
# --------------------------------------------------

input_file = Path(sys.argv[1])


# --------------------------------------------------
# Check file exists
# --------------------------------------------------

if not input_file.exists():
    print("Chunks file not found:")
    print(input_file)
    sys.exit(1)


# --------------------------------------------------
# Load JSON
# --------------------------------------------------

with input_file.open("r", encoding="utf-8") as file:
    chunks = json.load(file)


if not isinstance(chunks, list):
    print("Invalid format: expected a list of chunks.")
    sys.exit(1)


# --------------------------------------------------
# Validation statistics
# --------------------------------------------------

total_chunks = len(chunks)

empty_chunks = []
very_small_chunks = []
possible_heading_chunks = []

minimum_recommended_length = 100


# --------------------------------------------------
# Inspect every chunk
# --------------------------------------------------

for chunk in chunks:

    chunk_id = chunk.get("chunk_id", "")
    text = chunk.get("text", "")

    text = text.strip()

    # Empty chunk
    if not text:
        empty_chunks.append(chunk_id)
        continue

    # Very small chunk
    if len(text) < minimum_recommended_length:
        very_small_chunks.append({
            "chunk_id": chunk_id,
            "characters": len(text),
            "text": text
        })

    # Possible heading-only chunk
    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    if len(lines) == 1 and len(text) <= 100:
        possible_heading_chunks.append({
            "chunk_id": chunk_id,
            "characters": len(text),
            "text": text
        })


# --------------------------------------------------
# Print report
# --------------------------------------------------

print()
print("========================================")
print("       CHUNK VALIDATION REPORT")
print("========================================")
print()

print("File:", input_file)
print("Total chunks:", total_chunks)
print()


# Empty chunks
print("Empty chunks:", len(empty_chunks))

if empty_chunks:
    print("  IDs:", ", ".join(empty_chunks))

print()


# Very small chunks
print(
    "Chunks below",
    minimum_recommended_length,
    "characters:",
    len(very_small_chunks)
)

for item in very_small_chunks:
    print(
        f"  {item['chunk_id']} "
        f"({item['characters']} chars): "
        f"{item['text']}"
    )

print()


# Heading-like chunks
print(
    "Possible heading-only chunks:",
    len(possible_heading_chunks)
)

for item in possible_heading_chunks:
    print(
        f"  {item['chunk_id']} "
        f"({item['characters']} chars): "
        f"{item['text']}"
    )

print()


# --------------------------------------------------
# Final result
# --------------------------------------------------

if empty_chunks:
    print("RESULT: REVIEW REQUIRED")
    print("Reason: empty chunks were found.")

elif possible_heading_chunks:
    print("RESULT: REVIEW REQUIRED")
    print("Reason: possible heading-only chunks were found.")

else:
    print("RESULT: PASS")
    print("No obvious chunk-quality problems were detected.")

print()