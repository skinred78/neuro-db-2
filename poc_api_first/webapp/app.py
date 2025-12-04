"""
Flask webapp for Search Methodology Comparison.

PURPOSE: Side-by-side comparison of different search tool combinations to help
researchers identify optimal query expansion strategies for their domain.

CONFIGURATIONS:
- NeuroDB-Only: Local abbreviation DB (neuroscience-specific)
- UMLS-Only: Semantic classification only
- PubTator-Only: Biomedical disambiguation only
- UMLS+PubTator: 2-layer hybrid (disambiguation → classification)
- FullHybrid: 3-layer (NeuroDB → PubTator → UMLS)

USAGE: Select 2-5 configs, enter keywords, compare results side-by-side.
Each config shows: resolved terms, classifications, generated query, paper count.
"""

from flask import Flask, render_template, request
from pathlib import Path
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import sys

# Add parent dir to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from poc_api_first.tests.test_configurations import (
    NeuroDBOnlyConfig,
    UMLSOnlyConfig,
    PubTatorOnlyConfig,
    UMLSPubTatorConfig,
    FullHybridConfig
)

# Load .env from poc_api_first directory
load_dotenv(Path(__file__).parent.parent / '.env')

app = Flask(__name__)


# Configuration metadata for UI (ordered by complexity)
CONFIG_METADATA = {
    'neurodb_only': {
        'name': 'NeuroDB Only',
        'description': 'Neuroscience abbreviations only (no external APIs)',
        'class': NeuroDBOnlyConfig
    },
    'umls_only': {
        'name': 'UMLS Only',
        'description': 'Semantic classification only (no disambiguation)',
        'class': UMLSOnlyConfig
    },
    'pubtator_only': {
        'name': 'PubTator Only',
        'description': 'Biomedical disambiguation only (no classification)',
        'class': PubTatorOnlyConfig
    },
    'umls_pubtator': {
        'name': 'UMLS + PubTator',
        'description': 'Semantic classification + biomedical disambiguation',
        'class': UMLSPubTatorConfig
    },
    'full_hybrid': {
        'name': 'Full Hybrid',
        'description': 'All layers: NeuroDB + PubTator + UMLS',
        'class': FullHybridConfig
    }
}


@app.route('/healthz')
def healthz():
    """Health check endpoint for Cloud Run."""
    return 'OK', 200


@app.route('/')
def index():
    """Render input form with config selection."""
    configs = [
        {'id': cid, 'name': meta['name'], 'description': meta['description']}
        for cid, meta in CONFIG_METADATA.items()
    ]
    return render_template('index.html', configs=configs)


@app.route('/generate', methods=['POST'])
def generate():
    """Generate queries from selected configs."""
    keywords = request.form.get('keywords', '').strip()
    selected_configs = request.form.getlist('configs')

    # Default to all configs if none selected
    if not selected_configs:
        selected_configs = list(CONFIG_METADATA.keys())

    if not keywords:
        return render_template('results.html', error="No keywords provided")

    # Check UMLS_API_KEY
    if not os.getenv('UMLS_API_KEY'):
        return render_template('results.html',
            error="UMLS_API_KEY not set. Check .env file.")

    try:
        results = {}
        config_names = {}

        # Parallel execution
        with ThreadPoolExecutor(max_workers=len(selected_configs)) as executor:
            futures = {}
            for config_id in selected_configs:
                if config_id not in CONFIG_METADATA:
                    continue
                config = CONFIG_METADATA[config_id]['class']()
                config_names[config_id] = CONFIG_METADATA[config_id]['name']
                future = executor.submit(
                    config.run,
                    keywords,
                    days=60,
                    max_results=10,
                    verbose=False
                )
                futures[future] = config_id

            for future in as_completed(futures):
                config_id = futures[future]
                try:
                    results[config_id] = future.result()
                except Exception as e:
                    results[config_id] = {
                        'query': 'ERROR',
                        'result_count': 0,
                        'articles': [],
                        'classifications': [],
                        'error': str(e)
                    }

        # Compute article overlaps for highlighting
        all_pmids = {}
        for config_id, result in results.items():
            articles = result.get('articles', [])[:10]
            pmids = {str(art.get('pmid', '')) for art in articles if art.get('pmid')}
            all_pmids[config_id] = pmids

        # Mark unique articles
        for config_id, result in results.items():
            for art in result.get('articles', [])[:10]:
                pmid = str(art.get('pmid', ''))
                other_configs = [cid for cid in selected_configs if cid != config_id]
                art['is_unique'] = not any(pmid in all_pmids.get(cid, set()) for cid in other_configs)

        return render_template('results.html',
            keywords=keywords,
            selected_configs=selected_configs,
            results=results,
            config_names=config_names
        )

    except Exception as e:
        return render_template('results.html',
            error=f"Pipeline error: {str(e)}")


if __name__ == '__main__':
    app.run(debug=False, host='127.0.0.1', port=5000)
