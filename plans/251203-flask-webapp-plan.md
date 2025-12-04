# Flask Webapp for PubMed Query Generator

**Date**: 2025-12-03
**Status**: Planning
**Type**: Demo webapp (minimal viable product)

---

## Overview

Basic Flask webapp that accepts keywords, runs pipeline with two configs (UMLSPubTator, FullHybrid), displays generated PubMed query strings side-by-side.

**Not production** - demo/POC only.

---

## Requirements

### Functional
- Input field: comma/plus-separated keywords (e.g., "TMS, stroke, memory")
- Run both configs in parallel
- Display two query strings (UMLSPubTator vs FullHybrid)
- Show disambiguation metadata (which source resolved abbreviations)
- Basic error handling (missing UMLS_API_KEY, API failures)

### Non-Functional
- Single-page app (no navigation)
- No authentication needed
- No persistence (stateless)
- Response time: <10s for typical queries
- Local development only initially

---

## Architecture

### Tech Stack
- **Backend**: Flask 3.x
- **Frontend**: Jinja2 templates + minimal CSS (no framework)
- **Pipeline**: Existing `poc_api_first/` code
- **Dependencies**: flask, python-dotenv (already have others)

### Request Flow
```
User Input → Flask Route → Config.run() → Display Results
                ↓
          Parse keywords
                ↓
      [Parallel] UMLSPubTator.run() + FullHybrid.run()
                ↓
        Extract 'query' field from each
                ↓
         Render comparison template
```

---

## File Structure

```
poc_api_first/
├── webapp/
│   ├── __init__.py
│   ├── app.py              # Flask app + routes
│   ├── templates/
│   │   ├── index.html      # Input form
│   │   └── results.html    # Query comparison
│   └── static/
│       └── style.css       # Minimal styling
└── requirements.txt        # Add flask
```

---

## Implementation Details

### 1. Flask App (`webapp/app.py`)

```python
from flask import Flask, render_template, request, jsonify
import os
from pathlib import Path
from dotenv import load_dotenv
import sys

# Add parent dir to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from poc_api_first.tests.test_configurations import UMLSPubTatorConfig, FullHybridConfig

# Load .env
load_dotenv(Path(__file__).parent.parent.parent / '.env')

app = Flask(__name__)

@app.route('/')
def index():
    """Render input form."""
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    """Generate queries from both configs."""
    keywords = request.form.get('keywords', '').strip()

    if not keywords:
        return render_template('results.html', error="No keywords provided")

    # Check UMLS_API_KEY
    if not os.getenv('UMLS_API_KEY'):
        return render_template('results.html',
            error="UMLS_API_KEY not set. Check .env file.")

    try:
        # Init configs
        umls_pubtator = UMLSPubTatorConfig()
        full_hybrid = FullHybridConfig()

        # Run both (sequential for simplicity - parallel not critical for demo)
        result_1 = umls_pubtator.run(keywords, days=60, max_results=5, verbose=False)
        result_2 = full_hybrid.run(keywords, days=60, max_results=5, verbose=False)

        # Extract data
        return render_template('results.html',
            keywords=keywords,
            umls_query=result_1.get('query', 'N/A'),
            umls_terms=result_1.get('terms', []),
            umls_classifications=result_1.get('classifications', []),
            umls_count=result_1.get('result_count', 0),
            hybrid_query=result_2.get('query', 'N/A'),
            hybrid_terms=result_2.get('terms', []),
            hybrid_classifications=result_2.get('classifications', []),
            hybrid_count=result_2.get('result_count', 0)
        )

    except Exception as e:
        return render_template('results.html',
            error=f"Pipeline error: {str(e)}")

if __name__ == '__main__':
    # Development server only
    app.run(debug=True, host='127.0.0.1', port=5000)
```

### 2. Input Form (`templates/index.html`)

```html
<!DOCTYPE html>
<html>
<head>
    <title>NeuroDB Query Generator</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
</head>
<body>
    <div class="container">
        <h1>PubMed Query Generator</h1>
        <p>Enter neuroscience keywords separated by commas or plus signs</p>

        <form method="POST" action="/generate">
            <input type="text" name="keywords" placeholder="e.g., TMS, stroke, memory" required autofocus>
            <button type="submit">Generate Queries</button>
        </form>

        <div class="info">
            <h3>Configurations Tested:</h3>
            <ul>
                <li><strong>UMLS+PubTator</strong>: UMLS semantic classification + PubTator abbreviation expansion</li>
                <li><strong>Full Hybrid</strong>: UMLS + PubTator + NeuroDB-2 (neuroscience-specific)</li>
            </ul>
        </div>
    </div>
</body>
</html>
```

### 3. Results Display (`templates/results.html`)

```html
<!DOCTYPE html>
<html>
<head>
    <title>Query Results</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
</head>
<body>
    <div class="container">
        <h1>Query Results</h1>

        {% if error %}
        <div class="error">{{ error }}</div>
        <a href="/">← Back</a>
        {% else %}

        <div class="input-summary">
            <strong>Keywords:</strong> {{ keywords }}
        </div>

        <div class="comparison">
            <!-- UMLS+PubTator -->
            <div class="config-result">
                <h2>UMLS + PubTator</h2>
                <div class="query-box">
                    <strong>PubMed Query:</strong>
                    <pre>{{ umls_query }}</pre>
                </div>
                <p>Results: {{ umls_count }} articles</p>

                <details>
                    <summary>Classification Details</summary>
                    <ul>
                    {% for cls in umls_classifications %}
                        <li>
                            <strong>{{ cls.original_term }}</strong> → {{ cls.category }}
                            <br><small>Source: {{ cls.disambiguation_source }}, Confidence: {{ "%.2f"|format(cls.confidence) }}</small>
                        </li>
                    {% endfor %}
                    </ul>
                </details>
            </div>

            <!-- Full Hybrid -->
            <div class="config-result">
                <h2>Full Hybrid (+ NeuroDB)</h2>
                <div class="query-box">
                    <strong>PubMed Query:</strong>
                    <pre>{{ hybrid_query }}</pre>
                </div>
                <p>Results: {{ hybrid_count }} articles</p>

                <details>
                    <summary>Classification Details</summary>
                    <ul>
                    {% for cls in hybrid_classifications %}
                        <li>
                            <strong>{{ cls.original_term }}</strong> → {{ cls.category }}
                            <br><small>Source: {{ cls.disambiguation_source }}, Confidence: {{ "%.2f"|format(cls.confidence) }}</small>
                        </li>
                    {% endfor %}
                    </ul>
                </details>
            </div>
        </div>

        <a href="/">← Try Another Query</a>
        {% endif %}
    </div>
</body>
</html>
```

### 4. Styling (`static/style.css`)

```css
* { box-sizing: border-box; }

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
    background: #f5f5f5;
}

.container {
    background: white;
    padding: 30px;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

h1 { color: #2c3e50; margin-top: 0; }
h2 { color: #34495e; }

input[type="text"] {
    width: 100%;
    padding: 12px;
    font-size: 16px;
    border: 2px solid #ddd;
    border-radius: 4px;
    margin: 10px 0;
}

button {
    background: #3498db;
    color: white;
    padding: 12px 30px;
    border: none;
    border-radius: 4px;
    font-size: 16px;
    cursor: pointer;
}

button:hover { background: #2980b9; }

.comparison {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
    margin-top: 20px;
}

.config-result {
    border: 1px solid #ddd;
    padding: 15px;
    border-radius: 4px;
}

.query-box {
    background: #f8f9fa;
    padding: 15px;
    border-left: 3px solid #3498db;
    margin: 10px 0;
}

.query-box pre {
    white-space: pre-wrap;
    word-break: break-word;
    margin: 10px 0 0 0;
    font-size: 13px;
}

.error {
    background: #fee;
    border: 1px solid #fcc;
    padding: 15px;
    border-radius: 4px;
    color: #c33;
}

.info {
    background: #e8f4f8;
    padding: 15px;
    border-radius: 4px;
    margin-top: 20px;
}

details { margin-top: 10px; }
details summary { cursor: pointer; color: #3498db; }
details ul { margin: 10px 0; }
details li { margin: 5px 0; font-size: 14px; }
```

---

## Dependencies

Add to `requirements.txt`:
```
Flask==3.0.0
python-dotenv==1.0.0
# (existing deps already listed)
```

---

## Setup & Running

### Installation
```bash
cd /Users/sam/NeuroDB-2/poc_api_first
pip install flask
```

### Environment
Ensure `.env` file exists in project root with:
```
UMLS_API_KEY=your_key_here
```

### Launch
```bash
cd /Users/sam/NeuroDB-2/poc_api_first/webapp
python app.py
```

Visit: `http://127.0.0.1:5000`

---

## Testing Approach

### Manual Tests
1. **Basic query**: "TMS, stroke, memory"
   - Verify both queries generated
   - Check disambiguation sources differ between configs

2. **Abbreviation-heavy**: "MS, fMRI, DBS"
   - Verify NeuroDB used for FullHybrid
   - Check PubTator used for UMLSPubTator

3. **Error cases**:
   - Empty input → error message
   - Missing UMLS_API_KEY → clear error
   - API timeout → graceful failure

### Future Tests
- Load testing (not needed for demo)
- Unit tests for route handlers
- Integration tests with mock API responses

---

## Performance Considerations

### Current Approach (Sequential)
- UMLSPubTator.run(): ~3-5s
- FullHybrid.run(): ~3-5s
- Total: ~6-10s per request

**Acceptable for demo** - parallel execution would save ~3s but adds complexity.

### If Needed Later
Use `ThreadPoolExecutor` to run configs in parallel:
```python
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=2) as executor:
    future_1 = executor.submit(umls_pubtator.run, keywords, 60, 5, False)
    future_2 = executor.submit(full_hybrid.run, keywords, 60, 5, False)
    result_1 = future_1.result()
    result_2 = future_2.result()
```

---

## Security Considerations

### Current (Demo)
- Local development only
- No user data stored
- UMLS_API_KEY in .env (not committed)
- No authentication required

### Before Production
- Add rate limiting (flask-limiter)
- Input sanitization (prevent injection)
- HTTPS required
- API key rotation
- User authentication if needed
- CORS configuration
- Logging for monitoring

---

## Deployment (Future)

Not in scope for this plan, but options:
- **Local only**: Current setup sufficient
- **Internal network**: Use gunicorn + nginx
- **Cloud**: Deploy to Heroku/Railway/Render
- **Container**: Dockerize for portability

---

## Files to Create

```
/Users/sam/NeuroDB-2/poc_api_first/webapp/
├── __init__.py                    # Empty file
├── app.py                         # Flask app (above)
├── templates/
│   ├── index.html                 # Input form (above)
│   └── results.html               # Results display (above)
└── static/
    └── style.css                  # Styling (above)
```

---

---

## Phase 2: PubMed Article Results Display

### Overview

Extend results page to show actual PubMed articles found by each config. Side-by-side comparison highlights which articles unique to each approach.

**Goal**: Demonstrate real-world impact of different disambiguation strategies on retrieval results.

### Requirements

1. Display first 10 articles per config (limit for readability)
2. Show: title, authors (first 3), PMID, abstract snippet (150 chars), journal
3. Highlight differences: articles in one config but not other
4. Link to PubMed for each article

### Data Already Available

Pipeline `run()` returns `articles` array with:
- `pmid`: PubMed ID
- `title`: Article title
- `authors`: List of author names
- `abstract`: Full abstract text
- `pub_date`: Publication date
- `journal`: Journal name

**No additional API calls needed** - data already fetched.

### UI Design

#### Results Page Structure

```
+--------------------------------------------------+
| Keywords: TMS, stroke, memory                    |
+--------------------------------------------------+

+------------------------+------------------------+
| UMLS + PubTator        | Full Hybrid (NeuroDB)  |
+------------------------+------------------------+
| Query: ...             | Query: ...             |
| 47 results             | 52 results             |
+------------------------+------------------------+
| Articles (showing 10)  | Articles (showing 10)  |
|                        |                        |
| [Article card 1]       | [Article card 1]       |
| [Article card 2]       | [Article card 2]       |
| ...                    | ...                    |
+------------------------+------------------------+

Legend: [Unique to this config] [In both configs]
```

#### Article Card Layout

```
+------------------------------------------+
| [Title in blue, clickable link to PMID]  |
| Authors: Smith JA, Jones BC, et al.      |
| Journal • 2024 Nov • PMID: 39485372      |
| Abstract: First 150 chars of abstract... |
| [Badge: unique/common]                   |
+------------------------------------------+
```

### Implementation Changes

#### 1. Update `app.py` Route

```python
@app.route('/generate', methods=['POST'])
def generate():
    # ... existing code ...

    # Extract articles (limit to 10 for display)
    umls_articles = result_1.get('articles', [])[:10]
    hybrid_articles = result_2.get('articles', [])[:10]

    # Compute set differences for highlighting
    umls_pmids = {art['pmid'] for art in umls_articles}
    hybrid_pmids = {art['pmid'] for art in hybrid_articles}

    # Mark articles as unique or common
    for art in umls_articles:
        art['is_unique'] = art['pmid'] not in hybrid_pmids

    for art in hybrid_articles:
        art['is_unique'] = art['pmid'] not in umls_pmids

    return render_template('results.html',
        # ... existing vars ...
        umls_articles=umls_articles,
        hybrid_articles=hybrid_articles
    )
```

#### 2. Update `results.html` Template

Add article display section after query boxes:

```html
<!-- After classification details, before back link -->

<div class="articles-section">
    <h3>Article Comparison (first 10 results)</h3>

    <div class="legend">
        <span class="badge unique">Unique to this config</span>
        <span class="badge common">Found by both</span>
    </div>

    <div class="articles-comparison">
        <!-- UMLS Articles -->
        <div class="articles-column">
            <h4>UMLS + PubTator Articles</h4>
            {% if umls_articles %}
                {% for art in umls_articles %}
                <div class="article-card">
                    <h5>
                        <a href="https://pubmed.ncbi.nlm.nih.gov/{{ art.pmid }}" target="_blank">
                            {{ art.title }}
                        </a>
                    </h5>
                    <p class="meta">
                        <strong>Authors:</strong>
                        {% for author in art.authors[:3] %}
                            {{ author }}{% if not loop.last %}, {% endif %}
                        {% endfor %}
                        {% if art.authors|length > 3 %}et al.{% endif %}
                    </p>
                    <p class="meta">
                        {{ art.journal }} • {{ art.pub_date }} • PMID: {{ art.pmid }}
                    </p>
                    <p class="abstract-snippet">
                        {{ art.abstract[:150] }}{% if art.abstract|length > 150 %}...{% endif %}
                    </p>
                    <span class="badge {{ 'unique' if art.is_unique else 'common' }}">
                        {{ 'Unique' if art.is_unique else 'Common' }}
                    </span>
                </div>
                {% endfor %}
            {% else %}
                <p class="no-results">No articles returned</p>
            {% endif %}
        </div>

        <!-- Hybrid Articles -->
        <div class="articles-column">
            <h4>Full Hybrid Articles</h4>
            {% if hybrid_articles %}
                {% for art in hybrid_articles %}
                <div class="article-card">
                    <h5>
                        <a href="https://pubmed.ncbi.nlm.nih.gov/{{ art.pmid }}" target="_blank">
                            {{ art.title }}
                        </a>
                    </h5>
                    <p class="meta">
                        <strong>Authors:</strong>
                        {% for author in art.authors[:3] %}
                            {{ author }}{% if not loop.last %}, {% endif %}
                        {% endfor %}
                        {% if art.authors|length > 3 %}et al.{% endif %}
                    </p>
                    <p class="meta">
                        {{ art.journal }} • {{ art.pub_date }} • PMID: {{ art.pmid }}
                    </p>
                    <p class="abstract-snippet">
                        {{ art.abstract[:150] }}{% if art.abstract|length > 150 %}...{% endif %}
                    </p>
                    <span class="badge {{ 'unique' if art.is_unique else 'common' }}">
                        {{ 'Unique' if art.is_unique else 'Common' }}
                    </span>
                </div>
                {% endfor %}
            {% else %}
                <p class="no-results">No articles returned</p>
            {% endif %}
        </div>
    </div>
</div>
```

#### 3. Update `style.css`

Add article card styling:

```css
/* Article comparison section */
.articles-section {
    margin-top: 30px;
    padding-top: 20px;
    border-top: 2px solid #ddd;
}

.legend {
    text-align: center;
    margin: 15px 0;
    padding: 10px;
    background: #f9f9f9;
    border-radius: 4px;
}

.articles-comparison {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
    margin-top: 20px;
}

.articles-column h4 {
    color: #2c3e50;
    margin-bottom: 15px;
}

.article-card {
    background: #fafafa;
    border: 1px solid #e0e0e0;
    border-radius: 6px;
    padding: 15px;
    margin-bottom: 15px;
    position: relative;
}

.article-card h5 {
    margin: 0 0 10px 0;
    font-size: 15px;
    line-height: 1.4;
}

.article-card h5 a {
    color: #2563eb;
    text-decoration: none;
}

.article-card h5 a:hover {
    text-decoration: underline;
}

.article-card .meta {
    font-size: 13px;
    color: #666;
    margin: 5px 0;
}

.article-card .abstract-snippet {
    font-size: 13px;
    color: #444;
    line-height: 1.5;
    margin: 10px 0;
}

.badge {
    display: inline-block;
    padding: 4px 10px;
    border-radius: 12px;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
}

.badge.unique {
    background: #fef3c7;
    color: #92400e;
    border: 1px solid #fcd34d;
}

.badge.common {
    background: #dbeafe;
    color: #1e40af;
    border: 1px solid #93c5fd;
}

.no-results {
    color: #999;
    font-style: italic;
    padding: 20px;
    text-align: center;
}
```

### Performance Impact

- No additional API calls (data already fetched)
- Adds ~2-3KB per article to response (negligible)
- PMID set comparison: O(n) - instant for 10-20 articles
- Page rendering: <100ms additional

### Testing Scenarios

1. **Identical results**: Both configs find same 10 articles → all show "Common"
2. **Partial overlap**: Some unique to each → mixed badges
3. **Zero overlap**: Different articles → all show "Unique"
4. **Empty results**: One config returns 0 articles → "No articles returned"

### Files to Modify

```
/Users/sam/NeuroDB-2/poc_api_first/webapp/
├── app.py                    # Add PMID comparison logic
├── templates/
│   └── results.html          # Add article cards section
└── static/
    └── style.css             # Add article card styles
```

---

## Unresolved Questions (Updated)

1. ~~**Result count display**~~: ✅ Resolved - show both count and articles

2. **Caching**: Should repeated queries use cached results? (No - demo doesn't need this, adds complexity)

3. **Query validation**: Pre-validate keywords before running pipeline? (No - let pipeline handle errors naturally)

4. ~~**Multi-page results**~~: ✅ Resolved - limit to 10 per config for readability

5. **Export functionality**: Allow downloading query strings as text file? (Nice-to-have, not critical for MVP)

6. **Phase 2 specific**: Should clicking article card expand abstract in-page or only link to PubMed? (Plan uses PubMed link only - simpler)
# Flask Webapp Phase 3: Wider Configuration Scope

**Date**: 2025-12-03
**Status**: Planning (extends Phase 1+2)
**Base Plan**: `/Users/sam/NeuroDB-2/plans/251203-flask-webapp-plan.md`

---

## Overview

Extend webapp to support 5 configuration profiles with user-selectable comparison. Enables A/B/C/D/E testing of disambiguation strategies in single interface.

**Key Change**: From fixed 2-column layout → dynamic N-column layout (user selects which configs)

---

## New Configurations

### 1. NeuroDB-Only Config
```python
class NeuroDBOnlyConfig:
    """
    Single-layer: Only NeuroDB abbreviation lookup (no UMLS classification, no PubTator)

    Flow:
    - Abbreviation detected → NeuroDB lookup
    - Match found → use expanded term directly (no UMLS classification)
    - No match → use original term as-is

    Fallback: Original term (UNKNOWN category, no classification)
    """
    name = "NeuroDBOnly"
    use_neurodb = True
    use_umls = False
    use_pubtator = False
```

**Implementation Notes**:
- Reuse `FullHybridConfig.abbreviations` dict (already loads NeuroDB)
- Skip UMLS client initialization (save API quota)
- Return minimal classification dict: `{'term': resolved, 'category': 'UNKNOWN', 'confidence': 0.8}`
- Pipeline builds query without semantic categories (all terms treated equally)

---

### 2. UMLS-Only Config
```python
class UMLSOnlyConfig:
    """
    Single-layer: Only UMLS semantic classification (no abbreviation expansion)

    Flow:
    - All terms → UMLS direct lookup
    - No PubTator disambiguation
    - No NeuroDB expansion

    Limitation: Abbreviations may fail UMLS lookup (e.g., "MS" → no CUI found)
    """
    name = "UMLSOnly"
    use_neurodb = False
    use_umls = True
    use_pubtator = False
```

**Implementation Notes**:
- Reuse `UMLSClient.classify_term()` directly
- Set `disambiguation_source = 'UMLS_direct'`
- Abbreviations likely return empty/low-confidence results
- Good baseline to show value of disambiguation layers

---

### 3. PubTator-Only Config
```python
class PubTatorOnlyConfig:
    """
    Single-layer: Only PubTator disambiguation (no UMLS classification)

    Flow:
    - Abbreviation detected → PubTator autocomplete
    - Match found → use expanded term
    - No semantic classification

    Fallback: Original term (UNKNOWN category)
    """
    name = "PubTatorOnly"
    use_neurodb = False
    use_umls = False
    use_pubtator = True
```

**Implementation Notes**:
- Reuse `PubTatorClient.disambiguate_term()`
- Return resolved term without UMLS classification
- Good for comparing PubTator vs NeuroDB disambiguation quality

---

### 4. Keep Existing: UMLSPubTator (2-layer)
Already implemented in `test_configurations.py`

---

### 5. Keep Existing: FullHybrid (3-layer)
Already implemented in `test_configurations.py`

---

## Config Factory Pattern

Create factory to avoid code duplication:

```python
# poc_api_first/tests/test_configurations.py

class ConfigFactory:
    """Factory for creating pipeline configurations."""

    @staticmethod
    def create(config_name: str):
        """
        Create configuration by name.

        Args:
            config_name: One of: neurodb_only, umls_only, pubtator_only,
                        umls_pubtator, full_hybrid

        Returns:
            Config instance with run() method
        """
        configs = {
            'neurodb_only': NeuroDBOnlyConfig,
            'umls_only': UMLSOnlyConfig,
            'pubtator_only': PubTatorOnlyConfig,
            'umls_pubtator': UMLSPubTatorConfig,
            'full_hybrid': FullHybridConfig
        }

        if config_name not in configs:
            raise ValueError(f"Unknown config: {config_name}. Valid: {list(configs.keys())}")

        return configs[config_name]()

    @staticmethod
    def list_available() -> List[Dict[str, str]]:
        """Get list of available configs with descriptions."""
        return [
            {
                'id': 'neurodb_only',
                'name': 'NeuroDB Only',
                'description': 'Neuroscience abbreviations only (no classification)'
            },
            {
                'id': 'umls_only',
                'name': 'UMLS Only',
                'description': 'Semantic classification only (no disambiguation)'
            },
            {
                'id': 'pubtator_only',
                'name': 'PubTator Only',
                'description': 'Biomedical disambiguation only (no classification)'
            },
            {
                'id': 'umls_pubtator',
                'name': 'UMLS + PubTator',
                'description': 'Semantic classification + biomedical disambiguation'
            },
            {
                'id': 'full_hybrid',
                'name': 'Full Hybrid',
                'description': 'All layers: NeuroDB + PubTator + UMLS'
            }
        ]
```

---

## UI Changes

### Input Form (`index.html`)

Add config selection checkboxes:

```html
<form method="POST" action="/generate">
    <label for="keywords">Keywords:</label>
    <input type="text" name="keywords" id="keywords"
           placeholder="e.g., TMS, stroke, memory" required autofocus>

    <fieldset class="config-selector">
        <legend>Select Configurations to Compare (2-5):</legend>

        <label class="checkbox-label">
            <input type="checkbox" name="configs" value="neurodb_only">
            <strong>NeuroDB Only</strong> - Neuroscience abbreviations
        </label>

        <label class="checkbox-label">
            <input type="checkbox" name="configs" value="umls_only">
            <strong>UMLS Only</strong> - Semantic classification
        </label>

        <label class="checkbox-label">
            <input type="checkbox" name="configs" value="pubtator_only">
            <strong>PubTator Only</strong> - Biomedical disambiguation
        </label>

        <label class="checkbox-label">
            <input type="checkbox" name="configs" value="umls_pubtator" checked>
            <strong>UMLS + PubTator</strong> - 2-layer (proven POC)
        </label>

        <label class="checkbox-label">
            <input type="checkbox" name="configs" value="full_hybrid" checked>
            <strong>Full Hybrid</strong> - 3-layer (NeuroDB + PubTator + UMLS)
        </label>
    </fieldset>

    <button type="submit">Generate Queries</button>
</form>

<script>
// Validate: require 2-5 selections
document.querySelector('form').addEventListener('submit', function(e) {
    const checked = document.querySelectorAll('input[name="configs"]:checked');
    if (checked.length < 2) {
        e.preventDefault();
        alert('Please select at least 2 configurations to compare');
    } else if (checked.length > 5) {
        e.preventDefault();
        alert('Please select no more than 5 configurations');
    }
});
</script>
```

**CSS for checkboxes** (`style.css`):
```css
.config-selector {
    border: 1px solid #ddd;
    padding: 15px;
    border-radius: 4px;
    margin: 15px 0;
}

.config-selector legend {
    font-weight: 600;
    color: #2c3e50;
    padding: 0 10px;
}

.checkbox-label {
    display: block;
    padding: 8px 0;
    cursor: pointer;
}

.checkbox-label input {
    margin-right: 10px;
    cursor: pointer;
}

.checkbox-label:hover {
    background: #f5f5f5;
}
```

---

### Results Display (`results.html`)

Dynamic column grid:

```html
<div class="input-summary">
    <strong>Keywords:</strong> {{ keywords }}
    <br>
    <strong>Comparing:</strong> {{ selected_configs|length }} configurations
</div>

<!-- Dynamic grid: 2-5 columns based on selection -->
<div class="comparison" data-cols="{{ selected_configs|length }}">
    {% for config_id, result in results.items() %}
    <div class="config-result">
        <h2>{{ config_names[config_id] }}</h2>

        <div class="query-box">
            <strong>PubMed Query:</strong>
            <pre>{{ result.query }}</pre>
        </div>

        <p>Results: {{ result.result_count }} articles</p>

        <!-- Classification details (collapsible) -->
        <details>
            <summary>Classification Details</summary>
            <ul>
            {% for cls in result.classifications %}
                <li>
                    <strong>{{ cls.original_term }}</strong> → {{ cls.category }}
                    <br><small>Source: {{ cls.disambiguation_source }},
                              Confidence: {{ "%.2f"|format(cls.confidence) }}</small>
                </li>
            {% endfor %}
            </ul>
        </details>

        <!-- Article cards (Phase 2) -->
        <div class="articles">
            {% for art in result.articles[:10] %}
            <div class="article-card">
                <!-- Same structure as Phase 2 -->
            </div>
            {% endfor %}
        </div>
    </div>
    {% endfor %}
</div>
```

**Responsive grid CSS**:
```css
/* Dynamic grid based on selection count */
.comparison {
    display: grid;
    gap: 20px;
    margin-top: 20px;
}

.comparison[data-cols="2"] { grid-template-columns: 1fr 1fr; }
.comparison[data-cols="3"] { grid-template-columns: repeat(3, 1fr); }
.comparison[data-cols="4"] { grid-template-columns: repeat(2, 1fr); } /* 2x2 grid */
.comparison[data-cols="5"] { grid-template-columns: repeat(3, 1fr); } /* 3+2 grid */

/* Responsive breakpoint */
@media (max-width: 1024px) {
    .comparison[data-cols="3"],
    .comparison[data-cols="4"],
    .comparison[data-cols="5"] {
        grid-template-columns: 1fr 1fr; /* 2 cols on smaller screens */
    }
}

@media (max-width: 768px) {
    .comparison {
        grid-template-columns: 1fr !important; /* Single column on mobile */
    }
}
```

---

## Backend Changes

### Route Handler (`webapp/app.py`)

```python
from concurrent.futures import ThreadPoolExecutor, as_completed
from poc_api_first.tests.test_configurations import ConfigFactory

@app.route('/generate', methods=['POST'])
def generate():
    keywords = request.form.get('keywords', '').strip()
    selected_configs = request.form.getlist('configs')  # List of config IDs

    # Validation
    if not keywords:
        return render_template('results.html', error="No keywords provided")

    if not selected_configs:
        return render_template('results.html',
            error="No configurations selected. Please select at least 2.")

    if len(selected_configs) < 2 or len(selected_configs) > 5:
        return render_template('results.html',
            error=f"Invalid selection: {len(selected_configs)} configs. Choose 2-5.")

    # Check UMLS_API_KEY (needed for configs with UMLS)
    if not os.getenv('UMLS_API_KEY'):
        umls_configs = {'umls_only', 'umls_pubtator', 'full_hybrid'}
        if any(c in umls_configs for c in selected_configs):
            return render_template('results.html',
                error="UMLS_API_KEY not set. Required for UMLS-based configs.")

    try:
        # Parallel execution of selected configs
        results = {}
        config_names = {}

        with ThreadPoolExecutor(max_workers=len(selected_configs)) as executor:
            # Submit all jobs
            futures = {}
            for config_id in selected_configs:
                config = ConfigFactory.create(config_id)
                config_names[config_id] = config.name
                future = executor.submit(
                    config.run,
                    keywords,
                    days=60,
                    max_results=10,  # Limit for performance
                    verbose=False
                )
                futures[future] = config_id

            # Collect results as they complete
            for future in as_completed(futures):
                config_id = futures[future]
                try:
                    results[config_id] = future.result()
                except Exception as e:
                    # Partial failure handling
                    results[config_id] = {
                        'query': 'ERROR',
                        'result_count': 0,
                        'articles': [],
                        'classifications': [],
                        'error': str(e)
                    }

        # Compute article overlaps (for highlighting)
        all_pmids = {}
        for config_id, result in results.items():
            pmids = {art['pmid'] for art in result.get('articles', [])[:10]}
            all_pmids[config_id] = pmids

        # Mark unique articles
        for config_id, result in results.items():
            for art in result.get('articles', [])[:10]:
                pmid = art['pmid']
                # Unique = only in this config
                other_configs = [cid for cid in selected_configs if cid != config_id]
                art['is_unique'] = not any(pmid in all_pmids[cid] for cid in other_configs)

        return render_template('results.html',
            keywords=keywords,
            selected_configs=selected_configs,
            results=results,
            config_names=config_names
        )

    except Exception as e:
        return render_template('results.html',
            error=f"Pipeline error: {str(e)}")
```

---

## Error Handling

### Config-Level Fallbacks

Each single-layer config needs graceful degradation:

**NeuroDB-Only**:
- Abbreviation not in database → use original term
- Return: `{'term': original, 'category': 'UNKNOWN', 'confidence': 0.3}`

**UMLS-Only**:
- No CUI found → return UNKNOWN
- Abbreviation fails lookup → return original term unchanged
- Return: `{'term': original, 'category': 'UNKNOWN', 'confidence': 0.3}`

**PubTator-Only**:
- Autocomplete returns empty → use original term
- Return: `{'term': original, 'category': 'UNKNOWN', 'confidence': 0.3}`

**UI Display**: Show "fallback used" badge in classification details

---

## Performance Optimization

### Parallel Execution
- **Current (Phase 1+2)**: Sequential execution (~6-10s total)
- **Phase 3**: Parallel with `ThreadPoolExecutor` (~3-5s total)
- **Max workers**: Same as config count (2-5 threads)

### API Rate Limiting
- Only UMLS-based configs consume API quota
- PubTator has no key requirement
- NeuroDB is local (no API)

**Resource Usage Matrix**:
```
Config          | UMLS API | PubTator API | NeuroDB File
----------------|----------|--------------|-------------
NeuroDB Only    |    ✗     |      ✗       |      ✓
UMLS Only       |    ✓     |      ✗       |      ✗
PubTator Only   |    ✗     |      ✓       |      ✗
UMLS+PubTator   |    ✓     |      ✓       |      ✗
Full Hybrid     |    ✓     |      ✓       |      ✓
```

---

## Testing Strategy

### Test Cases

1. **2-config comparison** (minimal):
   - `umls_pubtator + full_hybrid`
   - Verify 2-column grid
   - Check article overlap highlighting

2. **5-config comparison** (maximal):
   - All configs selected
   - Verify 3+2 grid layout (5 columns)
   - Check performance (<10s total)

3. **Single-layer configs** (error paths):
   - `neurodb_only` with unknown abbreviation → verify fallback
   - `umls_only` with "MS" → verify low confidence/empty result
   - `pubtator_only` with rare term → verify fallback

4. **Partial failure**:
   - UMLS API timeout → other configs still display
   - One config crashes → show error in that column only

---

## Implementation Checklist

### New Files
- [ ] `poc_api_first/tests/test_configurations.py` - Add 3 new config classes
- [ ] `poc_api_first/tests/test_configurations.py` - Add `ConfigFactory`

### Modified Files
- [ ] `webapp/app.py` - Update route for multi-config selection + parallel execution
- [ ] `webapp/templates/index.html` - Add checkbox UI
- [ ] `webapp/templates/results.html` - Dynamic grid layout
- [ ] `webapp/static/style.css` - Grid responsive styles + checkbox styles

### Testing
- [ ] Manual: Test all 5 configs individually
- [ ] Manual: Test 2-config, 3-config, 5-config comparisons
- [ ] Manual: Verify fallback behavior for each single-layer config
- [ ] Manual: Test partial failures (kill UMLS API mid-request)

---

## Files to Modify

```
/Users/sam/NeuroDB-2/poc_api_first/
├── tests/
│   └── test_configurations.py      # Add: NeuroDBOnlyConfig, UMLSOnlyConfig,
│                                    #      PubTatorOnlyConfig, ConfigFactory
├── webapp/
│   ├── app.py                       # Update: parallel execution, dynamic results
│   ├── templates/
│   │   ├── index.html              # Add: checkbox config selector
│   │   └── results.html            # Update: dynamic N-column grid
│   └── static/
│       └── style.css               # Add: responsive grid, checkbox styles
```

---

## Data Flow Changes

### Phase 1+2 Flow
```
User → 2 fixed configs → Sequential execution → 2-column display
```

### Phase 3 Flow
```
User → Select N configs (2-5) → Parallel execution → N-column display
      ↓
   Checkbox validation
      ↓
   ThreadPoolExecutor (N workers)
      ↓
   Collect results + compute overlaps
      ↓
   Responsive grid (2-5 columns)
```

---

## Unresolved Questions

1. **Config naming**: Should UI use full names ("Full Hybrid") or show layer counts ("3-Layer")?
   - **Recommendation**: Use descriptive names (easier for users to understand capabilities)

2. **Default selections**: Which configs checked by default?
   - **Recommendation**: `umls_pubtator + full_hybrid` (proven baselines for comparison)

3. **Performance warning**: Show warning if user selects 5 configs + large keyword list?
   - **Recommendation**: Add client-side validation (limit keywords to 5 if 5 configs selected)

4. **Article overlap logic**: With 5 configs, "unique" means "only in this config" or "in minority"?
   - **Recommendation**: Strict unique (only in 1 config) - simpler to understand

5. **Fallback display**: Show fallback indicator in UI when term unresolved?
   - **Recommendation**: Add small badge "⚠️ Fallback" next to UNKNOWN categories
