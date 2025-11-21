"""
Build synonym relationships from Wiktextract data.
Second pass: now that words/senses are in DB, link synonyms together.
"""

import json
from database import ThesaurusDB
from typing import List, Dict, Tuple, Optional
from pathlib import Path

class SynonymBuilder:
    """Build synonym relationships between word senses"""

    def __init__(self, db: ThesaurusDB):
        self.db = db
        self.word_sense_cache = {}  # (word, pos) -> [sense_ids]
        self.relationships_created = 0
        self.synonyms_not_found = set()

    def load_sense_cache(self):
        """Pre-load all (word, pos) -> sense_ids mappings"""
        print("Loading word/sense cache...")
        cursor = self.db.execute("""
            SELECT w.word, s.pos, s.id
            FROM words w
            JOIN senses s ON w.id = s.word_id
        """)

        for row in cursor.fetchall():
            word = row[0].lower()
            pos = row[1] or 'unknown'
            sense_id = row[2]

            key = (word, pos)
            if key not in self.word_sense_cache:
                self.word_sense_cache[key] = []
            self.word_sense_cache[key].append(sense_id)

        print(f"  Cached {len(self.word_sense_cache)} (word, pos) combinations")

    def find_sense_ids(self, word: str, pos: str = None) -> List[int]:
        """Find all sense IDs for a word, optionally filtered by POS"""
        word_lower = word.lower()

        if pos:
            key = (word_lower, pos)
            return self.word_sense_cache.get(key, [])
        else:
            # Search all POS for this word
            results = []
            for (w, p), sense_ids in self.word_sense_cache.items():
                if w == word_lower:
                    results.extend(sense_ids)
            return results

    def process_entry_synonyms(self, entry: Dict) -> int:
        """Process synonyms for a single Wiktextract entry"""
        word_text = entry.get('word', '')
        pos = entry.get('pos', None)
        lang_code = entry.get('lang_code', 'en')

        # Only English
        if lang_code != 'en':
            return 0

        # Get source sense IDs for this word
        source_sense_ids = self.find_sense_ids(word_text, pos)
        if not source_sense_ids:
            return 0

        links_created = 0

        # Process each sense
        senses = entry.get('senses', [])
        for sense_index, sense_data in enumerate(senses):
            # Get synonyms from this sense
            synonyms = sense_data.get('synonyms', [])
            if not synonyms:
                continue

            # Use the corresponding source sense (by index)
            # If we have fewer sense_ids than senses in JSON, use the first one
            if sense_index < len(source_sense_ids):
                source_sense_id = source_sense_ids[sense_index]
            else:
                source_sense_id = source_sense_ids[0]

            # Process each synonym
            for syn in synonyms:
                syn_word = None
                syn_tags = []

                if isinstance(syn, dict):
                    syn_word = syn.get('word', '')
                    syn_tags = syn.get('tags', [])
                elif isinstance(syn, str):
                    syn_word = syn
                else:
                    continue

                if not syn_word:
                    continue

                # Find target sense IDs for synonym
                # Try to match by POS first, then fall back to any POS
                target_sense_ids = self.find_sense_ids(syn_word, pos)
                if not target_sense_ids:
                    target_sense_ids = self.find_sense_ids(syn_word)

                if not target_sense_ids:
                    self.synonyms_not_found.add(syn_word)
                    continue

                # Create relationships to all matching senses
                # In reality, we should match by definition similarity too
                # For now, link to all senses with matching POS
                for target_sense_id in target_sense_ids[:3]:  # Limit to first 3
                    # Calculate similarity score
                    # Direct Wiktionary synonym = high similarity
                    similarity = self._calculate_similarity(syn_tags)

                    # Create bidirectional relationship
                    self._create_relationship(source_sense_id, target_sense_id, similarity)
                    links_created += 1

        return links_created

    def _calculate_similarity(self, tags: List[str]) -> float:
        """
        Calculate similarity score based on synonym tags.

        Direct synonyms from Wiktionary are high quality (0.85-0.95)
        Tagged synonyms might be contextual (0.7-0.85)
        """
        # Base score for Wiktionary synonyms
        score = 0.90

        # Adjust based on tags
        if tags:
            # If it has qualifiers, it might be more contextual
            if any(t in tags for t in ['rare', 'archaic', 'obsolete']):
                score -= 0.15
            if any(t in tags for t in ['informal', 'slang']):
                score -= 0.05
            if any(t in tags for t in ['figuratively']):
                score -= 0.10

        return max(0.5, min(1.0, score))

    def _create_relationship(self, source_id: int, target_id: int, similarity: float):
        """Create a synonym relationship"""
        # Avoid self-links
        if source_id == target_id:
            return

        # Check if relationship already exists
        cursor = self.db.execute("""
            SELECT id FROM relationships
            WHERE source_sense_id = ? AND target_sense_id = ?
            AND relationship_type = 'synonym'
        """, (source_id, target_id))

        if cursor.fetchone():
            return  # Already exists

        # Create relationship
        self.db.insert_relationship(source_id, target_id, 'synonym', similarity)
        self.relationships_created += 1

    def build_from_file(self, filepath: str, max_entries: int = None):
        """Build synonym relationships from Wiktextract file"""
        if not Path(filepath).exists():
            print(f"Error: File not found: {filepath}")
            return

        print(f"Building synonym relationships from: {filepath}\n")

        # Load cache
        self.load_sense_cache()

        entries_processed = 0
        entries_with_synonyms = 0

        print("\nProcessing synonyms...")

        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                if max_entries and entries_processed >= max_entries:
                    break

                try:
                    entry = json.loads(line)

                    # Only process if entry has synonyms
                    has_synonyms = False
                    for sense in entry.get('senses', []):
                        if sense.get('synonyms'):
                            has_synonyms = True
                            break

                    if has_synonyms:
                        links = self.process_entry_synonyms(entry)
                        if links > 0:
                            entries_with_synonyms += 1

                    # Commit in batches
                    if entries_processed % 100 == 0:
                        self.db.commit()

                    if entries_processed % 1000 == 0 and entries_processed > 0:
                        print(f"  Processed {entries_processed:,} entries, "
                              f"created {self.relationships_created:,} links")

                except Exception as e:
                    print(f"Error processing entry: {e}")

                entries_processed += 1

        # Final commit
        self.db.commit()

        print(f"\n{'='*70}")
        print(" SYNONYM BUILDING COMPLETE")
        print(f"{'='*70}")
        print(f"Entries processed: {entries_processed:,}")
        print(f"Entries with synonyms: {entries_with_synonyms:,}")
        print(f"Relationships created: {self.relationships_created:,}")
        print(f"Synonyms not found in DB: {len(self.synonyms_not_found)}")

        # Show some not-found examples
        if self.synonyms_not_found:
            examples = list(self.synonyms_not_found)[:20]
            print(f"\nExample synonyms not in database:")
            print(f"  {', '.join(examples)}")
            print(f"  (These words weren't in our dataset)")


def main():
    """Main synonym building function"""
    import sys

    # Get filename from args or use default
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    else:
        filename = "wiktionary_large.jsonl"

    max_entries = None
    if len(sys.argv) > 2:
        max_entries = int(sys.argv[2])

    # Build synonyms
    with ThesaurusDB() as db:
        builder = SynonymBuilder(db)
        builder.build_from_file(filename, max_entries)

    print("\n[OK] Synonym relationships built successfully")
    print("\nTest with:")
    print("  python search.py angry")
    print("  python test_synonyms.py angry")


if __name__ == "__main__":
    main()
