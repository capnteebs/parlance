"""
Test and display synonym relationships
"""

from database import ThesaurusDB
import sys

def show_synonyms_for_word(word: str, min_similarity: float = 0.0):
    """Show all synonyms for a word with their similarity scores"""
    with ThesaurusDB() as db:
        # Get all senses for this word
        senses = db.search_word(word)

        if not senses:
            print(f"\nWord '{word}' not found in database.")
            return

        print(f"\n{'='*70}")
        print(f" SYNONYMS FOR: {word.upper()}")
        print(f"{'='*70}\n")

        total_synonyms = 0

        # For each sense, show its synonyms
        for sense in senses:
            sense_id = sense['sense_id']
            pos = sense['pos'] or 'unknown'
            definition = sense['definition']

            # Get synonyms for this sense
            synonyms = db.get_synonyms(sense_id, min_similarity)

            if not synonyms:
                continue

            # Display sense header
            print(f"{word} ({pos})")
            print(f"  Definition: {definition[:80]}...")
            print(f"  Synonyms ({len(synonyms)}):")

            # Display synonyms sorted by similarity
            for syn in synonyms:
                score = syn['similarity_score']
                score_str = f"{score:.2f}" if score else "N/A"
                syn_word = syn['word']
                syn_pos = syn['pos'] or '?'
                syn_def = syn['definition'][:50] + "..." if len(syn['definition']) > 50 else syn['definition']

                print(f"    [{score_str}] {syn_word} ({syn_pos}) - {syn_def}")

            print()
            total_synonyms += len(synonyms)

        print(f"Total synonyms found: {total_synonyms}\n")


def show_synonym_network(word: str, depth: int = 2):
    """Show synonym network expanding from a word"""
    with ThesaurusDB() as db:
        print(f"\n{'='*70}")
        print(f" SYNONYM NETWORK: {word.upper()} (depth {depth})")
        print(f"{'='*70}\n")

        # Get starting word
        senses = db.search_word(word)
        if not senses:
            print(f"Word '{word}' not found.")
            return

        # Use first sense
        sense_id = senses[0]['sense_id']

        # Get direct synonyms
        synonyms_l1 = db.get_synonyms(sense_id, min_similarity=0.7)

        print(f"{word}")
        for syn in synonyms_l1[:10]:  # Limit to 10
            score = syn['similarity_score'] or 0
            print(f"  -> [{score:.2f}] {syn['word']}")

            if depth > 1:
                # Get second-level synonyms
                cursor = db.execute("""
                    SELECT w.word, s.id as sense_id
                    FROM words w
                    JOIN senses s ON w.id = s.word_id
                    WHERE w.word = ?
                    LIMIT 1
                """, (syn['word'],))

                row = cursor.fetchone()
                if row:
                    syn_sense_id = row[1]
                    synonyms_l2 = db.get_synonyms(syn_sense_id, min_similarity=0.7)

                    for syn2 in synonyms_l2[:5]:  # Limit to 5
                        score2 = syn2['similarity_score'] or 0
                        print(f"      -> [{score2:.2f}] {syn2['word']}")


def analyze_similarity_distribution():
    """Analyze the distribution of similarity scores"""
    with ThesaurusDB() as db:
        print(f"\n{'='*70}")
        print(" SIMILARITY SCORE DISTRIBUTION")
        print(f"{'='*70}\n")

        # Get distribution
        cursor = db.execute("""
            SELECT
                CASE
                    WHEN similarity_score >= 0.9 THEN '0.90-1.00 (Perfect)'
                    WHEN similarity_score >= 0.8 THEN '0.80-0.89 (High)'
                    WHEN similarity_score >= 0.7 THEN '0.70-0.79 (Good)'
                    WHEN similarity_score >= 0.6 THEN '0.60-0.69 (Moderate)'
                    WHEN similarity_score >= 0.5 THEN '0.50-0.59 (Low)'
                    ELSE 'Below 0.50'
                END as score_range,
                COUNT(*) as count
            FROM relationships
            WHERE relationship_type = 'synonym'
            GROUP BY score_range
            ORDER BY score_range DESC
        """)

        for row in cursor.fetchall():
            range_name = row[0]
            count = row[1]
            print(f"  {range_name:<25} {count:>6} relationships")

        # Total
        cursor = db.execute("""
            SELECT COUNT(*) FROM relationships WHERE relationship_type = 'synonym'
        """)
        total = cursor.fetchone()[0]
        print(f"\n  Total synonym relationships: {total:,}")


def find_highly_connected_words():
    """Find words with the most synonyms"""
    with ThesaurusDB() as db:
        print(f"\n{'='*70}")
        print(" MOST HIGHLY CONNECTED WORDS")
        print(f"{'='*70}\n")

        cursor = db.execute("""
            SELECT w.word, s.pos, COUNT(r.id) as synonym_count
            FROM words w
            JOIN senses s ON w.id = s.word_id
            JOIN relationships r ON s.id = r.source_sense_id
            WHERE r.relationship_type = 'synonym'
            GROUP BY s.id
            ORDER BY synonym_count DESC
            LIMIT 20
        """)

        print("Words with most synonyms:")
        for row in cursor.fetchall():
            word = row[0]
            pos = row[1] or '?'
            count = row[2]
            print(f"  {word:<20} ({pos}) - {count} synonyms")


def main():
    """Main test interface"""
    if len(sys.argv) < 2:
        print("Synonym Test Tool")
        print("\nUsage:")
        print("  python test_synonyms.py <word>        - Show synonyms for a word")
        print("  python test_synonyms.py --network <word> - Show synonym network")
        print("  python test_synonyms.py --stats       - Show statistics")
        print("  python test_synonyms.py --top         - Show most connected words")
        print("\nExamples:")
        print("  python test_synonyms.py angry")
        print("  python test_synonyms.py cool")
        return

    command = sys.argv[1]

    if command == '--stats':
        analyze_similarity_distribution()
    elif command == '--top':
        find_highly_connected_words()
    elif command == '--network':
        if len(sys.argv) > 2:
            show_synonym_network(sys.argv[2])
        else:
            print("Please provide a word for network analysis")
    else:
        # Show synonyms for word
        show_synonyms_for_word(command)


if __name__ == "__main__":
    main()
