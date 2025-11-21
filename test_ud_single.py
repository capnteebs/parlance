"""Test Urban Dictionary integration for a single word"""
from database import ThesaurusDB
from urban_dictionary import UrbanDictionaryIntegrator

# Test with "cool" which exists in our database
with ThesaurusDB() as db:
    integrator = UrbanDictionaryIntegrator(db)
    integrator.setup_source()

    print("\nTesting Urban Dictionary integration for 'cool'...")
    print("="*60)

    # Fetch UD definitions
    entries = integrator.fetch_definition('cool')
    print(f"\nFetched {len(entries)} entries from UD API")

    if entries:
        print(f"\nFirst entry:")
        print(f"  Definition: {entries[0].get('definition', '')[:100]}...")
        print(f"  Thumbs up: {entries[0].get('thumbs_up', 0)}")
        print(f"  Thumbs down: {entries[0].get('thumbs_down', 0)}")
        print(f"  Valid? {integrator.is_valid_definition(entries[0])}")

    # Try integration
    result = integrator.integrate_word('cool')

    if result:
        print(f"\n[SUCCESS] Added {result} UD senses for 'cool'")
    else:
        print(f"\n[FAILED] No senses added")

        # Debug: check why
        cursor = db.execute("SELECT id FROM words WHERE word = 'cool' AND language_code = 'en'")
        word_row = cursor.fetchone()
        if word_row:
            print(f"  - Word exists (id={word_row[0]})")

            # Check existing senses
            cursor = db.execute("SELECT COUNT(*) FROM senses WHERE word_id = ?", (word_row[0],))
            sense_count = cursor.fetchone()[0]
            print(f"  - Has {sense_count} existing senses")
        else:
            print(f"  - Word NOT in database")
