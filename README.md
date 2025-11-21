# Thesaurus+ 🌐

**The Slang-Aware Thesaurus** | Mapping Language by Meaning, Tone, Era & Region

A living, dynamic linguistic tool that bridges dictionaries, thesauruses, and lived language—especially slang, idioms, and cultural expressions.

---

## 🎯 What Makes This Different

**Traditional thesauruses** give you "angry" → "mad, furious, irate"

**Thesaurus+** gives you:
- 💬 **Tone filtering**: Find formal, informal, slang, or vulgar equivalents
- 🌍 **Regional variants**: Discover US, UK, Australian, AAVE expressions
- 📊 **Similarity scores**: See how substitutable words really are (0.5-1.0)
- 🔗 **Semantic connections**: AI finds synonyms by understanding definitions
- 💬 **Idioms & phrases**: "rain cats and dogs", "kick the bucket"
- 🔥 **Modern slang**: Urban Dictionary integration for current expressions
- 📜 **Historical context**: Etymology, era tags (archaic, obsolete, modern)
- 🎯 **Multiple senses**: Polysemy support (e.g., "cool" has 25+ meanings)

---

## ✨ Features

### 1. Multi-Source Data Integration
- **Wiktionary**: 8,000+ words, 49,000+ senses with definitions, etymology, examples
- **Urban Dictionary**: Modern slang and internet language
- **Semantic AI**: NLP discovers 40,000+ additional synonym relationships

### 2. Advanced Filtering
Filter results by:
- **Register**: slang, informal, formal, vulgar
- **Region**: US, UK, Australian, AAVE
- **Era**: archaic, obsolete, dated, modern
- **Similarity**: 85-100% (direct), 70-84% (related), 50-69% (contextual)

### 3. Phrases & Idioms
- 277 multi-word expressions
- Idioms: "rain cats and dogs"
- Collocations: "computer science", "teddy bear"
- Auto-linked to component words

### 4. Beautiful Web Interface
- Real-time search with Enter key
- Clickable synonym navigation
- Color-coded tags
- Live database statistics
- Mobile responsive

### 5. RESTful API
JSON endpoints for programmatic access:
- `/api/search?q=cool&filter_tags=slang`
- `/api/stats` - Database metrics
- `/api/tags` - Available filters

---

## 🚀 Quick Start

**Install dependencies:**
```bash
pip install requests flask sentence-transformers
```

**Build database:**
```bash
python download_large_sample.py
python import_wiktextract.py
python build_synonyms.py
python semantic_similarity.py
python import_phrases.py 300
```

**Launch web interface:**
```bash
python app.py
```

Open **http://localhost:5000** in your browser!

---

## 📖 Documentation

- **[USER_GUIDE.md](USER_GUIDE.md)** - Complete setup and usage guide
- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Command cheat sheet
- **[WEB_INTERFACE.md](WEB_INTERFACE.md)** - Web features overview
- **[slang_tool_manifesto.md](slang_tool_manifesto.md)** - Project vision and principles

---

## 🎨 Screenshot Examples

**Search for "cool" with slang filter:**
```
cool (adj) - Fashionable; trendy; hip
  🔥 slang  💬 informal

  Synonyms:
  ✨ Direct: hip (92%), neat (88%), dope (87%)
  🔗 Related: awesome (78%), sick (76%)

  💬 Phrases:
  [idiom] cool as a cucumber - Very calm and composed

  Urban Dictionary:
  The best way to say something is neat-o, awesome, or swell...
```

**Search for "rain":**
```
rain (verb) - To fall from the clouds in drops of water

  💬 Phrases:
  [idiom] rain cats and dogs - To rain very heavily
  [idiom] rain on someone's parade - To spoil someone's plans
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────┐
│           Web Interface (Flask)             │
│         http://localhost:5000               │
└─────────────────┬───────────────────────────┘
                  │
┌─────────────────▼───────────────────────────┐
│              REST API                        │
│  /api/search  /api/stats  /api/tags        │
└─────────────────┬───────────────────────────┘
                  │
┌─────────────────▼───────────────────────────┐
│         Database Layer (SQLite)             │
│                                             │
│  ┌─────────┐  ┌──────────┐  ┌───────────┐ │
│  │  Words  │  │  Senses  │  │  Phrases  │ │
│  └────┬────┘  └─────┬────┘  └─────┬─────┘ │
│       │             │              │       │
│  ┌────▼──────────────▼──────────────▼────┐ │
│  │      Relationships (synonyms)         │ │
│  └───────────────────────────────────────┘ │
└─────────────────────────────────────────────┘

Data Sources:
- Wiktionary (via Wiktextract)
- Urban Dictionary (API)
- Semantic Similarity (NLP)
```

---

## 📊 Database Statistics

After full import:

| Metric | Count |
|--------|-------|
| **Words** | 8,034 |
| **Word Senses** | 49,608 |
| **Synonym Relationships** | 65,855 |
| **Phrases/Idioms** | 277 |
| **Tags** | 370 |
| **Examples** | 12,453 |

---

## 🛠️ Tools & Scripts

| Script | Purpose |
|--------|---------|
| `app.py` | Flask web server |
| `database.py` | Database interface |
| `import_wiktextract.py` | Import Wiktionary data |
| `build_synonyms.py` | Extract explicit synonyms |
| `semantic_similarity.py` | AI-powered synonym discovery |
| `urban_dictionary.py` | Import modern slang |
| `import_phrases.py` | Import idioms and phrases |
| `download_large_sample.py` | Download Wiktextract data |

---

## 🎯 Core Principles

### 1. No AI Hallucination
Every word and definition comes from real, human-curated sources:
- Wiktionary (crowd-sourced dictionary)
- Urban Dictionary (user-contributed slang)
- AI only finds connections between existing words

### 2. Anthropological Respect
Language is culture. We treat words—especially slang and taboo—with historical and social context, not moral judgment.

### 3. Traceability
Every synonym, idiom, or connection traces back to a source. No invented relationships.

### 4. Human First, Machine Assisted
AI assists pattern recognition, but human curation and nuance remain essential.

---

## 🌟 Use Cases

**Writers & Authors:**
- Find tone-appropriate synonyms for your genre
- Discover period-accurate historical terms
- Explore regional dialects for character voices

**Linguists & Researchers:**
- Study slang evolution and regional variants
- Track semantic relationships across word senses
- Analyze cultural expressions and idioms

**Screenwriters & Comedians:**
- Source authentic slang and cultural expressions
- Find period-specific language for historical settings
- Explore coded language and subculture terms

**Language Learners:**
- Understand formal vs informal usage
- Learn idioms and multi-word expressions
- See real usage examples in context

**Coders & Technical Writers:**
- Find precise technical synonyms
- Discover domain-specific collocations
- Maintain consistent terminology

---

## 🔮 Roadmap

Potential enhancements:
- [ ] Synonym network visualization (interactive graph)
- [ ] Dark mode theme
- [ ] Export results (JSON/CSV)
- [ ] Persistent search URLs
- [ ] Audio pronunciations (text-to-speech)
- [ ] Historical usage trends
- [ ] Cross-language translation support
- [ ] Progressive Web App (offline capability)
- [ ] More Urban Dictionary integration
- [ ] Antonym relationships
- [ ] Word frequency data

---

## 📚 API Examples

**Search for slang:**
```bash
curl "http://localhost:5000/api/search?q=cool&filter_tags=slang"
```

**Get database stats:**
```bash
curl "http://localhost:5000/api/stats"
```

**Response:**
```json
{
  "word": "cool",
  "found": true,
  "result_count": 5,
  "results": [
    {
      "word": "cool",
      "pos": "adj",
      "definition": "Fashionable; trendy; hip",
      "tags": [{"tag_name": "slang", "category": "register"}],
      "synonyms": {
        "direct": [{"word": "hip", "score": 0.92}],
        "related": [{"word": "neat", "score": 0.78}]
      },
      "phrases": [
        {
          "phrase_text": "cool as a cucumber",
          "definition": "Very calm and composed",
          "phrase_type": "idiom"
        }
      ]
    }
  ]
}
```

---

## 🤝 Contributing

This project is open for linguistic exploration. Contributions welcome:

- Add more data sources
- Improve quality filters
- Enhance semantic similarity
- Expand phrase coverage
- Build visualizations
- Improve UI/UX

---

## 📜 License & Credits

### Data Sources
- **Wiktionary**: CC BY-SA 3.0 (crowd-sourced dictionary)
- **Wiktextract**: Pre-processed Wiktionary by Tatu Ylonen
- **Urban Dictionary**: User-contributed modern slang
- **Sentence Transformers**: NLP models by UKPLab

### Technology Stack
- **Backend**: Python, Flask, SQLite
- **NLP**: sentence-transformers (all-MiniLM-L6-v2)
- **Frontend**: Vanilla JavaScript, CSS
- **APIs**: Urban Dictionary, Wiktextract

---

## 🎯 Philosophy

> "This project is for the lovers of language in all its dirty, sacred, evolving forms."

This is not simply for "finding synonyms." It is a **map of how humans actually speak**—raw, poetic, rude, beautiful, fleeting. A living museum of:
- Street poetry
- Internet lingo
- Dialect and coded language
- Defiance and invention
- Cultural expression

---

## 📧 Support

Having issues? Check:
1. **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Common commands
2. **[USER_GUIDE.md](USER_GUIDE.md)** - Troubleshooting section
3. Database queries in quick reference
4. API documentation

---

## ⚡ Quick Commands

```bash
# Start everything
python app.py

# Update database
python urban_dictionary.py 20
python import_phrases.py 300

# Check stats
python -c "from database import ThesaurusDB; db = ThesaurusDB(); cursor = db.execute('SELECT COUNT(*) FROM words'); print(f'Words: {cursor.fetchone()[0]}'); db.close()"
```

---

**Built with ❤️ for language lovers, writers, researchers, and anyone fascinated by how humans actually speak.**

Open **http://localhost:5000** and start exploring! 🚀
