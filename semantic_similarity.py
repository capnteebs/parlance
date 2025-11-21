"""
Semantic Similarity Engine for Thesaurus+
Uses NLP embeddings to find similar word senses based on definition text.
"""

import numpy as np
from database import ThesaurusDB
import pickle
from pathlib import Path

# Try to import sentence-transformers
try:
    from sentence_transformers import SentenceTransformer
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False
    print("WARNING: sentence-transformers not installed")
    print("Install with: pip install sentence-transformers")

class SemanticSimilarityEngine:
    """Generate and compare semantic embeddings of word definitions"""

    def __init__(self, db: ThesaurusDB, model_name: str = 'all-MiniLM-L6-v2'):
        self.db = db
        self.model_name = model_name
        self.model = None
        self.embeddings = {}  # sense_id -> embedding vector
        self.embeddings_file = "embeddings.pkl"

    def load_model(self):
        """Load the sentence transformer model"""
        if not HAS_TRANSFORMERS:
            raise ImportError("sentence-transformers not installed")

        print(f"Loading model: {self.model_name}")
        print("(This may take a minute on first run...)")
        self.model = SentenceTransformer(self.model_name)
        print("[OK] Model loaded")

    def generate_embeddings(self, max_senses: int = None, force_regenerate: bool = False):
        """
        Generate embeddings for all sense definitions.

        Args:
            max_senses: Limit number of senses (for testing)
            force_regenerate: Regenerate even if cached file exists
        """
        # Check if embeddings already exist
        if Path(self.embeddings_file).exists() and not force_regenerate:
            print(f"Loading cached embeddings from {self.embeddings_file}")
            with open(self.embeddings_file, 'rb') as f:
                self.embeddings = pickle.load(f)
            print(f"[OK] Loaded {len(self.embeddings)} cached embeddings")
            return

        if not self.model:
            self.load_model()

        print("\nGenerating embeddings for word sense definitions...")

        # Get all senses with definitions
        cursor = self.db.execute("""
            SELECT s.id, w.word, s.pos, s.definition
            FROM senses s
            JOIN words w ON s.word_id = w.id
            WHERE s.definition IS NOT NULL
            ORDER BY s.id
        """)

        senses = cursor.fetchall()
        if max_senses:
            senses = senses[:max_senses]

        print(f"Processing {len(senses)} word senses...")

        # Prepare texts for embedding
        texts = []
        sense_ids = []

        for row in senses:
            sense_id = row[0]
            word = row[1]
            pos = row[2] or ''
            definition = row[3]

            # Combine word, POS, and definition for better context
            text = f"{word} ({pos}): {definition}"
            texts.append(text)
            sense_ids.append(sense_id)

        # Generate embeddings in batches
        batch_size = 32
        print(f"Encoding in batches of {batch_size}...")

        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i+batch_size]
            batch_ids = sense_ids[i:i+batch_size]

            # Encode batch
            embeddings = self.model.encode(batch_texts, show_progress_bar=False)

            # Store embeddings
            for sense_id, embedding in zip(batch_ids, embeddings):
                self.embeddings[sense_id] = embedding

            if (i + batch_size) % 1000 == 0:
                print(f"  Encoded {i + batch_size}/{len(texts)} senses...")

        print(f"\n[OK] Generated {len(self.embeddings)} embeddings")

        # Cache embeddings
        print(f"Saving embeddings to {self.embeddings_file}...")
        with open(self.embeddings_file, 'wb') as f:
            pickle.dump(self.embeddings, f)
        print("[OK] Embeddings cached")

    def compute_similarity(self, sense_id1: int, sense_id2: int) -> float:
        """Compute cosine similarity between two sense embeddings"""
        if sense_id1 not in self.embeddings or sense_id2 not in self.embeddings:
            return 0.0

        emb1 = self.embeddings[sense_id1]
        emb2 = self.embeddings[sense_id2]

        # Cosine similarity
        similarity = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
        return float(similarity)

    def find_similar_senses(self, sense_id: int, min_similarity: float = 0.7,
                           max_results: int = 50) -> list:
        """
        Find senses most similar to the given sense.

        Returns list of (sense_id, similarity_score) tuples
        """
        if sense_id not in self.embeddings:
            return []

        target_embedding = self.embeddings[sense_id]
        similarities = []

        # Compare with all other senses
        for other_id, other_embedding in self.embeddings.items():
            if other_id == sense_id:
                continue

            # Compute cosine similarity
            similarity = np.dot(target_embedding, other_embedding) / \
                        (np.linalg.norm(target_embedding) * np.linalg.norm(other_embedding))

            if similarity >= min_similarity:
                similarities.append((other_id, float(similarity)))

        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x[1], reverse=True)

        return similarities[:max_results]

    def build_semantic_relationships(self, min_similarity: float = 0.75,
                                    max_synonyms_per_sense: int = 30):
        """
        Build synonym relationships based on semantic similarity.

        Args:
            min_similarity: Minimum cosine similarity (0.7-0.8 recommended)
            max_synonyms_per_sense: Maximum synonyms to add per sense
        """
        print(f"\n{'='*70}")
        print(" BUILDING SEMANTIC SIMILARITY RELATIONSHIPS")
        print(f"{'='*70}\n")

        print(f"Min similarity threshold: {min_similarity}")
        print(f"Max synonyms per sense: {max_synonyms_per_sense}")

        if not self.embeddings:
            print("Error: No embeddings loaded. Run generate_embeddings() first.")
            return

        relationships_added = 0
        senses_processed = 0

        # Process each sense
        for sense_id in self.embeddings.keys():
            # Find similar senses
            similar = self.find_similar_senses(
                sense_id,
                min_similarity=min_similarity,
                max_results=max_synonyms_per_sense
            )

            # Add relationships
            for similar_id, similarity in similar:
                # Check if relationship already exists
                cursor = self.db.execute("""
                    SELECT id FROM relationships
                    WHERE source_sense_id = ? AND target_sense_id = ?
                    AND relationship_type = 'synonym'
                """, (sense_id, similar_id))

                if cursor.fetchone():
                    continue  # Already exists

                # Add semantic similarity relationship
                self.db.insert_relationship(
                    sense_id,
                    similar_id,
                    'synonym',
                    similarity  # Use cosine similarity as score
                )
                relationships_added += 1

            senses_processed += 1

            # Commit in batches
            if senses_processed % 100 == 0:
                self.db.commit()
                print(f"  Processed {senses_processed}/{len(self.embeddings)} senses, "
                      f"added {relationships_added} relationships")

        # Final commit
        self.db.commit()

        print(f"\n[OK] Added {relationships_added} semantic similarity relationships")


def main():
    """Main semantic similarity workflow"""
    import sys

    if not HAS_TRANSFORMERS:
        print("\nERROR: sentence-transformers not installed")
        print("\nInstall with:")
        print("  pip install sentence-transformers")
        print("\nThis will download ~80MB of model weights on first run.")
        return

    # Parse arguments
    force_regenerate = '--regenerate' in sys.argv
    test_mode = '--test' in sys.argv

    with ThesaurusDB() as db:
        engine = SemanticSimilarityEngine(db)

        # Generate embeddings
        if test_mode:
            print("TEST MODE: Processing only 1000 senses")
            engine.generate_embeddings(max_senses=1000, force_regenerate=force_regenerate)
            min_similarity = 0.75
        else:
            engine.generate_embeddings(force_regenerate=force_regenerate)
            min_similarity = 0.75

        # Build relationships
        print("\nReady to build semantic similarity relationships.")
        print(f"This will find synonyms based on definition similarity.")
        print(f"Threshold: {min_similarity} (higher = stricter)")

        response = input("\nProceed? (y/n): ")
        if response.lower() != 'y':
            print("Cancelled.")
            return

        engine.build_semantic_relationships(
            min_similarity=min_similarity,
            max_synonyms_per_sense=30
        )

        print("\n[OK] Semantic similarity relationships built!")
        print("\nTest with:")
        print("  python thesaurus.py angry")
        print("  python test_synonyms.py cool")


if __name__ == "__main__":
    main()
