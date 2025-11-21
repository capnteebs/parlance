"""
Import Wiktextract data into Thesaurus+ database
Converts JSON entries into normalized database structure
"""

import json
from database import ThesaurusDB
from typing import Dict, List
from pathlib import Path

class WiktextractImporter:
    """Import Wiktextract JSON into database"""

    def __init__(self, db: ThesaurusDB):
        self.db = db
        self.tag_cache = {}  # Cache tag IDs for performance
        self.word_cache = {}  # Cache word IDs
        self.sense_cache = {}  # Map (word, pos, def) -> sense_id for synonym linking

    def load_tag_cache(self):
        """Pre-load all tag IDs"""
        cursor = self.db.execute("SELECT id, tag_name FROM tags")
        self.tag_cache = {row[1]: row[0] for row in cursor.fetchall()}
        print(f"Loaded {len(self.tag_cache)} tags")

    def get_or_create_tag(self, tag_name: str, category: str = None) -> int:
        """Get tag ID, creating if needed"""
        if tag_name in self.tag_cache:
            return self.tag_cache[tag_name]

        tag_id = self.db.insert_tag(tag_name, category)
        self.tag_cache[tag_name] = tag_id
        return tag_id

    def import_entry(self, entry: Dict) -> None:
        """Import a single Wiktextract entry"""
        word_text = entry.get('word', '')
        if not word_text:
            return

        language = entry.get('lang', 'English')
        lang_code = entry.get('lang_code', 'en')

        # Only import English for now
        if lang_code != 'en':
            return

        # Insert word
        word_key = (word_text, lang_code)
        if word_key in self.word_cache:
            word_id = self.word_cache[word_key]
        else:
            word_id = self.db.insert_word(word_text, language, lang_code)
            self.word_cache[word_key] = word_id

        # Get POS and etymology
        pos = entry.get('pos', None)
        etymology = entry.get('etymology_text', None)

        # Process senses
        senses = entry.get('senses', [])
        if not senses:
            return

        for sense_index, sense_data in enumerate(senses, 1):
            self._import_sense(word_id, word_text, pos, sense_data, sense_index, etymology)

    def _import_sense(self, word_id: int, word_text: str, pos: str,
                      sense_data: Dict, sense_index: int, etymology: str) -> None:
        """Import a single word sense"""
        # Get definition
        glosses = sense_data.get('glosses', [])
        if not glosses:
            return

        definition = glosses[0]  # Primary definition

        # Insert sense
        sense_id = self.db.insert_sense(
            word_id=word_id,
            definition=definition,
            pos=pos,
            sense_index=sense_index,
            etymology=etymology
        )

        # Cache this sense for synonym linking
        sense_key = (word_text.lower(), pos, definition[:100])
        self.sense_cache[sense_key] = sense_id

        # Process tags
        tags = sense_data.get('tags', [])
        for tag_name in tags:
            # Categorize tag
            category = self._categorize_tag(tag_name)
            tag_id = self.get_or_create_tag(tag_name, category)
            self.db.link_sense_tag(sense_id, tag_id)

        # Process examples
        examples = sense_data.get('examples', [])
        for example in examples[:5]:  # Limit to 5 examples
            example_text = None
            if isinstance(example, dict):
                example_text = example.get('text', '')
            elif isinstance(example, str):
                example_text = example

            if example_text:
                self.db.insert_example(sense_id, example_text, 'Wiktionary')

        # Process synonyms (create relationships)
        synonyms = sense_data.get('synonyms', [])
        if synonyms:
            self._process_synonyms(sense_id, synonyms)

    def _categorize_tag(self, tag_name: str) -> str:
        """Determine category for a tag"""
        tag_lower = tag_name.lower()

        # Register/tone
        if tag_lower in ['slang', 'informal', 'formal', 'colloquial', 'vulgar', 'poetic']:
            return 'register'

        # Era
        if tag_lower in ['archaic', 'obsolete', 'dated', 'historical']:
            return 'era'

        # Region
        if any(r in tag_lower for r in ['british', 'us', 'american', 'australian', 'canadian', 'aave']):
            return 'region'

        # Grammar
        if tag_lower in ['transitive', 'intransitive', 'countable', 'uncountable', 'plural', 'singular']:
            return 'grammar'

        # Offensive
        if tag_lower in ['offensive', 'derogatory', 'pejorative', 'slur']:
            return 'offensive'

        return 'other'

    def _process_synonyms(self, source_sense_id: int, synonyms: List) -> None:
        """Create synonym relationships"""
        for syn in synonyms:
            if isinstance(syn, dict):
                syn_word = syn.get('word', '')
            elif isinstance(syn, str):
                syn_word = syn
            else:
                continue

            if not syn_word:
                continue

            # Try to find the synonym in our cache
            # For now, just store the word - we'll link properly in a second pass
            # This is a simplified version; full implementation would do multi-pass linking
            pass

    def import_file(self, filepath: str, max_entries: int = None) -> None:
        """Import entries from a JSONL file"""
        if not Path(filepath).exists():
            print(f"Error: File not found: {filepath}")
            return

        print(f"Importing from: {filepath}")
        self.load_tag_cache()

        entries_processed = 0
        entries_imported = 0

        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                if max_entries and entries_processed >= max_entries:
                    break

                try:
                    entry = json.loads(line)
                    self.import_entry(entry)
                    entries_imported += 1

                    if entries_imported % 10 == 0:
                        self.db.commit()  # Commit in batches

                    if entries_imported % 50 == 0:
                        print(f"  Imported {entries_imported} entries...")

                except Exception as e:
                    print(f"Error processing entry: {e}")

                entries_processed += 1

        # Final commit
        self.db.commit()

        print(f"\n[OK] Imported {entries_imported} entries")
        print(f"Total words in database:")
        self.db._print_stats()


def main():
    """Main import function"""
    import sys

    # Get filename from args or use default
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    else:
        filename = "target_words.jsonl"

    max_entries = None
    if len(sys.argv) > 2:
        max_entries = int(sys.argv[2])

    # Import data
    with ThesaurusDB() as db:
        importer = WiktextractImporter(db)
        importer.import_file(filename, max_entries)


if __name__ == "__main__":
    main()
