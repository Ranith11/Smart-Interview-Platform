from pathlib import Path
import re
import sys


import argparse

# --------------------------------------------------
# Check command-line argument
# --------------------------------------------------

parser = argparse.ArgumentParser(description="Clean extracted text.")
parser.add_argument("concept", help="The concept name (e.g., array)")
parser.add_argument("--domain", default="dsa", help="The knowledge domain (e.g., dsa, dbms)")
parser.add_argument("--source", default="tech-interview-handbook", help="The source name (e.g., tech-interview-handbook, geeksforgeeks)")

args = parser.parse_args()
concept = args.concept
domain = args.domain
source = args.source

# --------------------------------------------------
# File paths
# --------------------------------------------------

input_file = Path(f"data/raw/{domain}/{concept}.txt")
output_file = Path(f"data/raw/{domain}/{concept}_clean.txt")

if not input_file.exists():
    print("Text file not found:")
    print(input_file)
    sys.exit(1)

text = input_file.read_text(encoding="utf-8")


# --------------------------------------------------
# 1. Remove invisible characters
# --------------------------------------------------

text = re.sub(r"[\u200b\u200c\u200d\ufeff]", "", text)


# --------------------------------------------------
# 2. Remove common mojibake / encoding artifacts
# --------------------------------------------------

encoding_artifacts = [
    "ðŸ'‹",
    "ðŸ",
    "â€‹",
    "Â",
]

for artifact in encoding_artifacts:
    text = text.replace(artifact, "")


# --------------------------------------------------
# SOURCE-SPECIFIC CLEANING
# --------------------------------------------------

if source == "tech-interview-handbook":
    # 3. Remove website navigation and promotion
    text = re.sub(
        r".*cheatsheet for coding interviews \| Tech Interview Handbook",
        "",
        text,
        flags=re.DOTALL
    )

    text = re.sub(
        r"Skip to main content.*?cheatsheet for coding interviews",
        "",
        text,
        flags=re.DOTALL
    )

    text = re.sub(
        r"We collaborated with engineers.*?Check out GreatFrontEnd today",
        "",
        text,
        flags=re.DOTALL
    )

    text = text.replace("On this page", "")
    text = text.replace("Tech Interview Handbook", "")

    # 4. Remove author's personal introduction
    text = re.sub(
        r"Hi there, I'm Yangshun.*?interview tips!",
        "",
        text,
        flags=re.DOTALL
    )

    # 5. Remove learning resources section
    text = re.sub(
        r"Learning resources\n.*?"
        r"(?=^(?:"
            r"Common terms|"
            r"Types of |"
            r"Time complexity|"
            r"Things to look out|"
            r"Introduction|"
            r"Implementations|"
            r"Overview|"
            r"Basics|"
            r"Operations|"
            r"Corner cases|"
            r"Techniques|"
            r"Essential questions"
        r"))",
        "",
        text,
        flags=re.DOTALL | re.MULTILINE
    )

    # 6. Remove recommended courses
    text = re.sub(
        r"Recommended courses.*?(?=Table of Contents|$)",
        "",
        text,
        flags=re.DOTALL
    )

    # 7. Remove table of contents
    text = re.sub(
        r"Table of Contents.*$",
        "",
        text,
        flags=re.DOTALL
    )

    # 8. Remove lines containing only symbols
    text = re.sub(
        r"(?m)^\s*[!|]+\s*$",
        "",
        text
    )

elif source == "geeksforgeeks":
    # Remove everything up to and including the "Last Updated :" date
    text = re.sub(
        r"^.*?Last Updated :\n.*?\n",
        "",
        text,
        flags=re.DOTALL
    )

    # Remove the "Comment" or typical footer sections if they exist
    text = re.sub(
        r"\nComment.*$",
        "",
        text,
        flags=re.DOTALL
    )

    # Sometimes there are "Please write comments if you find anything incorrect" type of messages
    text = re.sub(
        r"\nPlease write comments if you find anything incorrect.*$",
        "",
        text,
        flags=re.DOTALL
    )


# --------------------------------------------------
# 9. Remove remaining emoji / non-ASCII symbols
# --------------------------------------------------

# Remove the specific mojibake greeting if still present
text = text.replace("ðŸ'‹", "")

# Remove isolated replacement/unwanted symbols
text = re.sub(
    r"(?m)^\s*[^\w\s\[\]().,:;!?+\-/*=<>\[\]]\s*$",
    "",
    text
)


# --------------------------------------------------
# 10. Normalize whitespace
# --------------------------------------------------

text = re.sub(r"[ \t]+", " ", text)

text = re.sub(r"\n{3,}", "\n\n", text)

text = "\n".join(
    line.strip()
    for line in text.splitlines()
)

text = re.sub(r"\n{3,}", "\n\n", text)

text = text.strip()


# --------------------------------------------------
# Save
# --------------------------------------------------

output_file.write_text(
    text,
    encoding="utf-8"
)

print("Cleaning completed.")
print("Saved to:", output_file)
print("Characters after cleaning:", len(text))