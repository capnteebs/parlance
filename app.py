"""
Thesaurus+ Web Interface
Flask application for the slang-aware thesaurus
"""

from flask import Flask, render_template, request, jsonify
from database import ThesaurusDB
import json

app = Flask(__name__)

# Database connection helper
def get_db():
    return ThesaurusDB()

@app.route('/')
def index():
    """Main search page"""
    return render_template('index.html')

@app.route('/api/search')
def api_search():
    """
    API endpoint for word search
    Query params:
        - q: search query (word)
        - filter_tags: comma-separated tags (optional)
        - min_similarity: minimum similarity score (optional)
    """
    query = request.args.get('q', '').strip().lower()

    if not query:
        return jsonify({'error': 'No search query provided'}), 400

    # Get optional filters
    filter_tags = request.args.get('filter_tags', '')
    filter_tags = [t.strip() for t in filter_tags.split(',') if t.strip()]
    min_similarity = float(request.args.get('min_similarity', 0.5))

    with get_db() as db:
        # Search for word
        senses = db.search_word(query)

        if not senses:
            return jsonify({
                'word': query,
                'found': False,
                'message': f"Word '{query}' not found in database"
            })

        # Build response
        results = []

        for sense in senses:
            sense_id = sense['sense_id']

            # Get tags
            tags = db.get_sense_tags(sense_id)
            tag_names = [t['tag_name'] for t in tags]

            # Apply tag filter if specified
            if filter_tags:
                if not any(tag in tag_names for tag in filter_tags):
                    continue

            # Get synonyms
            synonyms = db.get_synonyms(sense_id, min_similarity)

            # Get examples
            examples = db.get_examples(sense_id)

            # Get related phrases/idioms
            phrases = db.get_related_phrases(sense_id)

            # Group synonyms by similarity
            high_sim = [s for s in synonyms if s['similarity_score'] and s['similarity_score'] >= 0.85]
            med_sim = [s for s in synonyms if s['similarity_score'] and 0.70 <= s['similarity_score'] < 0.85]
            low_sim = [s for s in synonyms if s['similarity_score'] and s['similarity_score'] < 0.70]

            results.append({
                'sense_id': sense_id,
                'word': sense['word'],
                'pos': sense['pos'],
                'definition': sense['definition'],
                'etymology': sense['etymology_text'],
                'tags': tags,
                'examples': examples[:3],  # Limit to 3 examples
                'phrases': phrases[:5],  # Limit to 5 phrases
                'synonyms': {
                    'direct': [{'word': s['word'], 'score': s['similarity_score']} for s in high_sim[:15]],
                    'related': [{'word': s['word'], 'score': s['similarity_score']} for s in med_sim[:10]],
                    'contextual': [{'word': s['word'], 'score': s['similarity_score']} for s in low_sim[:5]]
                },
                'synonym_count': len(synonyms)
            })

        return jsonify({
            'word': query,
            'found': True,
            'result_count': len(results),
            'results': results
        })

@app.route('/api/stats')
def api_stats():
    """Get database statistics"""
    with get_db() as db:
        # Word count
        cursor = db.execute("SELECT COUNT(*) FROM words")
        word_count = cursor.fetchone()[0]

        # Sense count
        cursor = db.execute("SELECT COUNT(*) FROM senses")
        sense_count = cursor.fetchone()[0]

        # Relationship count
        cursor = db.execute("SELECT COUNT(*) FROM relationships")
        relationship_count = cursor.fetchone()[0]

        # Tag count
        cursor = db.execute("SELECT COUNT(*) FROM tags")
        tag_count = cursor.fetchone()[0]

        # Example count
        cursor = db.execute("SELECT COUNT(*) FROM examples")
        example_count = cursor.fetchone()[0]

        # Top tags
        cursor = db.execute("""
            SELECT t.tag_name, t.category, COUNT(st.sense_id) as count
            FROM tags t
            JOIN sense_tags st ON t.id = st.tag_id
            WHERE t.category IN ('register', 'region', 'era')
            GROUP BY t.id
            ORDER BY count DESC
            LIMIT 20
        """)
        top_tags = [{'tag': row[0], 'category': row[1], 'count': row[2]} for row in cursor.fetchall()]

        return jsonify({
            'words': word_count,
            'senses': sense_count,
            'relationships': relationship_count,
            'tags': tag_count,
            'examples': example_count,
            'top_tags': top_tags
        })

@app.route('/api/tags')
def api_tags():
    """Get all available tags for filtering"""
    with get_db() as db:
        cursor = db.execute("""
            SELECT t.tag_name, t.category, COUNT(st.sense_id) as usage_count
            FROM tags t
            LEFT JOIN sense_tags st ON t.id = st.tag_id
            WHERE t.category IN ('register', 'region', 'era', 'offensive')
            GROUP BY t.id
            ORDER BY t.category, usage_count DESC
        """)

        tags_by_category = {}
        for row in cursor.fetchall():
            tag_name = row[0]
            category = row[1] or 'other'
            count = row[2]

            if category not in tags_by_category:
                tags_by_category[category] = []

            tags_by_category[category].append({
                'name': tag_name,
                'count': count
            })

        return jsonify(tags_by_category)

@app.route('/about')
def about():
    """About page"""
    return render_template('about.html')

if __name__ == '__main__':
    print("\n" + "="*70)
    print(" THESAURUS+ WEB SERVER")
    print("="*70)
    print("\nStarting server...")
    print("Open your browser to: http://localhost:5000")
    print("\nPress Ctrl+C to stop the server")
    print("="*70 + "\n")

    app.run(debug=True, host='0.0.0.0', port=5000)
