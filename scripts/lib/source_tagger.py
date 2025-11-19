"""
Source tagging and metadata management for NeuroDB-2 ontology imports.

Handles source provenance tracking and multi-source conflict resolution.
"""

from datetime import datetime


# Source priority hierarchy (1 = highest quality/authority)
SOURCE_PRIORITIES = {
    'umls': 1,              # UMLS Metathesaurus - most comprehensive medical terminology
    'neuronames': 2,        # Curated neuroanatomy database
    'nif': 2,               # Neuroscience Information Framework - comprehensive
    'gene_ontology': 2,     # Gene Ontology - standardized gene/protein functions
    'wikipedia': 3,         # Community-edited, good coverage but lower authority
    'ninds': 3              # NINDS glossary - reliable but limited scope
}


def add_source_metadata(row, source_name):
    """
    Adds source metadata to a row.

    Populates the 4 metadata columns:
    - source: Primary source name
    - source_priority: Integer priority (1-3)
    - sources_contributing: Comma-separated list (initially just source_name)
    - date_added: ISO 8601 date (YYYY-MM-DD)

    Args:
        row (dict): Row to tag (will be modified in place)
        source_name (str): Source identifier (e.g., 'neuronames', 'umls')

    Returns:
        dict: The modified row (same object as input)

    Raises:
        ValueError: If source_name not in SOURCE_PRIORITIES
    """
    if source_name not in SOURCE_PRIORITIES:
        raise ValueError(
            f"Unknown source '{source_name}'. "
            f"Valid sources: {list(SOURCE_PRIORITIES.keys())}"
        )

    row['source'] = source_name
    row['source_priority'] = str(SOURCE_PRIORITIES[source_name])
    row['sources_contributing'] = source_name
    row['date_added'] = datetime.now().strftime('%Y-%m-%d')

    return row


def merge_sources(existing_row, new_row, strategy='priority'):
    """
    Merges data from two sources for the same term.

    Conflict resolution strategies:
    - 'priority': Higher priority source wins (based on SOURCE_PRIORITIES)
    - 'complement': Keep existing data, fill empty fields from new source
    - 'latest': Most recent source wins

    Args:
        existing_row (dict): Current row in database
        new_row (dict): New row from import
        strategy (str): Conflict resolution strategy

    Returns:
        dict: Merged row with updated sources_contributing
    """
    if strategy == 'priority':
        return _merge_by_priority(existing_row, new_row)
    elif strategy == 'complement':
        return _merge_by_complement(existing_row, new_row)
    elif strategy == 'latest':
        return _merge_by_latest(existing_row, new_row)
    else:
        raise ValueError(f"Unknown merge strategy: {strategy}")


def _merge_by_priority(existing_row, new_row):
    """Priority-based merge: Higher priority source wins conflicts."""
    existing_priority = int(existing_row.get('source_priority', 999))
    new_priority = int(new_row.get('source_priority', 999))

    if new_priority < existing_priority:
        # New source has higher priority, use it as base
        merged = new_row.copy()
        # But complement with existing data for empty fields
        for field in merged:
            if not merged[field] and existing_row.get(field):
                merged[field] = existing_row[field]
    else:
        # Existing source has higher/equal priority, keep as base
        merged = existing_row.copy()
        # Complement with new data for empty fields
        for field in merged:
            if not merged[field] and new_row.get(field):
                merged[field] = new_row[field]

    # Update sources_contributing
    existing_sources = set(existing_row.get('sources_contributing', '').split(','))
    new_sources = set(new_row.get('sources_contributing', '').split(','))
    all_sources = existing_sources | new_sources
    merged['sources_contributing'] = ','.join(sorted(all_sources))

    # Keep the higher priority source as primary
    if new_priority < existing_priority:
        merged['source'] = new_row['source']
        merged['source_priority'] = str(new_priority)

    return merged


def _merge_by_complement(existing_row, new_row):
    """Complement merge: Keep existing, fill empty fields from new source."""
    merged = existing_row.copy()

    # Fill empty fields with new data
    for field in merged:
        if not merged[field] and new_row.get(field):
            merged[field] = new_row[field]

    # Update sources_contributing
    existing_sources = set(existing_row.get('sources_contributing', '').split(','))
    new_sources = set(new_row.get('sources_contributing', '').split(','))
    all_sources = existing_sources | new_sources
    merged['sources_contributing'] = ','.join(sorted(all_sources))

    return merged


def _merge_by_latest(existing_row, new_row):
    """Latest merge: Most recent source wins."""
    existing_date = existing_row.get('date_added', '1970-01-01')
    new_date = new_row.get('date_added', datetime.now().strftime('%Y-%m-%d'))

    if new_date >= existing_date:
        # New source is more recent, use it as base
        merged = new_row.copy()
        # But complement with existing data for empty fields
        for field in merged:
            if not merged[field] and existing_row.get(field):
                merged[field] = existing_row[field]
    else:
        # Existing source is more recent, keep as base
        merged = existing_row.copy()
        # Complement with new data for empty fields
        for field in merged:
            if not merged[field] and new_row.get(field):
                merged[field] = new_row[field]

    # Update sources_contributing
    existing_sources = set(existing_row.get('sources_contributing', '').split(','))
    new_sources = set(new_row.get('sources_contributing', '').split(','))
    all_sources = existing_sources | new_sources
    merged['sources_contributing'] = ','.join(sorted(all_sources))

    return merged


def filter_by_sources(rows, enabled_sources):
    """
    Filters rows to only include those from enabled sources.

    Used for selective source testing (e.g., "UMLS only" vs "UMLS + Neuronames").

    Args:
        rows (list): List of row dicts
        enabled_sources (list): List of source names to include (e.g., ['umls', 'neuronames'])

    Returns:
        list: Filtered rows where sources_contributing intersects with enabled_sources
    """
    filtered = []

    for row in rows:
        contributing_sources = set(row.get('sources_contributing', '').split(','))
        enabled_set = set(enabled_sources)

        # Include row if ANY of its contributing sources are enabled
        if contributing_sources & enabled_set:
            filtered.append(row)

    return filtered


def get_source_stats(rows):
    """
    Generates statistics about source distribution in dataset.

    Args:
        rows (list): List of row dicts

    Returns:
        dict: Statistics including:
            - total_terms: Total number of terms
            - by_source: Count of terms by primary source
            - multi_source: Count of terms with multiple contributing sources
            - by_priority: Count of terms by priority level
    """
    stats = {
        'total_terms': len(rows),
        'by_source': {},
        'multi_source': 0,
        'by_priority': {1: 0, 2: 0, 3: 0}
    }

    for row in rows:
        # Count by primary source
        source = row.get('source', 'unknown')
        stats['by_source'][source] = stats['by_source'].get(source, 0) + 1

        # Count multi-source terms
        contributing = row.get('sources_contributing', '')
        if ',' in contributing:
            stats['multi_source'] += 1

        # Count by priority
        priority = int(row.get('source_priority', 3))
        if priority in stats['by_priority']:
            stats['by_priority'][priority] += 1

    return stats
