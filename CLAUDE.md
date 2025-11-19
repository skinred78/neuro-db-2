# CLAUDE.md: Neuroscience Terminology Database

## Role & Responsibilities

Your role is to manage the Neuroscience Terminology Database project, analyze requirements, delegate tasks to appropriate sub-agents, and ensure cohesive delivery of features that meet specifications and quality standards.

## Project Overview

This project is a neuroscience terminology database. All terms from A-Z have been collected and validated following strict, multi-step validation processes to ensure data accuracy and completeness.

**Database Status**: ✅ Complete (~595 terms across 26 letters, all using 22-column schema)

### Integration with Lex Stream

**Purpose**: This database powers the **[Lex Stream](../Lex-stream-2)** query expansion pipeline.

**Data Flow**:
```
NeuroDB-2 (ingestion, enrichment, validation)
    ↓ export via convert_to_lexstream.py
neuro_terms.json → Lex Stream (agents: spell checker, abbreviation expander, synonym finder, MeSH detector)
```

**Integration Status**: ✅ Production-ready (95% test pass rate)
**Integration Report**: `LEXSTREAM_INTEGRATION_REPORT.md`
**Lex Stream Documentation**: [CLAUDE.md](../Lex-stream-2/CLAUDE.md), [README.md](../Lex-stream-2/README.md)

**Current Priority**: Implementing MeSH hierarchy trees (neuroscientist feedback in Lex Stream: `docs/analysis/20251117-neuroscientist-feedback-expansion-trees.md`)

## Workflows

- Primary workflow: `./.claude/workflows/primary-workflow.md`
- Development rules: `./.claude/workflows/development-rules.md`
- Orchestration protocols: `./.claude/workflows/orchestration-protocol.md`
- Documentation management: `./.claude/workflows/documentation-management.md`

**IMPORTANT:** Follow strictly the development rules in `./.claude/workflows/development-rules.md` file.
**IMPORTANT:** Sacrifice grammar for the sake of concision when writing reports.
**IMPORTANT:** In reports, list any unresolved questions at the end, if any.

---

## Key Files

- **Working Files:** `[A-Z].csv` (one CSV file per letter during data collection, e.g., `B.csv`, `C.csv`)
- **Master Database:** `neuro_terms.csv` (consolidated final database)
- **Final Output:** `neuro_terms.json`
- **Validation Directory:** `MeshValidation/` (contains MeSH validation reports and correction logs)
  - `mesh_corrections_log.json` - Master log of all MeSH corrections
  - `mesh_corrections_log.csv` - CSV format for spreadsheets
  - `mesh_corrections_summary.md` - Human-readable summary
  - `archive/` - Historical validation reports

---

## Data Schema (for neuro_terms.csv)

The CSV file MUST contain these exact columns:
- `Term` - The primary neuroscience term
- `Term Two` - **ONLY** for alternate representations with special characters removed (e.g., "alpha (α) motor neurons" → "alphamotor neurons"). Used for searchable/ASCII-safe versions. NOT for synonyms or alternative names.
- `Definition` - The full definition from Wikipedia (must be properly quoted if it contains commas)
- `Closest MeSH term` - The exact official MeSH (Medical Subject Headings) database entry
- `Synonym 1` - Alternative names or terms (not abbreviations)
- `Synonym 2`
- `Synonym 3`
- `Abbreviation` - Standard abbreviated forms only (e.g., BBB, BDNF, BCI)
- `UK Spelling` - British English spelling variant if different
- `US Spelling` - American English spelling variant if different
- `Noun Form of Word` - Noun form (only if applicable and specific to this term)
- `Verb Form of Word` - Verb form (only if applicable and specific to this term)
- `Adjective Form of Word` - Adjective form (only if applicable and specific to this term)
- `Adverb Form of Word` - Adverb form (only if applicable and specific to this term)
- `Commonly Associated Term 1` - Related neuroscience concepts (1-8 as appropriate)
- `Commonly Associated Term 2`
- `Commonly Associated Term 3`
- `Commonly Associated Term 4`
- `Commonly Associated Term 5`
- `Commonly Associated Term 6`
- `Commonly Associated Term 7`
- `Commonly Associated Term 8`

**Total columns: 22** (expanded from 19 to accommodate more associated terms)

**Note**: All letter files (A-Z) now use the complete 22-column schema.

---

## <instructions> Workflow 1: Adding New Terms </instructions>

**Status**: ✅ All letters A-Z completed. This workflow is preserved for reference and future term additions.

This is the 5-step process used for collecting terms:

<step_1>
  **Task:** Ingest Core Data
  **Source:** Wikipedia-Glossary-of-Neuroscience.md
  **Action:** Read the source file and extract the `Term` and `Definition` for the requested letter.
</step_1>

<step_2>
  **Task:** AI Data Enrichment
  **Action:** For each `Term`, enrich the data by filling in the remaining columns where verifiable information is available.
  **Critical Guidelines:**
  - Only populate fields with accurate, verifiable information
  - Do NOT fabricate or guess information
  - Leave fields empty if no reliable data is available
  - For "Commonly Associated Term" columns: fill 1-8 terms as appropriate (not mandatory to fill all 8)
  - Prioritize accuracy over completeness
</step_2>

<step_3>
  **Task:** Automated Data Quality Review
  **Action:** Invoke BOTH validation agents to validate the CSV data.
  **Process:**
  - First, validate CSV structure locally using Python/bash (verify exactly 22 columns per row)
  - Write the CSV data to a temporary file using Python's csv module (ensures proper quoting)
  - **Launch TWO agents in parallel** (use single message with multiple Task tool calls):

    **Agent 1: mesh-validator** (API-based MeSH validation)
    - Validates ONLY the "Closest MeSH term" field
    - Uses official NIH MeSH API for authoritative verification
    - Fast and accurate (API responses in milliseconds)
    - Reports exact matches, errors, and suggested corrections

    **Agent 2: neuro-reviewer** (Gemini-based validation for all other fields)
    - Validates ALL fields EXCEPT "Closest MeSH term"
    - Verifies: Term Two, Definition, Synonyms, Abbreviations, Word Forms, Associated Terms
    - Uses Gemini CLI for cross-checking
    - Reports errors and recommendations

  - **Combine results** from both agents:
    - If BOTH agents return "PASS", proceed to step 4
    - If EITHER agent returns "FAIL":
      1. Apply ALL recommended corrections from both agents in one batch
      2. **If mesh-validator reported any MeSH corrections**, update all three MeSH tracking files:
         - `MeshValidation/mesh_corrections_log.json` (add corrections to letter's array)
         - `MeshValidation/mesh_corrections_log.csv` (append rows)
         - `MeshValidation/mesh_corrections_summary.md` (update summary and details)
      3. Invoke the failed agent(s) for TARGETED re-validation of ONLY the corrected items
      4. Do NOT re-run full review - only verify the specific corrections made

  **CRITICAL:**
  - Do not proceed to human review until BOTH automated reviews pass
  - Run agents in parallel for maximum efficiency
  - Minimize agent invocations to save tokens and time
  - Full reviews should only happen once per letter
  - mesh-validator has final authority on MeSH terms (API-verified)
</step_3>

<step_4>
  **Task:** Format & Human Review
  **Action:** Present the validated CSV block to me for final review.
  **CRITICAL:** Do NOT save this data until I give my explicit approval.
</step_4>

<step_5>
  **Task:** Save to Working File
  **Action:** Once I approve the CSV block, save it to `[X].csv` (where X is the letter being processed, e.g., `F.csv`). Do not overwrite existing files without confirmation.
</step_5>

---

## <instructions> Workflow 2: Merging Letter Files </instructions>

This workflow consolidates all individual letter CSV files into the master database.
When I ask you to "merge the letters" or "consolidate the database," you must:
1. Read all `[A-Z].csv` files in alphabetical order (e.g., `B.csv`, `C.csv`, `D.csv`).
2. Combine all rows (preserving headers from the first file only).
3. Save the consolidated data to `neuro_terms.csv`.
4. Report how many terms were merged from each letter.

---

## <instructions> Workflow 3: Final Database Merge </instructions>

This workflow consolidates all individual letter CSV files into the master database.
When I ask you to "merge the letters" or "consolidate the database," you must:
1. Read all `[A-Z].csv` files in alphabetical order (e.g., `B.csv`, `C.csv`, `D.csv`).
2. Verify all files have 22 columns before merging
3. Combine all rows (preserving headers from the first file only).
4. Save the consolidated data to `neuro_terms.csv`.
5. Report how many terms were merged from each letter.

---

## <instructions> Workflow 4: Generating JSON Output </instructions>

This is the final export step. When I ask you to "generate the JSON," you must:
1. Read the entire `neuro_terms.csv` file.
2. Convert all rows into a valid JSON array.
3. Save the result, overwriting the `neuro_terms.json` file.

---

## ClaudeKit Integration

This project uses ClaudeKit framework for AI-powered development orchestration. Available specialized agents:

### Domain-Specific Agents (Project-Critical)
- **mesh-validator** - Validates MeSH terms against NIH API (REQUIRED for neuroscience data)
- **neuro-reviewer** - Reviews neuroscience terminology data using Gemini CLI (REQUIRED for neuroscience data)

### General Development Agents
- **planner** - Creates implementation plans for new features
- **researcher** - Conducts parallel research on technical topics
- **tester** - Runs tests and generates reports
- **debugger** - Analyzes logs and error reports
- **code-reviewer** - Reviews code quality and standards
- **docs-manager** - Updates project documentation
- **git-manager** - Manages version control workflows
- **project-manager** - Tracks progress and milestones

### Agent Orchestration Principles
- Use **parallel execution** for independent tasks (e.g., mesh-validator + neuro-reviewer)
- Use **sequential chaining** for dependent tasks
- Communicate between agents via markdown reports in `./plans/reports/`
- Follow agent-specific expertise for task delegation

---

## Documentation Management

We keep all important docs in `./docs` folder and keep updating them:

```
./docs
├── project-overview-pdr.md
├── code-standards.md
├── codebase-summary.md
└── RELEASE.md
```

---

## Best Practices

### Development Principles
- **YANGI**: You Aren't Gonna Need It - avoid over-engineering
- **KISS**: Keep It Simple, Stupid - prefer simple solutions
- **DRY**: Don't Repeat Yourself - eliminate code duplication

### Data Quality
- All data goes through dual validation (mesh-validator + neuro-reviewer)
- MeSH terms MUST be API-verified
- Accuracy over completeness for all fields
- Comprehensive validation logging in MeshValidation/

### Git Workflow
- Clean, conventional commit messages
- Professional git history
- No AI attribution in commits
- Focused, atomic commits

---

## Important Notes

- Only create files when absolutely necessary
- ALWAYS prefer editing existing files to creating new ones
- Never fabricate data - leave fields empty if information is unavailable
- All letter files use the exact 22-column schema
- Run both validation agents in parallel for efficiency
- Document all MeSH corrections in tracking files
