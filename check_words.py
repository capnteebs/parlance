from database import ThesaurusDB

words = ['cool', 'lit', 'fire', 'cap', 'dope', 'sick', 'hot']

with ThesaurusDB() as db:
    for word in words:
        cursor = db.execute("SELECT id FROM words WHERE word = ? AND language_code = 'en'", (word,))
        result = cursor.fetchone()
        if result:
            print(f"{word}: EXISTS (id={result[0]})")
        else:
            print(f"{word}: MISSING")
