"""
Stream through the full Wiktextract data to find specific words.
Doesn't download everything - just searches for what you need.
"""

import requests
import gzip
import json

# Wiktextract data URL
DATA_URL = "https://kaikki.org/dictionary/raw-wiktextract-data.jsonl.gz"

# Words to search for
TARGET_WORDS = [
    "angry",
    "mad",
    "hit",
    "punch",
    "slang",
    "cool",
    "sick",
    "flex",
    "fire",
    "lit"
]

def stream_search_words(target_words, max_entries=50000):
    """
    Stream through compressed data looking for specific words.
    Stops after finding all words or hitting max_entries.
    """
    print(f"Streaming search for {len(target_words)} words...")
    print(f"Searching up to {max_entries} entries...")
    print(f"Words: {', '.join(target_words)}\n")

    # Track what we've found
    found_words = {word.lower(): [] for word in target_words}
    entries_scanned = 0

    try:
        # Stream the compressed file
        response = requests.get(DATA_URL, stream=True, timeout=30)
        response.raise_for_status()

        with gzip.open(response.raw, 'rt', encoding='utf-8') as gz_file:
            for line in gz_file:
                entries_scanned += 1

                if entries_scanned % 5000 == 0:
                    found_count = sum(1 for v in found_words.values() if v)
                    print(f"  Scanned {entries_scanned} entries... Found {found_count}/{len(target_words)} words")

                entry = json.loads(line)
                word = entry.get('word', '').lower()

                # Check if this is one of our target words
                if word in found_words:
                    found_words[word].append(entry)

                # Stop if we found everything or hit max
                if all(found_words.values()) or entries_scanned >= max_entries:
                    break

        # Report results
        print(f"\n{'='*60}")
        print(f"SEARCH COMPLETE - Scanned {entries_scanned} entries")
        print(f"{'='*60}\n")

        for word, entries in found_words.items():
            if entries:
                print(f"[FOUND] '{word}' - {len(entries)} entries")
            else:
                print(f"[MISSING] '{word}' - not found")

        # Save results
        output_file = "target_words.jsonl"
        with open(output_file, 'w', encoding='utf-8') as f:
            for word, entries in found_words.items():
                for entry in entries:
                    f.write(json.dumps(entry) + '\n')

        total_found = sum(len(v) for v in found_words.values())
        print(f"\nSaved {total_found} entries to {output_file}")

        return found_words

    except Exception as e:
        print(f"[ERROR] {e}")
        return None


def display_word_details(word, entries):
    """Display detailed info for a specific word"""
    print(f"\n{'='*60}")
    print(f"WORD: {word.upper()}")
    print(f"{'='*60}\n")

    for i, entry in enumerate(entries, 1):
        pos = entry.get('pos', 'unknown')
        print(f"Entry {i}: {word} ({pos})")

        # Definitions
        senses = entry.get('senses', [])
        if senses:
            print(f"  Definitions:")
            for sense in senses[:3]:  # Show first 3
                glosses = sense.get('glosses', [])
                if glosses:
                    print(f"    - {glosses[0][:100]}")  # Truncate long ones

                # Tags (THIS IS THE GOLD!)
                tags = sense.get('tags', [])
                if tags:
                    print(f"      [Tags: {', '.join(tags)}]")

                # Examples
                examples = sense.get('examples', [])
                if examples:
                    example_text = examples[0].get('text', '') if isinstance(examples[0], dict) else examples[0]
                    print(f"      Example: \"{example_text[:80]}\"")

        # Synonyms
        synonyms = entry.get('synonyms', [])
        if synonyms:
            syn_words = [s.get('word', s) if isinstance(s, dict) else s for s in synonyms[:10]]
            print(f"  Synonyms: {', '.join(str(s) for s in syn_words)}")

        # Etymology
        etymology = entry.get('etymology_text', '')
        if etymology:
            print(f"  Etymology: {etymology[:100]}...")

        print()


if __name__ == "__main__":
    # Search for words
    results = stream_search_words(TARGET_WORDS, max_entries=100000)

    if results:
        # Display details for interesting words
        print("\n" + "="*60)
        print("DETAILED EXAMPLES")
        print("="*60)

        for word in ["angry", "slang", "sick"]:
            if word in results and results[word]:
                display_word_details(word, results[word])
