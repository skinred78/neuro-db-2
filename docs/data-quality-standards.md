# Data Quality Standards

**Last Updated**: 2025-11-07
**Applies To**: All NeuroDB-2 neuroscience terminology entries
**Enforcement**: Dual validation (mesh-validator + neuro-reviewer agents)

## Core Principles

### 1. Accuracy Over Completeness
**NEVER fabricate or guess information**
- Leave fields empty if no reliable data available
- Empty field is better than incorrect data
- Quality of existing data > quantity of fields filled
- Cite sources when adding information beyond Wikipedia glossary

### 2. Verifiability
**All data must be verifiable from authoritative sources**
- MeSH terms: NIH MeSH API (authoritative, no exceptions)
- Definitions: Wikipedia Glossary of Neuroscience (primary source)
- Synonyms: Cross-reference with neuroscience literature, textbooks
- Word forms: Standard English dictionaries, medical dictionaries
- Associated terms: Neuroscience domain knowledge, verified relationships

### 3. Consistency
**Maintain uniform data formats and standards across all entries**
- Use standardized column names (exact match required)
- Follow MeSH formatting rules (commas, hyphens, capitalization)
- Apply consistent rules for synonyms vs abbreviations
- Use uniform terminology for commonly associated terms

### 4. Traceability
**Document all changes and corrections**
- Log all MeSH corrections in 3 tracking files
- Archive validation reports with date stamps
- Maintain audit trail of data modifications
- Record rationale for empty fields or non-standard choices

## Field-Specific Standards

### Term (Primary)
**Purpose**: Main neuroscience term being defined

**Standards**:
- Use exact capitalization from Wikipedia Glossary source
- Preserve special characters (e.g., α, β, Greek letters)
- Do NOT abbreviate in this field
- Singular vs plural: Match source material

**Examples**:
- ✅ `"Alpha motor neuron"`
- ✅ `"γ-Aminobutyric acid"`
- ❌ `"alpha motor neuron"` (wrong capitalization)
- ❌ `"AMN"` (abbreviation, not full term)

### Term Two (Alternate Representation)
**Purpose**: ASCII-safe searchable version with special characters removed

**Standards**:
- ONLY use when Term contains special characters
- Remove special characters: `α` → `alpha`, `β` → `beta`
- NOT for synonyms or alternative names
- Leave empty if Term is already ASCII-safe

**Examples**:
- Term: `"α motor neuron"` → Term Two: `"alpha motor neuron"`
- Term: `"γ-Aminobutyric acid"` → Term Two: `"gamma-Aminobutyric acid"`
- Term: `"Neuron"` → Term Two: `` (empty, no special chars)

**NOT for**:
- ❌ Alternative names: `"Nerve cell"` (use Synonym field)
- ❌ Abbreviations: `"GABA"` (use Abbreviation field)
- ❌ Spelling variants: `"Neurone"` (use UK/US Spelling fields)

### Definition
**Purpose**: Complete, accurate definition from source material

**Standards**:
- Use Wikipedia Glossary definition verbatim (primary source)
- Preserve all commas, periods, scientific notation
- Properly quote if definition contains commas (CSV formatting)
- Do NOT abbreviate or summarize
- Do NOT add information not in source

**Quality Checks**:
- Complete sentences with proper punctuation
- Scientific accuracy (cross-validated by neuro-reviewer)
- No fabricated information
- Maintain technical precision

### Closest MeSH Term
**Purpose**: Map to official NIH MeSH controlled vocabulary

**Standards**:
- MUST match official MeSH database exactly (validated via API)
- Use exact capitalization, punctuation, format from MeSH
- Follow MeSH comma rules: `"Reflex, Babinski"` not `"Reflex Babinski"`
- Follow MeSH hyphenation: `"Blood-Brain Barrier"` not `"Blood Brain Barrier"`
- Leave empty if no appropriate MeSH term exists (document rationale)

**Validation**:
- 100% API-validated via mesh-validator agent
- Zero tolerance for typos or format errors
- All corrections logged in tracking files

**Examples**:
- ✅ `"Reflex, Babinski"` (correct format with comma)
- ✅ `"Blood-Brain Barrier"` (correct hyphenation)
- ❌ `"Reflex Babinski"` (missing comma, will FAIL validation)
- ❌ `"Blood Brain Barrier"` (missing hyphen, will FAIL validation)

### Synonyms (1-3)
**Purpose**: True alternative names for the term (NOT abbreviations)

**Standards**:
- Must be full alternative names or phrases
- NOT abbreviations (those go in Abbreviation field)
- NOT associated terms (those go in Commonly Associated Term fields)
- NOT spelling variants (those go in UK/US Spelling fields)
- Verify each synonym is actually used in neuroscience literature

**Examples**:
- Term: `"Babinski sign"` → Synonym 1: `"Babinski reflex"` ✅
- Term: `"Blood-brain barrier"` → Synonym 1: `"BBB"` ❌ (abbreviation, not synonym)
- Term: `"Neuron"` → Synonym 1: `"Nerve cell"` ✅
- Term: `"Neuron"` → Synonym 1: `"Axon"` ❌ (related term, not synonym)

**Quality Checks**:
- Each synonym is truly interchangeable with main term
- No overlap with Abbreviation field
- No overlap with Commonly Associated Term fields
- Verified usage in neuroscience context

### Abbreviation
**Purpose**: Standard abbreviated forms only

**Standards**:
- Short form acronyms or initialisms only
- Commonly used in neuroscience literature
- NOT full names (even if shorter)
- NOT symbols or Greek letters (those stay in Term)
- Leave empty if no standard abbreviation exists

**Examples**:
- Term: `"Blood-brain barrier"` → Abbreviation: `"BBB"` ✅
- Term: `"Brain-derived neurotrophic factor"` → Abbreviation: `"BDNF"` ✅
- Term: `"Basal ganglia"` → Abbreviation: `"BG"` ✅
- Term: `"Neuron"` → Abbreviation: `` (no standard abbreviation) ✅

**NOT for**:
- ❌ Shorter names: Term: `"Action potential"` → Abbreviation: `"potential"`
- ❌ Casual shorthand: Term: `"Hippocampus"` → Abbreviation: `"hippo"`

### UK Spelling / US Spelling
**Purpose**: Document spelling variants between British and American English

**Standards**:
- ONLY use when spelling genuinely differs between regions
- Verify variant is used in neuroscience literature
- Leave empty if no regional spelling difference exists
- Most terms will have BOTH fields empty

**Examples**:
- Term: `"Behaviour"` → US Spelling: `"Behavior"` ✅
- Term: `"Axon"` → UK/US Spelling: both empty (no variant) ✅

### Word Forms (Noun, Verb, Adjective, Adverb)
**Purpose**: Document grammatical variations specific to this term

**Standards**:
- ONLY fill if word form is SPECIFIC to this neuroscience term
- NOT for generic word forms (e.g., "cortical" is general adjective of "cortex")
- Verify word form is actually used in neuroscience context
- Leave empty if no specific form exists or if form is generic

**Examples**:
- Term: `"Baroreceptor"`
  - Noun: `"baroreceptor"` ✅ (is a noun)
  - Adjective: `"baroreceptive"` ✅ (specific to this term)
  - Verb: `` (no verb form exists) ✅

**NOT for**:
- ❌ Term: `"Brain"` → Adjective: `"cerebral"` (derived from "cerebrum", not "brain")
- ❌ Generic forms that apply to any usage of the word

### Commonly Associated Terms (1-8)
**Purpose**: Related neuroscience concepts relevant to understanding this term

**Standards**:
- Fill 1-8 fields as appropriate (NOT mandatory to fill all 8)
- Use established neuroscience terminology
- Include terms that appear together in literature
- Prioritize most relevant/frequently associated terms
- Verify relationships are meaningful

**Categories**:
- Anatomical structures (related brain regions)
- Physiological processes (related functions)
- Diseases/disorders (if pathology-related)
- Cell types (if cellular-level term)
- Neurotransmitters (if relevant to signaling)
- Research methods (if technique-related)

**Examples**:
- Term: `"Basal ganglia"`
  - Associated Term 1: `"striatum"` ✅ (component)
  - Associated Term 2: `"substantia nigra"` ✅ (component)
  - Associated Term 3: `"motor control"` ✅ (primary function)
  - Associated Term 4: `"Parkinson's disease"` ✅ (related disorder)
  - Associated Term 5: `"Huntington's disease"` ✅ (related disorder)

**NOT for**:
- ❌ Synonyms (use Synonym fields)
- ❌ Abbreviations (use Abbreviation field)
- ❌ Antonyms (e.g., listing "unilateral" for "bilateral")
- ❌ Tangentially related terms with no meaningful connection

## Validation Workflow

### Dual Validation Requirements

**Both agents must pass before human review**:

1. **mesh-validator** - Validates ONLY MeSH terms
   - Pass criteria: MeSH term matches NIH API exactly
   - Fail triggers: Typos, format errors, non-existent terms
   - Re-validation: Targeted (only corrected terms)

2. **neuro-reviewer** - Validates ALL other fields
   - Pass criteria: Definitions accurate, synonyms correct, word forms appropriate
   - Fail triggers: Misclassifications, incorrect data, fabricated information
   - Re-validation: Targeted (only corrected fields)

### Human Review Checklist

After both agents pass, verify:
- [ ] Definitions make scientific sense
- [ ] MeSH terms are logically appropriate (not just API-valid)
- [ ] Synonyms are truly interchangeable
- [ ] Abbreviations are standard in field
- [ ] Associated terms are meaningfully related
- [ ] No obvious errors or typos
- [ ] Empty fields are intentionally empty (not oversights)

## Common Errors to Avoid

### 1. Abbreviation/Synonym Confusion
❌ **Wrong**: Term: `"Brain-derived neurotrophic factor"`, Synonym 3: `"BDNF"`, Abbreviation: `"BDNF"`
✅ **Right**: Term: `"Brain-derived neurotrophic factor"`, Synonym 3: `` (empty), Abbreviation: `"BDNF"`

**Rule**: BDNF is an abbreviation, not a synonym. Don't duplicate.

### 2. Generic vs Specific Word Forms
❌ **Wrong**: Term: `"Cortex"`, Adjective: `"cortical"`
✅ **Right**: Term: `"Cortex"`, Adjective: `` (empty)

**Rule**: "Cortical" is generic adjective form, not specific to neuroscience term.

### 3. Associated Term Overload
❌ **Wrong**: Filling all 8 Associated Term fields with loosely related concepts
✅ **Right**: Filling 3-5 fields with clearly related, frequently co-occurring terms

**Rule**: Quality over quantity. Prioritize most relevant associations.

### 4. Fabricated MeSH Terms
❌ **Wrong**: Guessing MeSH term format: `"Neuron, Alpha Motor"`
✅ **Right**: Validating via API, using exact result: `"Motor Neurons"`

**Rule**: NEVER guess MeSH terms. API validation required.

### 5. Definition Modification
❌ **Wrong**: Summarizing or simplifying Wikipedia definition
✅ **Right**: Using verbatim definition from source

**Rule**: Preserve source definition exactly as written.

## Quality Assurance Metrics

### Per-Letter Targets
- **MeSH Validation Pass Rate**: 100% (after corrections)
- **Neuro-Review Pass Rate**: 100% (after corrections)
- **Empty Fields**: < 30% of non-mandatory fields (acceptable if verified empty)
- **MeSH Corrections**: < 20% of terms (indicates good initial quality)
- **Full Re-validations**: 1 per letter (minimize agent invocations)

### Database-Wide Goals
- **Complete Coverage**: All Wikipedia Glossary terms (A-Z)
- **Zero Fabricated Data**: All populated fields verified
- **MeSH Accuracy**: 100% API-validated
- **Definition Accuracy**: 100% from authoritative source
- **Audit Trail**: 100% of corrections documented

## Reference Standards

### External Resources
- **MeSH Database**: https://www.nlm.nih.gov/mesh/ (authoritative)
- **MeSH Browser**: https://meshb.nlm.nih.gov/ (search interface)
- **PubMed**: https://pubmed.ncbi.nlm.nih.gov/ (usage verification)
- **Wikipedia Glossary**: Source material for definitions
- **Medical Dictionaries**: Dorland's, Stedman's (term verification)
- **Neuroscience Textbooks**: Kandel, Purves, Bear (domain knowledge)

### Internal Documentation
- **CLAUDE.md**: Workflow instructions
- **SCHEMA_MIGRATION.md**: Schema evolution notes
- **mesh-validation-guide.md**: MeSH-specific standards
- **agent-orchestration.md**: Validation workflow

## Continuous Improvement

### Feedback Loop
1. Track common validation errors across letters
2. Update standards based on recurring issues
3. Refine agent prompts to catch new error types
4. Document edge cases and resolution approaches

### Version Control
- Tag significant standards updates
- Link standards version to letter files
- Maintain changelog of standards modifications
- Ensure backward compatibility with existing data

---

For implementation, see CLAUDE.md Workflow 1 (Adding New Terms) and agent documentation in `.claude/agents/`.
