# UMLS MRREL Relationship Profile Report

**Date**: 2025-11-20
**Total Concepts**: 325,241
**Concepts with Associations**: 294,008

---

## Overall Statistics

| Metric | Count |
|--------|-------|
| Total MRREL rows | 63,494,934 |
| Rows involving our CUIs | 14,620,746 |
| Relationships extracted | 13,028,966 |
| Domain-specific relationships | 1,801,248 |
| Taxonomy relationships (excluded) | 3,063,984 |
| CUIs with associations | 304,086 |
| CUIs with mapped term names | 294,008 |

**Association Coverage**: 294,008 / 325,241 (90.4%)

---

## Relationship Types (REL)

| REL Code | Description | Count |
|----------|-------------|-------|
| RO | Other related | 5,272,288 |
| SY | Source asserted synonymy | 1,690,002 |
| RQ | Related and possibly synonymous | 1,279,970 |
| PAR | Parent | 1,219,291 |
| CHD | Child | 1,219,291 |
| RN | Narrower (child) | 312,701 |
| RB | Broader (parent) | 312,701 |
| AQ | Unknown | 117,397 |
| QB | Unknown | 117,397 |
| RL | Unknown | 24,742 |

---

## Relationship Attributes (RELA) - Domain-Specific

| RELA | Count | Domain-Specific? |
|------|-------|------------------|
| inverse_isa | 741,433 | ✅ |
| isa | 741,433 | ✅ |
| translation_of | 665,518 | ❌ |
| has_translation | 665,518 | ❌ |
| has_member | 640,994 | ❌ |
| member_of | 640,994 | ❌ |
| classified_as | 546,904 | ❌ |
| classifies | 546,904 | ❌ |
| has_finding_site | 311,992 | ❌ |
| finding_site_of | 311,992 | ❌ |
| mapped_to | 125,345 | ❌ |
| mapped_from | 125,345 | ❌ |
| associated_morphology_of | 101,311 | ❌ |
| has_associated_morphology | 101,311 | ❌ |
| has_direct_procedure_site | 100,932 | ❌ |
| direct_procedure_site_of | 100,932 | ❌ |
| subset_includes_concept | 69,903 | ❌ |
| concept_in_subset | 69,903 | ❌ |
| is_abnormal_cell_of_disease | 69,027 | ❌ |
| disease_has_abnormal_cell | 69,027 | ❌ |
| pathological_process_of | 57,627 | ❌ |
| has_pathological_process | 57,627 | ❌ |
| is_finding_of_disease | 56,387 | ❌ |
| disease_has_finding | 56,387 | ❌ |
| laterality_of | 53,088 | ❌ |
| has_laterality | 53,088 | ❌ |
| has_system | 51,397 | ❌ |
| system_of | 51,397 | ❌ |
| has_manifestation | 51,195 | ❌ |
| manifestation_of | 51,195 | ✅ |

---

## Source Vocabularies Contributing Relationships

| Source | Relationships | % of Total |
|--------|--------------|-----------|
| NCI | 1,369,544 | 11.8% |
| SNOMEDCT_US | 1,014,792 | 8.8% |
| SCTSPA | 821,976 | 7.1% |
| MEDCIN | 596,600 | 5.2% |
| GO | 411,452 | 3.6% |
| MSH | 364,442 | 3.2% |
| FMA | 362,006 | 3.1% |
| UWDA | 350,716 | 3.0% |
| LNC | 287,834 | 2.5% |
| MTH | 253,916 | 2.2% |
| OMIM | 203,444 | 1.8% |
| MDRITA | 180,550 | 1.6% |
| MDRCZE | 180,550 | 1.6% |
| MDRHUN | 180,550 | 1.6% |
| MDRFRE | 180,550 | 1.6% |
| MDRSPA | 180,550 | 1.6% |
| MDRGER | 180,550 | 1.6% |
| MDRDUT | 180,550 | 1.6% |
| MDRPOR | 180,550 | 1.6% |
| MDRRUS | 180,550 | 1.6% |

---

## Sample Associations (First 20 CUIs)

### 1. CUI: C0031843
**Total Associations**: 2820
**Associated Terms** (showing up to 10):
- Anhedonia
- Aponeurosis structure
- Cornea
- Gyrus Cinguli
- Menstrual cycle
- Cytophagocytosis
- Heart Valves
- Chromosomes
- Structure of Broca's area
- Large Intestine

### 2. CUI: C2256707
**Total Associations**: 1
**Associated Terms** (showing up to 10):
- glycogen branching enzyme activity

### 3. CUI: C2256711
**Total Associations**: 5
**Associated Terms** (showing up to 10):
- enzymatic branching factor
- plant branching enzyme
- glycogen branching enzyme activity
- branching enzyme activity
- hexosyltransferase activity (isa, inverse_isa)

### 4. CUI: C0013036
**Total Associations**: 8
**Associated Terms** (showing up to 10):
- Antiparkinson Agents (isa, inverse_isa)
- Dopamine Agonists (isa, inverse_isa)
- Other dopaminergic agents in ATC (isa, inverse_isa)
- Adamantane derivatives, dopaminergic (isa, inverse_isa)
- Dopamine Effect
- MAO B Inhibitors, dopaminergic anti-parkinson drugs (isa, inverse_isa)
- Dopaminergic Agents (has_permuted_term, has_permuted_term, permuted_term_of)
- dopamine (inverse_isa, inverse_isa, inverse_isa)

### 5. CUI: C0270730
**Total Associations**: 6
**Associated Terms** (showing up to 10):
- Movement (interprets, is_interpreted_by)
- Secondary parkinsonism due to other external agents (mapped_from, mapped_to)
- chemically induced
- MPTP-Induced Parkinsonism (has_translation, has_entry_version, has_entry_version)
- Basal Ganglia (has_finding_site, has_finding_site, finding_site_of)
- Toxin-induced parkinsonism (inverse_isa, inverse_isa, isa)

### 6. CUI: C0013030
**Total Associations**: 29
**Associated Terms** (showing up to 10):
- Dopamine Agonists (entry_combination_of, has_entry_combination)
- physiological aspects
- poisoning by dopamine, accidental (has_causative_agent, causative_agent_of)
- Systemic Arterial Vasoconstriction (physiologic_effect_of, has_physiologic_effect)
- Dopamine Metabolites
- Dopamine Agonists [MoA] (mechanism_of_action_of, has_mechanism_of_action)
- dopamine hydrochloride (has_free_acid_or_base_form, isa, is_modification_of)
- Positive Inotropy (physiologic_effect_of, has_physiologic_effect)
- poisoning by dopamine (has_causative_agent, causative_agent_of)
- Dopamine only product (isa, isa, has_active_ingredient)

### 7. CUI: C0000119
**Total Associations**: 1
**Associated Terms** (showing up to 10):
- 11-Hydroxycorticosteroids (has_permuted_term, permuted_term_of, translation_of)

### 8. CUI: C1151265
**Total Associations**: 2
**Associated Terms** (showing up to 10):
- estradiol 17-beta-dehydrogenase [NAD(P)+] activity
- testosterone dehydrogenase (NAD+) activity

### 9. CUI: C3549015
**Total Associations**: 2
**Associated Terms** (showing up to 10):
- steroid dehydrogenase activity, acting on the CH-OH group of donors, NAD or NADP as acceptor (isa, inverse_isa)
- testosterone dehydrogenase (NAD+) activity (inverse_isa, isa)

### 10. CUI: C0000163
**Total Associations**: 18
**Associated Terms** (showing up to 10):
- Glucocorticoids (used_for, use)
- Epitestosterone (isa, isa, inverse_isa)
- Pregnanetriol (isa, isa, inverse_isa)
- 6-alpha hydroxytetrahydro-11-deoxycortisol (isa, isa, inverse_isa)
- Cortolone (isa, isa, inverse_isa)
- 17-Hydroxycorticosteroids (has_permuted_term, permuted_term_of, translation_of)
- 20-alpha-Dihydroprogesterone (isa, isa, inverse_isa)
- Tetrahydrocortisol (isa, isa, inverse_isa)
- Cortodoxone (isa, isa, inverse_isa)
- Adrenal glucocorticoid hormone (inverse_isa, inverse_isa, isa)

### 11. CUI: C0017710
**Total Associations**: 15
**Associated Terms** (showing up to 10):
- physiological aspects
- 17-Hydroxycorticosteroids (used_for, use)
- Steroid suppression of ACTH secretion (has_causative_agent, has_causative_agent, causative_agent_of)
- Adrenal Cortex Hormones (isa, isa, isa)
- Osteonecrosis caused by glucocorticoid (has_causative_agent, has_causative_agent, causative_agent_of)
- Glucocorticoids (translation_of, translation_of, translation_of)
- Corticosteroid and/or corticosteroid derivative (inverse_isa, inverse_isa, isa)
- Cortexone (inverse_isa, isa)
- Cortexone acetate (isa, inverse_isa)
- fluprednisolone (inverse_isa, inverse_isa, inverse_isa)

### 12. CUI: C0010139
**Total Associations**: 4
**Associated Terms** (showing up to 10):
- Glucocorticoids (inverse_isa, isa)
- 17-Hydroxycorticosteroids (isa, isa, inverse_isa)
- Cortodoxone (translation_of, translation_of, translation_of)
- Hormones (inverse_isa, isa)

### 13. CUI: C0012311
**Total Associations**: 3
**Associated Terms** (showing up to 10):
- physiological aspects
- 17-Hydroxycorticosteroids (isa, isa, inverse_isa)
- 20-alpha-Dihydroprogesterone (has_permuted_term, has_permuted_term, has_permuted_term)

### 14. CUI: C0014594
**Total Associations**: 3
**Associated Terms** (showing up to 10):
- physiological aspects
- 17-Hydroxycorticosteroids (isa, isa, inverse_isa)
- Epitestosterone (translation_of, translation_of, translation_of)

### 15. CUI: C0033007
**Total Associations**: 5
**Associated Terms** (showing up to 10):
- 11-oxo-pregnanetriol (isa, isa, inverse_isa)
- Hormones (isa, inverse_isa)
- Delta-5-pregnanetriol (isa, isa, inverse_isa)
- 17-Hydroxycorticosteroids (isa, isa, inverse_isa)
- Pregnanetriol (translation_of, translation_of, translation_of)

### 16. CUI: C0039664
**Total Associations**: 2
**Associated Terms** (showing up to 10):
- 17-Hydroxycorticosteroids (isa, isa, inverse_isa)
- Tetrahydrocortisol (translation_of, translation_of, translation_of)

### 17. CUI: C0039665
**Total Associations**: 2
**Associated Terms** (showing up to 10):
- Tetrahydrocortisone (translation_of, translation_of, translation_of)
- 17-Hydroxycorticosteroids (isa, isa, inverse_isa)

### 18. CUI: C0056399
**Total Associations**: 2
**Associated Terms** (showing up to 10):
- 17-Hydroxycorticosteroids (isa, isa, inverse_isa)
- Allo-cortolones (replaced_by, replaces)

### 19. CUI: C0076263
**Total Associations**: 2
**Associated Terms** (showing up to 10):
- 17-Hydroxycorticosteroids (isa, isa, inverse_isa)
- Tetrahydrodeoxycortisol (same_as, same_as)

### 20. CUI: C0376260
**Total Associations**: 2
**Associated Terms** (showing up to 10):
- 17-Hydroxycorticosteroids (isa, isa, inverse_isa)
- 17-hydroxypregnenolone (has_translation, has_translation, has_translation)

---

## DEC-001 Assessment: Relationship Quality

**Question**: Do UMLS associations provide domain-specific relationships or generic taxonomy?

**Finding**:
- Domain-specific relationships: 1,801,248 (13.8% of extracted)
- Pure taxonomy relationships: 3,063,984 (21.0% of matches)

**Conclusion**: ⚠️ UMLS relationships are **primarily taxonomic**
- May need supplemental sources for domain-specific associations
- Consider NIF, GO, or literature mining for functional relationships

**Recommendation**: Proceed with MRREL associations for NeuroDB-2 'Commonly Associated Terms' mapping
