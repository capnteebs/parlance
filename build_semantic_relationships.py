"""
Build semantic similarity relationships using pre-generated embeddings.
No confirmation needed - just runs.
"""

from semantic_similarity import SemanticSimilarityEngine
from database import ThesaurusDB
import pickle
from pathlib import Path

def main():
    """Build semantic relationships from cached embeddings"""

    embeddings_file = "embeddings.pkl"

    if not Path(embeddings_file).exists():
        print(f"ERROR: {embeddings_file} not found!")
        print("Run: python semantic_similarity.py first")
        return

    print("Loading cached embeddings...")
    with open(embeddings_file, 'rb') as f:
        embeddings = pickle.load(f)

    print(f"Loaded {len(embeddings)} embeddings")

    with ThesaurusDB() as db:
        engine = SemanticSimilarityEngine(db)
        engine.embeddings = embeddings

        print("\nBuilding semantic similarity relationships...")
        print("Threshold: 0.75")
        print("Max synonyms per sense: 30")
        print("\nThis will take several minutes for 49k senses...\n")

        engine.build_semantic_relationships(
            min_similarity=0.75,
            max_synonyms_per_sense=30
        )

    print("\n[OK] Done! Testing...")

    # Show stats
    with ThesaurusDB() as db:
        cursor = db.execute("""
            SELECT COUNT(*) FROM relationships WHERE relationship_type = 'synonym'
        """)
        total = cursor.fetchone()[0]

        print(f"\nTotal synonym relationships: {total:,}")

        print("\nTest with:")
        print("  python test_synonyms.py --stats")
        print("  python thesaurus.py cool")


if __name__ == "__main__":
    main()
