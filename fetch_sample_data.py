"""
Fetch a small sample from Wiktextract data to explore structure.
Downloads just the first 1000 lines instead of the full 2.3GB file.
"""

import requests
import gzip
import json
from pathlib import Path

# Wiktextract data URL (compressed)
# Try different possible URLs
DATA_URL = "https://kaikki.org/dictionary/raw-wiktextract-data.jsonl.gz"
SAMPLE_SIZE = 1000  # Number of lines to download
OUTPUT_FILE = "wiktionary_sample.jsonl"

def download_sample():
    """Stream download and save first N lines"""
    print(f"Downloading first {SAMPLE_SIZE} lines from Wiktextract...")
    print(f"Source: {DATA_URL}")
    print("This may take a minute...\n")

    try:
        # Stream the compressed file
        response = requests.get(DATA_URL, stream=True)
        response.raise_for_status()

        lines_written = 0

        with open(OUTPUT_FILE, 'w', encoding='utf-8') as outfile:
            # Decompress on the fly
            with gzip.open(response.raw, 'rt', encoding='utf-8') as gz_file:
                for line in gz_file:
                    outfile.write(line)
                    lines_written += 1

                    if lines_written % 100 == 0:
                        print(f"  Downloaded {lines_written} entries...")

                    if lines_written >= SAMPLE_SIZE:
                        break

        print(f"\n[OK] Saved {lines_written} entries to {OUTPUT_FILE}")
        return True

    except Exception as e:
        print(f"[ERROR] Error downloading: {e}")
        return False


def explore_sample():
    """Parse and display some example entries"""
    print(f"\n{'='*60}")
    print("SAMPLE ENTRIES")
    print(f"{'='*60}\n")

    with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if i >= 5:  # Show first 5 entries
                break

            entry = json.loads(line)

            print(f"Entry #{i+1}: {entry.get('word', 'N/A')}")
            print(f"  Language: {entry.get('lang', 'N/A')}")
            print(f"  POS: {entry.get('pos', 'N/A')}")

            # Show senses (definitions)
            senses = entry.get('senses', [])
            if senses:
                print(f"  Definitions:")
                for sense in senses[:2]:  # First 2 definitions
                    glosses = sense.get('glosses', [])
                    if glosses:
                        print(f"    - {glosses[0]}")

                    # Show tags (slang, archaic, etc.)
                    tags = sense.get('tags', [])
                    if tags:
                        print(f"      Tags: {', '.join(tags)}")

            # Show synonyms if present
            synonyms = entry.get('synonyms', [])
            if synonyms:
                syn_words = [s.get('word', '') for s in synonyms[:5]]
                print(f"  Synonyms: {', '.join(syn_words)}")

            print()

    print(f"{'='*60}")
    print(f"Full sample saved to: {OUTPUT_FILE}")
    print(f"Total entries: {SAMPLE_SIZE}")
    print(f"{'='*60}\n")


def find_word(word_to_find):
    """Search sample for a specific word"""
    print(f"\nSearching for '{word_to_find}'...\n")

    with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            entry = json.loads(line)
            if entry.get('word', '').lower() == word_to_find.lower():
                print(json.dumps(entry, indent=2))
                return

    print(f"'{word_to_find}' not found in sample. Try downloading more entries or search the full dataset.")


if __name__ == "__main__":
    # Download sample
    if download_sample():
        # Show examples
        explore_sample()

        # Try to find specific words
        print("\nLooking for interesting examples...")
        for word in ["angry", "hit", "slang"]:
            find_word(word)
