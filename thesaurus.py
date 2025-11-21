"""
Main Thesaurus+ interface - search words and get synonyms by tone/register
This is the core user-facing tool
"""

from database import ThesaurusDB
import sys

def search_thesaurus(word: str, filter_tags: list = None, min_similarity: float = 0.5):
    """
    Main thesaurus search - shows word definitions and synonyms
    """
    with ThesaurusDB() as db:
        senses = db.search_word(word)

        if not senses:
            print(f"\n'{word}' not found in database.")
            print("\nTry:")
            print("  - Check spelling")
            print("  - Try a simpler form (e.g., 'run' instead of 'running')")
            return

        print(f"\n{'='*70}")
        print(f" {word.upper()}")
        print(f"{'='*70}\n")

        # Group by POS
        by_pos = {}
        for sense in senses:
            pos = sense['pos'] or 'unknown'
            if pos not in by_pos:
                by_pos[pos] = []
            by_pos[pos].append(sense)

        # Display each POS
        for pos, pos_senses in by_pos.items():
            print(f"--- {pos.upper()} ---\n")

            for i, sense in enumerate(pos_senses, 1):
                sense_id = sense['sense_id']

                # Definition
                print(f"{i}. {sense['definition']}")

                # Tags
                tags = db.get_sense_tags(sense_id)
                if tags:
                    tag_list = []
                    for tag in tags:
                        tag_name = tag['tag_name']
                        category = tag.get('category', '')
                        if category and category not in ['grammar', 'other']:
                            tag_list.append(f"{tag_name}")

                    if tag_list:
                        print(f"   Tags: {', '.join(tag_list)}")

                # Examples
                examples = db.get_examples(sense_id)
                if examples:
                    print(f"   Example: \"{examples[0][:80]}...\"" if len(examples[0]) > 80 else f"   Example: \"{examples[0]}\"")

                # SYNONYMS - The key feature!
                synonyms = db.get_synonyms(sense_id, min_similarity)

                if synonyms:
                    # Group synonyms by similarity score
                    high_sim = [s for s in synonyms if s['similarity_score'] and s['similarity_score'] >= 0.85]
                    med_sim = [s for s in synonyms if s['similarity_score'] and 0.70 <= s['similarity_score'] < 0.85]
                    low_sim = [s for s in synonyms if s['similarity_score'] and s['similarity_score'] < 0.70]

                    print(f"\n   SYNONYMS:")

                    if high_sim:
                        syn_words = [s['word'] for s in high_sim[:15]]
                        print(f"     Direct: {', '.join(syn_words)}")

                    if med_sim:
                        syn_words = [s['word'] for s in med_sim[:10]]
                        print(f"     Related: {', '.join(syn_words)}")

                    if low_sim:
                        syn_words = [s['word'] for s in low_sim[:5]]
                        print(f"     Contextual: {', '.join(syn_words)}")

                print()

            # Etymology
            if pos_senses[0].get('etymology_text'):
                etym = pos_senses[0]['etymology_text']
                if len(etym) > 150:
                    etym = etym[:150] + "..."
                try:
                    print(f"Etymology: {etym}\n")
                except UnicodeEncodeError:
                    print(f"Etymology: [unicode text]\n")


def filter_by_tone(word: str, tone: str):
    """Show only synonyms matching a specific tone (slang, informal, formal, etc.)"""
    with ThesaurusDB() as db:
        senses = db.search_word(word)

        if not senses:
            print(f"\n'{word}' not found.")
            return

        print(f"\n{'='*70}")
        print(f" {word.upper()} - {tone.upper()} SYNONYMS")
        print(f"{'='*70}\n")

        for sense in senses:
            sense_id = sense['sense_id']
            synonyms = db.get_synonyms(sense_id, 0.5)

            if not synonyms:
                continue

            # Filter synonyms by tone
            filtered_syns = []
            for syn in synonyms:
                # Get tags for synonym sense
                # This requires looking up the target sense's tags
                cursor = db.execute("""
                    SELECT w.word, s.id
                    FROM words w
                    JOIN senses s ON w.id = s.word_id
                    WHERE w.word = ?
                    LIMIT 1
                """, (syn['word'],))

                row = cursor.fetchone()
                if row:
                    syn_sense_id = row[1]
                    syn_tags = db.get_sense_tags(syn_sense_id)
                    tag_names = [t['tag_name'] for t in syn_tags]

                    if tone.lower() in tag_names:
                        filtered_syns.append(syn['word'])

            if filtered_syns:
                print(f"{sense['definition'][:60]}...")
                print(f"  {', '.join(filtered_syns[:20])}\n")


def main():
    """Main CLI"""
    if len(sys.argv) < 2:
        print("Thesaurus+ - The Slang-Aware Thesaurus")
        print("\nUsage:")
        print("  python thesaurus.py <word>           - Search for a word")
        print("  python thesaurus.py <word> --slang   - Show only slang synonyms")
        print("  python thesaurus.py <word> --formal  - Show only formal synonyms")
        print("\nExamples:")
        print("  python thesaurus.py cool")
        print("  python thesaurus.py hit --slang")
        print("  python thesaurus.py angry --formal")
        return

    word = sys.argv[1]

    # Check for filter flags
    if len(sys.argv) > 2:
        filter_arg = sys.argv[2].replace('--', '')
        filter_by_tone(word, filter_arg)
    else:
        search_thesaurus(word)


if __name__ == "__main__":
    main()
