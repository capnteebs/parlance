"""
View details for a specific word from the extracted data.
"""

import json
import sys

def view_word(word_to_find, filename="target_words.jsonl"):
    """Display formatted info for a word"""
    found = False

    with open(filename, 'r', encoding='utf-8') as f:
        for line in f:
            entry = json.loads(line)

            if entry.get('word', '').lower() == word_to_find.lower():
                found = True
                pos = entry.get('pos', 'unknown')

                print(f"\n{'='*60}")
                print(f"{entry['word'].upper()} ({pos})")
                print(f"{'='*60}\n")

                # Senses (definitions)
                senses = entry.get('senses', [])
                if senses:
                    print("DEFINITIONS:")
                    for i, sense in enumerate(senses, 1):
                        glosses = sense.get('glosses', [])
                        if glosses:
                            print(f"  {i}. {glosses[0]}")

                            # Tags - THIS IS KEY!
                            tags = sense.get('tags', [])
                            if tags:
                                print(f"     Tags: [{', '.join(tags)}]")

                            # Examples
                            examples = sense.get('examples', [])
                            if examples:
                                ex_text = examples[0].get('text', examples[0]) if isinstance(examples[0], dict) else str(examples[0])
                                try:
                                    print(f"     Ex: \"{ex_text}\"")
                                except:
                                    pass  # Skip unicode issues

                # Synonyms - CRITICAL DATA
                synonyms = entry.get('synonyms', [])
                if synonyms:
                    print(f"\nSYNONYMS:")
                    for syn in synonyms[:15]:
                        if isinstance(syn, dict):
                            syn_word = syn.get('word', '')
                            syn_tags = syn.get('tags', [])
                            tag_str = f" [{', '.join(syn_tags)}]" if syn_tags else ""
                            print(f"  - {syn_word}{tag_str}")
                        else:
                            print(f"  - {syn}")

                # Etymology
                etymology = entry.get('etymology_text', '')
                if etymology:
                    print(f"\nETYMOLOGY:")
                    print(f"  {etymology[:200]}...")

                # Forms/Derived
                forms = entry.get('forms', [])
                if forms:
                    print(f"\nFORMS:")
                    for form in forms[:5]:
                        if isinstance(form, dict):
                            form_word = form.get('word', '')
                            form_tags = form.get('tags', [])
                            print(f"  - {form_word} [{', '.join(form_tags)}]")

                print()

    if not found:
        print(f"'{word_to_find}' not found in data file.")


if __name__ == "__main__":
    # Check which words we have
    print("Available words in dataset:")
    words_found = set()
    with open("target_words.jsonl", 'r', encoding='utf-8') as f:
        for line in f:
            entry = json.loads(line)
            words_found.add(entry.get('word', '').lower())

    print(f"  {', '.join(sorted(words_found))}\n")

    # View specific words
    for word in ["angry", "cool", "slang"]:
        view_word(word)
