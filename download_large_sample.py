"""
Download a larger sample from Wiktextract for scaling up the database.
"""

import requests
import gzip
import json
from pathlib import Path

DATA_URL = "https://kaikki.org/dictionary/raw-wiktextract-data.jsonl.gz"

def download_large_sample(sample_size=50000, output_file="wiktionary_large.jsonl"):
    """
    Download a larger sample of Wiktextract data.

    Args:
        sample_size: Number of entries to download
        output_file: Where to save the data
    """
    print(f"Downloading {sample_size:,} entries from Wiktextract...")
    print(f"This will take several minutes...\n")

    try:
        # Stream the compressed file
        response = requests.get(DATA_URL, stream=True, timeout=60)
        response.raise_for_status()

        lines_written = 0
        english_entries = 0

        with open(output_file, 'w', encoding='utf-8') as outfile:
            # Decompress on the fly
            with gzip.open(response.raw, 'rt', encoding='utf-8') as gz_file:
                for line in gz_file:
                    # Parse to check if it's English
                    try:
                        entry = json.loads(line)
                        lang_code = entry.get('lang_code', '')

                        # Only save English entries
                        if lang_code == 'en':
                            outfile.write(line)
                            english_entries += 1

                            if english_entries % 1000 == 0:
                                print(f"  Downloaded {english_entries:,} English entries...")

                            if english_entries >= sample_size:
                                break

                    except json.JSONDecodeError:
                        continue

                    lines_written += 1

                    # Safety limit - don't scan forever
                    if lines_written >= sample_size * 3:
                        print(f"\nReached scan limit ({lines_written:,} total entries scanned)")
                        break

        print(f"\n[OK] Downloaded {english_entries:,} English entries")
        print(f"Saved to: {output_file}")
        print(f"File size: {Path(output_file).stat().st_size / 1024 / 1024:.1f} MB")

        return english_entries

    except Exception as e:
        print(f"[ERROR] {e}")
        return 0


def analyze_sample(filename="wiktionary_large.jsonl"):
    """Quick analysis of downloaded data"""
    print(f"\n{'='*70}")
    print(" ANALYZING SAMPLE")
    print(f"{'='*70}\n")

    words = set()
    pos_counts = {}
    has_slang_tag = 0
    has_synonyms = 0
    total = 0

    with open(filename, 'r', encoding='utf-8') as f:
        for line in f:
            entry = json.loads(line)
            total += 1

            word = entry.get('word', '')
            words.add(word.lower())

            pos = entry.get('pos', 'unknown')
            pos_counts[pos] = pos_counts.get(pos, 0) + 1

            # Check for slang
            senses = entry.get('senses', [])
            for sense in senses:
                tags = sense.get('tags', [])
                if 'slang' in tags or 'informal' in tags:
                    has_slang_tag += 1
                    break

            # Check for synonyms
            if entry.get('synonyms'):
                has_synonyms += 1

    print(f"Total entries: {total:,}")
    print(f"Unique words: {len(words):,}")
    print(f"Entries with slang/informal tags: {has_slang_tag:,} ({has_slang_tag/total*100:.1f}%)")
    print(f"Entries with synonyms: {has_synonyms:,} ({has_synonyms/total*100:.1f}%)")

    print(f"\nTop parts of speech:")
    for pos, count in sorted(pos_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {pos:<15} {count:,}")


if __name__ == "__main__":
    import sys

    # Get sample size from command line or use default
    sample_size = 50000
    if len(sys.argv) > 1:
        sample_size = int(sys.argv[1])

    output_file = "wiktionary_large.jsonl"

    # Download
    count = download_large_sample(sample_size, output_file)

    if count > 0:
        # Analyze
        analyze_sample(output_file)

        print(f"\n{'='*70}")
        print(" NEXT STEPS")
        print(f"{'='*70}")
        print(f"\nTo import this data into the database, run:")
        print(f"  python import_wiktextract.py {output_file}")
