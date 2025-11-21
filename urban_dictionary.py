"""
Urban Dictionary Integration for Thesaurus+
Fetches modern slang definitions and links them to existing Wiktionary entries.
"""

import requests
import json
import time
from database import ThesaurusDB
from datetime import datetime

class UrbanDictionaryIntegrator:
    """Integrate Urban Dictionary slang into the thesaurus"""

    def __init__(self, db: ThesaurusDB):
        self.db = db
        self.api_base = "https://api.urbandictionary.com/v0"
        self.session = requests.Session()
        self.ud_source_id = None

    def setup_source(self):
        """Create Urban Dictionary as a data source"""
        cursor = self.db.execute("""
            SELECT id FROM sources WHERE source_name = 'Urban Dictionary'
        """)
        row = cursor.fetchone()

        if row:
            self.ud_source_id = row[0]
        else:
            cursor = self.db.execute("""
                INSERT INTO sources (source_name, extraction_date, notes)
                VALUES (?, ?, ?)
            """, ('Urban Dictionary', datetime.now().date().isoformat(),
                  'Modern slang and internet language'))
            self.ud_source_id = cursor.lastrowid
            self.db.commit()

        print(f"Urban Dictionary source ID: {self.ud_source_id}")

    def fetch_definition(self, word: str):
        """Fetch Urban Dictionary definition for a word"""
        try:
            url = f"{self.api_base}/define"
            params = {'term': word}

            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            return data.get('list', [])

        except Exception as e:
            print(f"Error fetching '{word}': {e}")
            return []

    def clean_definition(self, text: str) -> str:
        """Clean Urban Dictionary definition text"""
        # Remove [brackets] used for internal links
        import re
        text = re.sub(r'\[([^\]]+)\]', r'\1', text)

        # Remove excessive newlines
        text = re.sub(r'\n+', ' ', text)

        # Trim whitespace
        text = text.strip()

        return text

    def is_valid_definition(self, entry: dict) -> bool:
        """Filter out joke/spam definitions"""
        definition = entry.get('definition', '')
        example = entry.get('example', '')
        thumbs_up = entry.get('thumbs_up', 0)
        thumbs_down = entry.get('thumbs_down', 0)

        # Filter criteria
        if len(definition) < 10:  # Too short
            return False

        if len(definition) > 500:  # Too long, probably spam
            return False

        # Check ratio of upvotes to downvotes (only if there are votes)
        if thumbs_up > 0 or thumbs_down > 0:
            if thumbs_down > thumbs_up * 2:  # More than 2x downvotes
                return False

        # Accept entries with 0 votes (likely new/recent entries)
        # Or entries with at least 1 upvote
        return True

    def categorize_slang(self, entry: dict) -> list:
        """Determine what tags to apply to UD entry"""
        definition = entry.get('definition', '').lower()
        example = entry.get('example', '').lower()
        word = entry.get('word', '').lower()

        tags = ['slang']  # All UD is slang

        # Internet/meme slang indicators
        internet_markers = ['internet', 'meme', 'viral', 'online', 'twitter',
                           'tiktok', 'instagram', 'reddit', 'social media']
        if any(marker in definition or marker in example for marker in internet_markers):
            tags.append('internet')

        # Gen Z / modern slang
        gen_z_markers = ['gen z', 'zoomer', 'tiktok', 'no cap', 'fr fr']
        if any(marker in definition or marker in example for marker in gen_z_markers):
            tags.append('modern')

        # AAVE
        aave_markers = ['aave', 'black', 'african american', 'hood']
        if any(marker in definition for marker in aave_markers):
            tags.append('AAVE')

        # Vulgar content
        if entry.get('thumbs_up', 0) > 100 and any(word in definition for word in ['sex', 'fuck', 'shit']):
            tags.append('vulgar')

        return tags

    def integrate_word(self, word: str):
        """Fetch UD definitions for a word and integrate into database"""
        # Check if word exists in our database
        cursor = self.db.execute("""
            SELECT id FROM words WHERE word = ? AND language_code = 'en'
        """, (word,))

        word_row = cursor.fetchone()
        if not word_row:
            return None  # Word not in our database

        word_id = word_row[0]

        # Fetch from Urban Dictionary
        entries = self.fetch_definition(word)

        if not entries:
            return None

        # Filter and process entries
        valid_entries = [e for e in entries if self.is_valid_definition(e)]

        if not valid_entries:
            return None

        # Take top entries by upvotes
        valid_entries.sort(key=lambda x: x.get('thumbs_up', 0), reverse=True)
        valid_entries = valid_entries[:3]  # Top 3 definitions

        added_senses = 0

        for entry in valid_entries:
            # Clean definition
            definition = self.clean_definition(entry.get('definition', ''))
            example = self.clean_definition(entry.get('example', ''))

            # Check if this definition already exists
            cursor = self.db.execute("""
                SELECT id FROM senses
                WHERE word_id = ? AND definition = ?
                LIMIT 1
            """, (word_id, definition))

            if cursor.fetchone():
                continue  # Already exists

            # Add as new sense
            sense_id = self.db.insert_sense(
                word_id=word_id,
                definition=definition,
                pos='slang',  # Mark as slang
                sense_index=999  # Put UD senses at end
            )

            # Add example
            if example:
                self.db.insert_example(sense_id, example, 'Urban Dictionary')

            # Add tags
            tags = self.categorize_slang(entry)
            for tag_name in tags:
                # Get or create tag
                cursor = self.db.execute("SELECT id FROM tags WHERE tag_name = ?", (tag_name,))
                row = cursor.fetchone()

                if row:
                    tag_id = row[0]
                else:
                    tag_id = self.db.insert_tag(tag_name, 'slang')

                self.db.link_sense_tag(sense_id, tag_id)

            # Link to source
            self.db.execute("""
                INSERT OR IGNORE INTO sense_sources (sense_id, source_id)
                VALUES (?, ?)
            """, (sense_id, self.ud_source_id))

            added_senses += 1

        if added_senses > 0:
            self.db.commit()

        return added_senses

    def integrate_existing_words(self, limit: int = 100, focus_words: list = None):
        """
        Integrate UD definitions for words already in our database.

        Args:
            limit: Maximum number of words to process
            focus_words: Specific words to prioritize (slang-heavy words)
        """
        print(f"\n{'='*70}")
        print(" URBAN DICTIONARY INTEGRATION")
        print(f"{'='*70}\n")

        self.setup_source()

        # Get words to process
        if focus_words:
            words = focus_words[:limit]
        else:
            # Get words that likely have slang meanings
            # Prioritize shorter, common words
            cursor = self.db.execute("""
                SELECT DISTINCT w.word
                FROM words w
                WHERE LENGTH(w.word) BETWEEN 3 AND 10
                AND w.language_code = 'en'
                ORDER BY RANDOM()
                LIMIT ?
            """, (limit,))
            words = [row[0] for row in cursor.fetchall()]

        print(f"Processing {len(words)} words from Urban Dictionary...")
        print("(This will take a few minutes due to API rate limiting)\n")

        total_added = 0
        successful_words = []

        for i, word in enumerate(words, 1):
            print(f"[{i}/{len(words)}] Fetching '{word}'...", end=' ')

            added = self.integrate_word(word)

            if added:
                total_added += added
                successful_words.append(word)
                print(f"[OK] Added {added} definitions")
            else:
                print("[SKIP] No valid definitions")

            # Rate limiting - be nice to the API
            time.sleep(1)  # 1 second between requests

        print(f"\n{'='*70}")
        print(" INTEGRATION COMPLETE")
        print(f"{'='*70}")
        print(f"Words processed: {len(words)}")
        print(f"Words with UD definitions: {len(successful_words)}")
        print(f"Total UD senses added: {total_added}")

        if successful_words:
            print(f"\nExample words with UD definitions:")
            print(f"  {', '.join(successful_words[:10])}")


def main():
    """Main integration workflow"""
    import sys

    # Define slang-heavy words to prioritize
    priority_words = [
        'cool', 'hot', 'sick', 'fire', 'lit', 'dope', 'flex', 'cap',
        'vibe', 'mood', 'slay', 'stan', 'ghost', 'shade', 'tea',
        'savage', 'basic', 'extra', 'salty', 'woke', 'sus', 'bet',
        'fam', 'squad', 'lowkey', 'highkey', 'yeet', 'simp', 'karen',
        'boomer', 'zoomer', 'clout', 'drip', 'bussin', 'sheesh',
        'bop', 'slaps', 'vibe', 'mid', 'ratio', 'based', 'cringe'
    ]

    # Get limit from args
    limit = 50
    if len(sys.argv) > 1:
        limit = int(sys.argv[1])

    print("\nUrban Dictionary Integration")
    print(f"Will process up to {limit} words")
    print("\nThis adds modern slang definitions to existing words.\n")

    with ThesaurusDB() as db:
        integrator = UrbanDictionaryIntegrator(db)
        integrator.integrate_existing_words(
            limit=limit,
            focus_words=priority_words
        )

    print("\n[OK] Urban Dictionary integration complete!")
    print("\nTest with:")
    print("  python thesaurus.py fire")
    print("  python thesaurus.py cap")
    print("  python search.py lit")


if __name__ == "__main__":
    main()
