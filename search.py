"""
Search and query interface for Thesaurus+ database
"""

from database import ThesaurusDB
import sys

def format_sense(sense: dict, tags: list, examples: list, index: int = None) -> str:
    """Format a sense for display"""
    output = []

    # Header
    prefix = f"{index}. " if index else ""
    pos_str = f" ({sense['pos']})" if sense['pos'] else ""
    output.append(f"{prefix}{sense['definition']}{pos_str}")

    # Tags
    if tags:
        tag_strs = []
        for tag in tags:
            tag_name = tag['tag_name']
            category = tag.get('category', '')
            if category:
                tag_strs.append(f"{tag_name} [{category}]")
            else:
                tag_strs.append(tag_name)
        output.append(f"     Tags: {', '.join(tag_strs)}")

    # Examples
    if examples:
        output.append(f"     Examples:")
        for ex in examples[:2]:  # Limit to 2
            output.append(f'       "{ex}"')

    return '\n'.join(output)


def search_word(word: str):
    """Search for a word and display all its senses"""
    with ThesaurusDB() as db:
        senses = db.search_word(word)

        if not senses:
            print(f"\nWord '{word}' not found in database.")
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

        # Display each POS group
        for pos, pos_senses in by_pos.items():
            print(f"\n--- {pos.upper()} ---\n")

            for i, sense in enumerate(pos_senses, 1):
                # Get tags and examples
                tags = db.get_sense_tags(sense['sense_id'])
                examples = db.get_examples(sense['sense_id'])

                # Format and print
                print(format_sense(sense, tags, examples, index=i))
                print()

            # Show etymology if available
            if pos_senses[0].get('etymology_text'):
                etym = pos_senses[0]['etymology_text']
                if len(etym) > 200:
                    etym = etym[:200] + "..."
                print(f"Etymology: {etym}\n")


def show_tags():
    """Display all tags in database"""
    with ThesaurusDB() as db:
        cursor = db.execute(
            """SELECT tag_name, category, COUNT(st.sense_id) as usage_count
               FROM tags t
               LEFT JOIN sense_tags st ON t.id = st.tag_id
               GROUP BY t.id
               ORDER BY t.category, t.tag_name"""
        )

        print(f"\n{'='*70}")
        print(" TAGS IN DATABASE")
        print(f"{'='*70}\n")

        current_category = None
        for row in cursor.fetchall():
            tag_name = row[0]
            category = row[1] or 'other'
            count = row[2]

            if category != current_category:
                current_category = category
                print(f"\n{category.upper()}:")

            print(f"  {tag_name:<20} (used {count} times)")


def show_stats():
    """Display database statistics"""
    with ThesaurusDB() as db:
        print(f"\n{'='*70}")
        print(" DATABASE STATISTICS")
        print(f"{'='*70}\n")

        # Word count
        cursor = db.execute("SELECT COUNT(*) FROM words")
        word_count = cursor.fetchone()[0]
        print(f"Total words: {word_count}")

        # Sense count
        cursor = db.execute("SELECT COUNT(*) FROM senses")
        sense_count = cursor.fetchone()[0]
        print(f"Total senses: {sense_count}")

        # Average senses per word
        avg_senses = sense_count / word_count if word_count > 0 else 0
        print(f"Average senses per word: {avg_senses:.1f}")

        # Tag count
        cursor = db.execute("SELECT COUNT(*) FROM tags")
        tag_count = cursor.fetchone()[0]
        print(f"Total tags: {tag_count}")

        # Example count
        cursor = db.execute("SELECT COUNT(*) FROM examples")
        example_count = cursor.fetchone()[0]
        print(f"Total examples: {example_count}")

        # Top tags
        print(f"\nMost used tags:")
        cursor = db.execute(
            """SELECT t.tag_name, COUNT(st.sense_id) as cnt
               FROM tags t
               JOIN sense_tags st ON t.id = st.tag_id
               GROUP BY t.id
               ORDER BY cnt DESC
               LIMIT 10"""
        )
        for row in cursor.fetchall():
            print(f"  {row[0]:<20} {row[1]} uses")

        # List all words
        print(f"\nWords in database:")
        cursor = db.execute("SELECT DISTINCT word FROM words ORDER BY word")
        words = [row[0] for row in cursor.fetchall()]
        print(f"  {', '.join(words)}")


def list_words():
    """List all words in database"""
    with ThesaurusDB() as db:
        cursor = db.execute(
            """SELECT w.word, COUNT(s.id) as sense_count
               FROM words w
               LEFT JOIN senses s ON w.id = s.word_id
               GROUP BY w.id
               ORDER BY w.word"""
        )

        print(f"\n{'='*70}")
        print(" WORDS IN DATABASE")
        print(f"{'='*70}\n")

        for row in cursor.fetchall():
            word = row[0]
            sense_count = row[1]
            print(f"  {word:<20} ({sense_count} senses)")


def main():
    """Main CLI interface"""
    if len(sys.argv) < 2:
        print("Thesaurus+ Search Tool")
        print("\nUsage:")
        print("  python search.py <word>       - Search for a word")
        print("  python search.py --tags       - Show all tags")
        print("  python search.py --stats      - Show statistics")
        print("  python search.py --list       - List all words")
        print("\nExamples:")
        print("  python search.py angry")
        print("  python search.py cool")
        return

    command = sys.argv[1]

    if command == '--tags':
        show_tags()
    elif command == '--stats':
        show_stats()
    elif command == '--list':
        list_words()
    else:
        search_word(command)


if __name__ == "__main__":
    main()
