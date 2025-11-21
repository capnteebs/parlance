"""Explore phrase and idiom data in Wiktextract"""
import json

print("Exploring phrases and idioms in Wiktextract data...")
print("="*70)

# Load sample entries
entries = []
with open('wiktionary_large.jsonl', 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if i >= 5000:  # Check first 5000 entries
            break
        try:
            entries.append(json.loads(line))
        except:
            continue

print(f"\nLoaded {len(entries)} entries\n")

# 1. Find entries with "idiom" tag
idiom_entries = []
for entry in entries:
    for sense in entry.get('senses', []):
        tags = sense.get('tags', [])
        if 'idiomatic' in tags or 'idiom' in tags:
            idiom_entries.append({
                'word': entry.get('word'),
                'pos': entry.get('pos'),
                'definition': sense.get('glosses', [''])[0],
                'tags': tags
            })
            break

print(f"Found {len(idiom_entries)} entries with idiom tags")
if idiom_entries:
    print("\nFirst 5 idioms:")
    for i, idiom in enumerate(idiom_entries[:5]):
        print(f"\n{i+1}. '{idiom['word']}' ({idiom['pos']})")
        print(f"   {idiom['definition'][:80]}...")
        print(f"   Tags: {idiom['tags']}")

# 2. Find multi-word entries (phrases)
phrase_entries = []
for entry in entries:
    word = entry.get('word', '')
    if ' ' in word:  # Contains space = phrase
        phrase_entries.append({
            'phrase': word,
            'pos': entry.get('pos'),
            'definition': entry.get('senses', [{}])[0].get('glosses', [''])[0] if entry.get('senses') else '',
            'sense_count': len(entry.get('senses', []))
        })

print(f"\n\nFound {len(phrase_entries)} multi-word phrases")
if phrase_entries:
    print("\nFirst 10 phrases:")
    for i, phrase in enumerate(phrase_entries[:10]):
        print(f"\n{i+1}. '{phrase['phrase']}' ({phrase['pos']})")
        print(f"   {phrase['definition'][:80]}...")

# 3. Find entries with "form_of" (phrasal verbs like "kick off")
form_of_entries = []
for entry in entries:
    for sense in entry.get('senses', []):
        if sense.get('form_of'):
            form_of_entries.append({
                'word': entry.get('word'),
                'form_of': sense.get('form_of'),
                'tags': sense.get('tags', [])
            })
            break

print(f"\n\nFound {len(form_of_entries)} 'form_of' entries (phrasal verbs, etc.)")
if form_of_entries:
    print("\nFirst 5 form_of entries:")
    for i, item in enumerate(form_of_entries[:5]):
        print(f"\n{i+1}. '{item['word']}' -> form_of: {item['form_of']}")

print("\n" + "="*70)
print("Exploration complete!")
