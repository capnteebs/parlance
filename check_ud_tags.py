"""Check tags on UD senses"""
from database import ThesaurusDB

with ThesaurusDB() as db:
    cursor = db.execute("""
        SELECT s.id, w.word, GROUP_CONCAT(t.tag_name, ', ') as tags
        FROM senses s
        JOIN words w ON s.word_id = w.id
        LEFT JOIN sense_tags st ON s.id = st.sense_id
        LEFT JOIN tags t ON st.tag_id = t.id
        WHERE s.pos = 'slang' AND s.id >= 49603
        GROUP BY s.id
        ORDER BY s.id DESC
        LIMIT 10
    """)

    print("\nUrban Dictionary senses and their tags:")
    print("="*70)
    for row in cursor.fetchall():
        sense_id, word, tags = row
        print(f"\nSense {sense_id} - '{word}':")
        print(f"  Tags: {tags if tags else '(no tags)'}")
