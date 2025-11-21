"""
Database management for Thesaurus+
Handles initialization, queries, and data access
"""

import sqlite3
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime

DB_FILE = "thesaurus.db"

class ThesaurusDB:
    """Main database interface"""

    def __init__(self, db_path: str = DB_FILE):
        self.db_path = db_path
        self.conn = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def connect(self):
        """Open database connection"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row  # Access columns by name
        return self.conn

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

    def execute(self, query: str, params: tuple = ()):
        """Execute a query"""
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        return cursor

    def executemany(self, query: str, params_list: List[tuple]):
        """Execute many queries"""
        cursor = self.conn.cursor()
        cursor.executemany(query, params_list)
        return cursor

    def commit(self):
        """Commit transaction"""
        self.conn.commit()

    # ==================== INITIALIZATION ====================

    def initialize(self, schema_file: str = "schema.sql"):
        """Create all tables from schema file"""
        print(f"Initializing database: {self.db_path}")

        if not Path(schema_file).exists():
            raise FileNotFoundError(f"Schema file not found: {schema_file}")

        with open(schema_file, 'r', encoding='utf-8') as f:
            schema = f.read()

        # Execute schema
        self.conn.executescript(schema)
        self.commit()

        print("[OK] Database initialized successfully")
        self._print_stats()

    def _print_stats(self):
        """Print database statistics"""
        cursor = self.execute("SELECT COUNT(*) FROM words")
        word_count = cursor.fetchone()[0]

        cursor = self.execute("SELECT COUNT(*) FROM senses")
        sense_count = cursor.fetchone()[0]

        cursor = self.execute("SELECT COUNT(*) FROM tags")
        tag_count = cursor.fetchone()[0]

        print(f"\nDatabase stats:")
        print(f"  Words: {word_count}")
        print(f"  Senses: {sense_count}")
        print(f"  Tags: {tag_count}")

    # ==================== INSERT OPERATIONS ====================

    def insert_word(self, word: str, language: str = "English", language_code: str = "en") -> int:
        """Insert a word and return its ID"""
        cursor = self.execute(
            "INSERT OR IGNORE INTO words (word, language, language_code) VALUES (?, ?, ?)",
            (word, language, language_code)
        )

        if cursor.rowcount == 0:
            # Word already exists, get its ID
            cursor = self.execute(
                "SELECT id FROM words WHERE word = ? AND language_code = ?",
                (word, language_code)
            )
            return cursor.fetchone()[0]

        return cursor.lastrowid

    def insert_sense(self, word_id: int, definition: str, pos: str = None,
                     sense_index: int = 1, etymology: str = None) -> int:
        """Insert a word sense and return its ID"""
        cursor = self.execute(
            """INSERT INTO senses (word_id, pos, definition, sense_index, etymology_text)
               VALUES (?, ?, ?, ?, ?)""",
            (word_id, pos, definition, sense_index, etymology)
        )
        return cursor.lastrowid

    def insert_tag(self, tag_name: str, category: str = None, description: str = None) -> int:
        """Insert a tag and return its ID"""
        cursor = self.execute(
            "INSERT OR IGNORE INTO tags (tag_name, category, description) VALUES (?, ?, ?)",
            (tag_name, category, description)
        )

        if cursor.rowcount == 0:
            cursor = self.execute("SELECT id FROM tags WHERE tag_name = ?", (tag_name,))
            return cursor.fetchone()[0]

        return cursor.lastrowid

    def link_sense_tag(self, sense_id: int, tag_id: int):
        """Link a sense to a tag"""
        self.execute(
            "INSERT OR IGNORE INTO sense_tags (sense_id, tag_id) VALUES (?, ?)",
            (sense_id, tag_id)
        )

    def insert_relationship(self, source_sense_id: int, target_sense_id: int,
                           rel_type: str, similarity: float = None):
        """Create a relationship between two senses"""
        self.execute(
            """INSERT INTO relationships
               (source_sense_id, target_sense_id, relationship_type, similarity_score)
               VALUES (?, ?, ?, ?)""",
            (source_sense_id, target_sense_id, rel_type, similarity)
        )

    def insert_example(self, sense_id: int, example_text: str, source: str = None):
        """Add usage example to a sense"""
        self.execute(
            "INSERT INTO examples (sense_id, example_text, source) VALUES (?, ?, ?)",
            (sense_id, example_text, source)
        )

    # ==================== QUERY OPERATIONS ====================

    def search_word(self, word: str) -> List[Dict]:
        """Find all senses of a word"""
        cursor = self.execute(
            """SELECT w.id as word_id, w.word, s.id as sense_id, s.pos, s.definition, s.etymology_text
               FROM words w
               JOIN senses s ON w.id = s.word_id
               WHERE w.word = ?
               ORDER BY s.sense_index""",
            (word,)
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_sense_tags(self, sense_id: int) -> List[str]:
        """Get all tags for a sense"""
        cursor = self.execute(
            """SELECT t.tag_name, t.category
               FROM tags t
               JOIN sense_tags st ON t.id = st.tag_id
               WHERE st.sense_id = ?""",
            (sense_id,)
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_synonyms(self, sense_id: int, min_similarity: float = 0.0) -> List[Dict]:
        """Get synonyms for a sense"""
        cursor = self.execute(
            """SELECT w.word, s.definition, r.similarity_score, s.pos
               FROM relationships r
               JOIN senses s ON r.target_sense_id = s.id
               JOIN words w ON s.word_id = w.id
               WHERE r.source_sense_id = ?
               AND r.relationship_type = 'synonym'
               AND (r.similarity_score >= ? OR r.similarity_score IS NULL)
               ORDER BY r.similarity_score DESC""",
            (sense_id, min_similarity)
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_examples(self, sense_id: int) -> List[str]:
        """Get usage examples for a sense"""
        cursor = self.execute(
            "SELECT example_text FROM examples WHERE sense_id = ?",
            (sense_id,)
        )
        return [row[0] for row in cursor.fetchall()]

    def get_related_phrases(self, sense_id: int) -> List[Dict]:
        """Get phrases/idioms related to this sense"""
        cursor = self.execute(
            """SELECT p.phrase_text, p.definition, p.phrase_type
               FROM phrases p
               JOIN phrase_senses ps ON p.id = ps.phrase_id
               WHERE ps.sense_id = ?
               ORDER BY p.phrase_type, p.phrase_text""",
            (sense_id,)
        )
        return [dict(row) for row in cursor.fetchall()]

    def filter_by_tags(self, sense_id: int, required_tags: List[str]) -> bool:
        """Check if a sense has all required tags"""
        cursor = self.execute(
            """SELECT COUNT(DISTINCT t.tag_name)
               FROM tags t
               JOIN sense_tags st ON t.id = st.tag_id
               WHERE st.sense_id = ?
               AND t.tag_name IN ({})""".format(','.join('?' * len(required_tags))),
            (sense_id, *required_tags)
        )
        count = cursor.fetchone()[0]
        return count == len(required_tags)


def init_database():
    """Initialize a fresh database"""
    # Remove old database if exists
    if Path(DB_FILE).exists():
        print(f"Removing existing database: {DB_FILE}")
        Path(DB_FILE).unlink()

    # Create new database
    with ThesaurusDB() as db:
        db.initialize()

    print(f"\n[OK] Database ready: {DB_FILE}")


if __name__ == "__main__":
    init_database()
