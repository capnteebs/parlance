"""Check what UD definitions were added"""
from database import ThesaurusDB

with ThesaurusDB() as db:
    # Check for recently added slang senses
    cursor = db.execute("""
        SELECT w.word, s.definition, s.pos
        FROM senses s
        JOIN words w ON s.word_id = w.id
        WHERE s.pos = 'slang'
        ORDER BY s.id DESC
        LIMIT 10
    """)

    results = cursor.fetchall()

    if results:
        print("\nRecently added UD senses:")
        print("="*60)
        for row in results:
            word, definition, pos = row
            print(f"\n{word} ({pos}):")
            print(f"  {definition[:80]}...")
    else:
        print("No UD senses found yet")
