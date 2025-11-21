"""
Verify data quality and explore slang/informal content
"""

from database import ThesaurusDB

def analyze_slang_content():
    """Analyze slang and informal language coverage"""
    with ThesaurusDB() as db:
        print("="*70)
        print(" SLANG & INFORMAL CONTENT ANALYSIS")
        print("="*70 + "\n")

        # Count slang/informal entries
        cursor = db.execute("""
            SELECT t.tag_name, COUNT(DISTINCT st.sense_id) as sense_count
            FROM tags t
            JOIN sense_tags st ON t.id = st.tag_id
            WHERE t.tag_name IN ('slang', 'informal', 'colloquial', 'vulgar')
            GROUP BY t.tag_name
            ORDER BY sense_count DESC
        """)

        print("Slang/Informal tags:")
        for row in cursor.fetchall():
            print(f"  {row[0]:<15} {row[1]:,} senses")

        # Get some random slang words
        print("\nSample slang words:")
        cursor = db.execute("""
            SELECT DISTINCT w.word, s.definition, s.pos
            FROM words w
            JOIN senses s ON w.id = s.word_id
            JOIN sense_tags st ON s.id = st.sense_id
            JOIN tags t ON st.tag_id = t.id
            WHERE t.tag_name = 'slang'
            LIMIT 20
        """)

        for row in cursor.fetchall():
            word = row[0]
            definition = row[1][:60] + "..." if len(row[1]) > 60 else row[1]
            pos = row[2] or "?"
            try:
                print(f"  {word:<20} ({pos}) - {definition}")
            except UnicodeEncodeError:
                print(f"  {word:<20} ({pos}) - [unicode definition]")


def analyze_regional_tags():
    """Check regional language coverage"""
    with ThesaurusDB() as db:
        print("\n" + "="*70)
        print(" REGIONAL/CULTURAL TAGS")
        print("="*70 + "\n")

        cursor = db.execute("""
            SELECT t.tag_name, COUNT(DISTINCT st.sense_id) as sense_count
            FROM tags t
            JOIN sense_tags st ON t.id = st.tag_id
            WHERE t.category = 'region'
            OR t.tag_name IN ('UK', 'US', 'British', 'American', 'Australian',
                              'AAVE', 'Canadian', 'Irish', 'Scottish')
            GROUP BY t.tag_name
            ORDER BY sense_count DESC
            LIMIT 15
        """)

        print("Regional tags:")
        for row in cursor.fetchall():
            print(f"  {row[0]:<20} {row[1]:,} senses")


def analyze_era_tags():
    """Check temporal language coverage"""
    with ThesaurusDB() as db:
        print("\n" + "="*70)
        print(" ERA/TEMPORAL TAGS")
        print("="*70 + "\n")

        cursor = db.execute("""
            SELECT t.tag_name, COUNT(DISTINCT st.sense_id) as sense_count
            FROM tags t
            JOIN sense_tags st ON t.id = st.tag_id
            WHERE t.category = 'era'
            OR t.tag_name IN ('obsolete', 'archaic', 'dated', 'historical')
            GROUP BY t.tag_name
            ORDER BY sense_count DESC
        """)

        print("Era tags:")
        for row in cursor.fetchall():
            print(f"  {row[0]:<20} {row[1]:,} senses")


def test_lookups():
    """Test looking up some common words"""
    with ThesaurusDB() as db:
        print("\n" + "="*70)
        print(" SAMPLE LOOKUPS")
        print("="*70 + "\n")

        test_words = ['cool', 'hit', 'mad', 'sick', 'dope', 'fire', 'wicked',
                     'awesome', 'bad', 'tight']

        for word in test_words:
            cursor = db.execute("""
                SELECT COUNT(*)
                FROM words w
                WHERE w.word = ?
            """, (word,))

            count = cursor.fetchone()[0]
            if count > 0:
                # Get sense count
                cursor = db.execute("""
                    SELECT COUNT(s.id)
                    FROM words w
                    JOIN senses s ON w.id = s.word_id
                    WHERE w.word = ?
                """, (word,))
                sense_count = cursor.fetchone()[0]

                # Check for slang tag
                cursor = db.execute("""
                    SELECT COUNT(DISTINCT s.id)
                    FROM words w
                    JOIN senses s ON w.id = s.word_id
                    JOIN sense_tags st ON s.id = st.sense_id
                    JOIN tags t ON st.tag_id = t.id
                    WHERE w.word = ? AND t.tag_name = 'slang'
                """, (word,))
                slang_count = cursor.fetchone()[0]

                slang_marker = " [HAS SLANG]" if slang_count > 0 else ""
                print(f"  {word:<15} {sense_count} senses{slang_marker}")
            else:
                print(f"  {word:<15} NOT FOUND")


def check_synonyms():
    """Check synonym data quality"""
    with ThesaurusDB() as db:
        print("\n" + "="*70)
        print(" SYNONYM DATA")
        print("="*70 + "\n")

        # Note: We haven't built synonym relationships yet
        # This will be mostly empty for now
        cursor = db.execute("SELECT COUNT(*) FROM relationships")
        rel_count = cursor.fetchone()[0]

        print(f"Relationship records: {rel_count}")
        print("(Note: Synonym linking not yet implemented)")


def main():
    """Run all verification checks"""
    analyze_slang_content()
    analyze_regional_tags()
    analyze_era_tags()
    test_lookups()
    check_synonyms()

    print("\n" + "="*70)
    print(" VERIFICATION COMPLETE")
    print("="*70)
    print("\nDatabase is ready for:")
    print("  - Synonym relationship building")
    print("  - Semantic similarity scoring")
    print("  - Advanced filtering by tone/region/era")
    print("  - Web interface development")


if __name__ == "__main__":
    main()
