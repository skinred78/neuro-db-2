"""
Schema mapping utilities for NeuroDB-2 ontology imports.

Maps external ontology formats to the extended 26-column NeuroDB-2 schema.
"""

# Extended NeuroDB-2 schema (22 standard + 4 metadata columns)
NEURODB_SCHEMA = [
    'Term',
    'Term Two',
    'Definition',
    'Closest MeSH term',
    'Synonym 1',
    'Synonym 2',
    'Synonym 3',
    'Abbreviation',
    'UK Spelling',
    'US Spelling',
    'Noun Form of Word',
    'Verb Form of Word',
    'Adjective Form of Word',
    'Adverb Form of Word',
    'Commonly Associated Term 1',
    'Commonly Associated Term 2',
    'Commonly Associated Term 3',
    'Commonly Associated Term 4',
    'Commonly Associated Term 5',
    'Commonly Associated Term 6',
    'Commonly Associated Term 7',
    'Commonly Associated Term 8',
    'source',
    'source_priority',
    'sources_contributing',
    'date_added'
]


def create_empty_row():
    """
    Creates an empty row with all 26 columns initialized to empty strings.

    Returns:
        dict: Dictionary with all NEURODB_SCHEMA columns set to ''
    """
    return {col: '' for col in NEURODB_SCHEMA}


def map_neuronames_to_schema(entry):
    """
    Maps Neuronames JSON entry to NeuroDB-2 schema.

    Neuronames provides:
    - Preferred name (Term)
    - Synonyms (multiple alternative names)
    - Definition (description)
    - Possibly abbreviations

    Args:
        entry (dict): Neuronames JSON entry

    Returns:
        dict: Row mapped to NEURODB_SCHEMA
    """
    row = create_empty_row()

    # Core fields
    row['Term'] = entry.get('preferred_name', '').strip()
    row['Definition'] = entry.get('definition', '').strip()

    # Synonyms (Neuronames may have multiple alternative names)
    synonyms = entry.get('synonyms', [])
    if isinstance(synonyms, list):
        for i, syn in enumerate(synonyms[:3]):  # Max 3 synonyms
            row[f'Synonym {i+1}'] = syn.strip()
    elif isinstance(synonyms, str) and synonyms:
        row['Synonym 1'] = synonyms.strip()

    # Abbreviations (if present)
    abbrev = entry.get('abbreviation', '').strip()
    if abbrev:
        row['Abbreviation'] = abbrev

    # Associated terms (related concepts, parent/child structures)
    related = entry.get('related_terms', [])
    if isinstance(related, list):
        for i, term in enumerate(related[:8]):  # Max 8 associated terms
            row[f'Commonly Associated Term {i+1}'] = term.strip()

    # Leave MeSH term empty (will be populated by mesh-validator later)
    # Leave word forms empty (Neuronames is neuroanatomy, not linguistic data)
    # Leave UK/US spelling empty (not applicable for anatomical terms)

    return row


def map_nif_to_schema(entry):
    """
    Maps NIF/NIFSTD OWL entry to NeuroDB-2 schema.

    NIF provides rich semantic data including definitions, synonyms, and relationships.

    Args:
        entry (dict): Parsed NIF OWL entry

    Returns:
        dict: Row mapped to NEURODB_SCHEMA
    """
    row = create_empty_row()

    # Core fields
    row['Term'] = entry.get('label', '').strip()
    row['Definition'] = entry.get('definition', '').strip()

    # Synonyms (NIF has extensive synonym data)
    synonyms = entry.get('hasExactSynonym', []) + entry.get('hasRelatedSynonym', [])
    for i, syn in enumerate(synonyms[:3]):
        row[f'Synonym {i+1}'] = syn.strip()

    # Abbreviations
    abbrevs = entry.get('hasAbbreviation', [])
    if abbrevs:
        row['Abbreviation'] = abbrevs[0].strip()

    # Associated terms (broader/narrower/related concepts)
    related = (entry.get('broader', []) +
               entry.get('narrower', []) +
               entry.get('related', []))
    for i, term in enumerate(related[:8]):
        row[f'Commonly Associated Term {i+1}'] = term.strip()

    return row


def map_go_to_schema(entry):
    """
    Maps Gene Ontology (GO) OBO entry to NeuroDB-2 schema.

    GO provides standardized gene/protein function descriptions.

    Args:
        entry (dict): Parsed GO OBO entry

    Returns:
        dict: Row mapped to NEURODB_SCHEMA
    """
    row = create_empty_row()

    # Core fields
    row['Term'] = entry.get('name', '').strip()
    row['Definition'] = entry.get('def', '').strip()

    # Synonyms (GO has exact/broad/narrow/related synonyms)
    synonyms = entry.get('synonym', [])
    for i, syn in enumerate(synonyms[:3]):
        # GO synonyms format: "text" EXACT|BROAD|NARROW|RELATED []
        # Extract just the quoted text
        if '"' in syn:
            syn_text = syn.split('"')[1]
            row[f'Synonym {i+1}'] = syn_text.strip()

    # Associated terms (is_a, part_of relationships)
    related = entry.get('is_a', []) + entry.get('relationship', [])
    for i, term in enumerate(related[:8]):
        row[f'Commonly Associated Term {i+1}'] = term.strip()

    return row


def map_umls_to_schema(entry):
    """
    Maps UMLS Metathesaurus RRF entry to NeuroDB-2 schema.

    UMLS provides comprehensive medical terminology with extensive cross-references.

    Args:
        entry (dict): Parsed UMLS RRF entry (from MRCONSO.RRF + MRDEF.RRF)

    Returns:
        dict: Row mapped to NEURODB_SCHEMA
    """
    row = create_empty_row()

    # Core fields
    row['Term'] = entry.get('preferred_term', '').strip()
    row['Definition'] = entry.get('definition', '').strip()

    # Synonyms (UMLS has extensive synonym data from multiple sources)
    synonyms = entry.get('synonyms', [])
    for i, syn in enumerate(synonyms[:3]):
        row[f'Synonym {i+1}'] = syn.strip()

    # Abbreviations
    abbrevs = entry.get('abbreviations', [])
    if abbrevs:
        row['Abbreviation'] = abbrevs[0].strip()

    # MeSH term (UMLS cross-references to MeSH)
    mesh = entry.get('mesh_term', '').strip()
    if mesh:
        row['Closest MeSH term'] = mesh

    # Associated terms (related concepts, semantic relationships)
    related = entry.get('related_concepts', [])
    for i, term in enumerate(related[:8]):
        row[f'Commonly Associated Term {i+1}'] = term.strip()

    return row


def validate_row(row):
    """
    Validates that a row conforms to schema requirements.

    Args:
        row (dict): Row to validate

    Returns:
        tuple: (is_valid, error_message)
    """
    # Check all required columns present
    for col in NEURODB_SCHEMA:
        if col not in row:
            return False, f"Missing required column: {col}"

    # Check Term is non-empty
    if not row['Term'].strip():
        return False, "Term field cannot be empty"

    # Check Definition is non-empty
    if not row['Definition'].strip():
        return False, "Definition field cannot be empty"

    # Check source metadata is non-empty
    if not row['source'].strip():
        return False, "source field cannot be empty"

    if not row['source_priority'].strip():
        return False, "source_priority field cannot be empty"

    if not row['date_added'].strip():
        return False, "date_added field cannot be empty"

    return True, None
