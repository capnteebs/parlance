"""
Import phrases and idioms from Wiktextract into the database
Links phrases to related word senses for discovery
"""
import json
from database import ThesaurusDB
from datetime import datetime

class PhraseImporter:
    """Import and link phrases/idioms to word senses"""

    def __init__(self, db: ThesaurusDB):
        self.db = db
        self.imported_count = 0
        self.linked_count = 0

    def is_phrase(self, entry: dict) -> bool:
        """Check if entry is a multi-word phrase/idiom"""
        word = entry.get('word', '')

        # Multi-word expression
        if ' ' in word:
            return True

        # Tagged as idiomatic
        for sense in entry.get('senses', []):
            if 'idiomatic' in sense.get('tags', []):
                return True

        return False

    def get_phrase_type(self, entry: dict) -> str:
        """Determine phrase type: idiom, proverb, collocation, slang phrase"""
        word = entry.get('word', '')

        # Check tags
        for sense in entry.get('senses', []):
            tags = sense.get('tags', [])

            if 'idiomatic' in tags:
                return 'idiom'
            elif 'proverb' in tags:
                return 'proverb'

        # Check POS for collocations
        pos = entry.get('pos', '')
        if pos in ['noun', 'verb', 'adj'] and ' ' in word:
            return 'collocation'

        return 'phrase'

    def extract_component_words(self, phrase: str) -> list:
        """Extract meaningful words from phrase for linking"""
        # Remove punctuation and split
        import re
        words = re.findall(r'\b\w+\b', phrase.lower())

        # Filter out common stop words
        stop_words = {'a', 'an', 'the', 'and', 'or', 'but', 'of', 'to', 'in',
                     'on', 'at', 'by', 'for', 'with', 'from', 'as', 'is', 'was'}

        meaningful_words = [w for w in words if w not in stop_words and len(w) > 2]
        return meaningful_words

    def import_phrase(self, entry: dict) -> int:
        """Import a phrase and link it to related word senses"""
        phrase_text = entry.get('word', '')
        pos = entry.get('pos', '')

        # Get definition
        senses = entry.get('senses', [])
        if not senses:
            return 0

        first_sense = senses[0]
        glosses = first_sense.get('glosses', [])
        if not glosses:
            return 0

        definition = glosses[0]

        # Determine phrase type
        phrase_type = self.get_phrase_type(entry)

        # Check if phrase already exists
        cursor = self.db.execute(
            "SELECT id FROM phrases WHERE phrase_text = ?",
            (phrase_text,)
        )
        existing = cursor.fetchone()

        if existing:
            phrase_id = existing[0]
        else:
            # Insert phrase
            cursor = self.db.execute("""
                INSERT INTO phrases (phrase_text, definition, phrase_type)
                VALUES (?, ?, ?)
            """, (phrase_text, definition, phrase_type))
            phrase_id = cursor.lastrowid
            self.imported_count += 1

        # Link to component word senses
        component_words = self.extract_component_words(phrase_text)

        for word in component_words:
            # Find word in database
            cursor = self.db.execute("""
                SELECT id FROM words WHERE word = ? AND language_code = 'en'
            """, (word,))

            word_row = cursor.fetchone()
            if not word_row:
                continue

            word_id = word_row[0]

            # Get senses for this word
            cursor = self.db.execute("""
                SELECT id FROM senses WHERE word_id = ? LIMIT 5
            """, (word_id,))

            sense_rows = cursor.fetchall()

            # Link phrase to first few senses of each component word
            for sense_row in sense_rows[:2]:  # Link to top 2 senses
                sense_id = sense_row[0]

                # Check if link already exists
                cursor = self.db.execute("""
                    SELECT 1 FROM phrase_senses
                    WHERE phrase_id = ? AND sense_id = ?
                """, (phrase_id, sense_id))

                if not cursor.fetchone():
                    # Create link
                    self.db.execute("""
                        INSERT INTO phrase_senses (phrase_id, sense_id, relationship_type)
                        VALUES (?, ?, 'contains')
                    """, (phrase_id, sense_id))
                    self.linked_count += 1

        return phrase_id

    def import_from_wiktextract(self, filename: str = 'wiktionary_large.jsonl', limit: int = 1000):
        """Import phrases from Wiktextract JSONL file"""
        print("\n" + "="*70)
        print(" PHRASE/IDIOM IMPORT")
        print("="*70 + "\n")

        print(f"Reading from: {filename}")
        print(f"Limit: {limit} phrases\n")

        processed = 0
        phrase_count = 0

        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    entry = json.loads(line)

                    # Check if this is a phrase/idiom
                    if self.is_phrase(entry):
                        phrase_count += 1

                        if phrase_count <= limit:
                            phrase_id = self.import_phrase(entry)

                            if phrase_id and phrase_count % 50 == 0:
                                print(f"  Imported {self.imported_count} phrases, created {self.linked_count} links...")
                                self.db.commit()

                        if phrase_count >= limit:
                            break

                    processed += 1

                except Exception as e:
                    continue

        self.db.commit()

        print("\n" + "="*70)
        print(" IMPORT COMPLETE")
        print("="*70)
        print(f"Entries processed: {processed}")
        print(f"Phrases found: {phrase_count}")
        print(f"Phrases imported: {self.imported_count}")
        print(f"Sense links created: {self.linked_count}")

        # Show examples
        cursor = self.db.execute("""
            SELECT phrase_text, definition, phrase_type
            FROM phrases
            ORDER BY id DESC
            LIMIT 10
        """)

        print("\nExample phrases imported:")
        for row in cursor.fetchall():
            phrase_text, definition, phrase_type = row
            print(f"  [{phrase_type}] {phrase_text}")
            print(f"    {definition[:70]}...")


def main():
    """Main import workflow"""
    import sys

    # Get limit from command line
    limit = 500
    if len(sys.argv) > 1:
        limit = int(sys.argv[1])

    print("\nPhrase & Idiom Importer")
    print(f"Will import up to {limit} phrases/idioms\n")

    with ThesaurusDB() as db:
        importer = PhraseImporter(db)
        importer.import_from_wiktextract(limit=limit)

    print("\n[OK] Import complete!")
    print("\nTest with:")
    print("  python app.py")
    print("  Search for 'rain' to see 'rain cats and dogs'")


if __name__ == "__main__":
    main()
