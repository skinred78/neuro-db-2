"""
Semantic Type Classification for Neuroscience Terms

Maps 127 UMLS Semantic Types (TUIs) to 7 neuroscience-relevant categories
as defined by James (neuroscientist) in stakeholder feedback.

Reference: docs/architecture/semantic-classification-architecture.md
"""

from enum import Enum
from typing import Dict, Optional


class SemanticCategory(Enum):
    """
    7 semantic categories for neuroscience term classification.

    Defined by James based on UMLS's 15 semantic groups mapped to
    neuroscience-relevant categories for query expansion.
    """
    POPULATION_CONTEXT = "POPULATION_CONTEXT"
    CONDITION_DISEASE = "CONDITION_DISEASE"
    INTERVENTION_EXPOSURE = "INTERVENTION_EXPOSURE"
    OUTCOME_MEASURE = "OUTCOME_MEASURE"
    ANATOMY_SYSTEM = "ANATOMY_SYSTEM"
    MECHANISM_BIOLOGICAL = "MECHANISM_BIOLOGICAL"
    OBJECT_DEVICE = "OBJECT_DEVICE"
    UNKNOWN = "UNKNOWN"


# UMLS Semantic Group to Category mapping (per James's feedback)
# UMLS has 15 groups, we map to 7 categories
SEMANTIC_GROUP_TO_CATEGORY: Dict[str, SemanticCategory] = {
    # Living beings, Geographic, Activities, Events, Orgs, Occupations → POPULATION_CONTEXT
    "LIVB": SemanticCategory.POPULATION_CONTEXT,
    "GEOG": SemanticCategory.POPULATION_CONTEXT,
    "ACTI": SemanticCategory.POPULATION_CONTEXT,
    "OCCU": SemanticCategory.POPULATION_CONTEXT,
    "ORGA": SemanticCategory.POPULATION_CONTEXT,

    # Disorders → CONDITION_DISEASE
    "DISO": SemanticCategory.CONDITION_DISEASE,

    # Procedures, Chemicals & Drugs → INTERVENTION_EXPOSURE
    "PROC": SemanticCategory.INTERVENTION_EXPOSURE,
    "CHEM": SemanticCategory.INTERVENTION_EXPOSURE,

    # Physiology, Phenomena → OUTCOME_MEASURE
    "PHYS": SemanticCategory.OUTCOME_MEASURE,
    "PHEN": SemanticCategory.OUTCOME_MEASURE,

    # Anatomy → ANATOMY_SYSTEM
    "ANAT": SemanticCategory.ANATOMY_SYSTEM,

    # Genes & molecular sequences, Concepts & ideas → MECHANISM_BIOLOGICAL
    "GENE": SemanticCategory.MECHANISM_BIOLOGICAL,
    "CONC": SemanticCategory.MECHANISM_BIOLOGICAL,

    # Objects, Devices → OBJECT_DEVICE
    "OBJC": SemanticCategory.OBJECT_DEVICE,
    "DEVI": SemanticCategory.OBJECT_DEVICE,
}


# Complete TUI to Semantic Group mapping (127 TUIs)
# Source: UMLS Semantic Network (https://lhncbc.nlm.nih.gov/semanticnetwork/)
TUI_TO_SEMANTIC_GROUP: Dict[str, str] = {
    # ACTIVITIES & BEHAVIORS (ACTI)
    "T051": "ACTI",  # Event
    "T052": "ACTI",  # Activity
    "T053": "ACTI",  # Behavior
    "T054": "ACTI",  # Social Behavior
    "T055": "ACTI",  # Individual Behavior
    "T056": "ACTI",  # Daily or Recreational Activity
    "T057": "ACTI",  # Occupational Activity
    "T064": "ACTI",  # Governmental or Regulatory Activity
    "T065": "ACTI",  # Educational Activity
    "T066": "ACTI",  # Machine Activity
    "T068": "ACTI",  # Human-caused Phenomenon or Process
    "T101": "ACTI",  # Patient or Disabled Group (behavior context)

    # ANATOMY (ANAT)
    "T017": "ANAT",  # Anatomical Structure
    "T018": "ANAT",  # Embryonic Structure
    "T019": "ANAT",  # Congenital Abnormality
    "T020": "ANAT",  # Acquired Abnormality
    "T021": "ANAT",  # Fully Formed Anatomical Structure
    "T022": "ANAT",  # Body System
    "T023": "ANAT",  # Body Part, Organ, or Organ Component
    "T024": "ANAT",  # Tissue
    "T025": "ANAT",  # Cell
    "T026": "ANAT",  # Cell Component
    "T029": "ANAT",  # Body Location or Region
    "T030": "ANAT",  # Body Space or Junction
    "T031": "ANAT",  # Body Substance

    # CHEMICALS & DRUGS (CHEM) - Pharmacologic substances → INTERVENTION
    "T103": "CHEM",  # Chemical
    "T104": "CHEM",  # Chemical Viewed Structurally
    "T109": "CHEM",  # Organic Chemical
    "T110": "CHEM",  # Steroid
    "T111": "CHEM",  # Eicosanoid
    "T114": "GENE",  # Nucleic Acid, Nucleoside, or Nucleotide → MECHANISM
    "T115": "CHEM",  # Organophosphorus Compound
    "T116": "GENE",  # Amino Acid, Peptide, or Protein → MECHANISM (biological)
    "T118": "CHEM",  # Carbohydrate
    "T119": "CHEM",  # Lipid
    "T120": "CHEM",  # Chemical Viewed Functionally
    "T121": "CHEM",  # Pharmacologic Substance
    "T122": "CHEM",  # Biomedical or Dental Material
    "T123": "GENE",  # Biologically Active Substance → MECHANISM
    "T124": "GENE",  # Neuroreactive Substance or Biogenic Amine → MECHANISM
    "T125": "GENE",  # Hormone → MECHANISM (biological signaling)
    "T126": "GENE",  # Enzyme → MECHANISM
    "T127": "CHEM",  # Vitamin
    "T129": "CHEM",  # Immunologic Factor
    "T130": "CHEM",  # Indicator, Reagent, or Diagnostic Aid
    "T131": "CHEM",  # Hazardous or Poisonous Substance
    "T167": "CHEM",  # Substance
    "T168": "CHEM",  # Food
    "T169": "CONC",  # Functional Concept → MECHANISM (concepts)
    "T192": "GENE",  # Receptor → MECHANISM (biological)
    "T195": "CHEM",  # Antibiotic
    "T196": "CHEM",  # Element, Ion, or Isotope
    "T197": "CHEM",  # Inorganic Chemical
    "T200": "CHEM",  # Clinical Drug
    "T203": "DEVI",  # Drug Delivery Device → OBJECT_DEVICE

    # CONCEPTS & IDEAS (CONC)
    "T077": "CONC",  # Conceptual Entity
    "T078": "CONC",  # Idea or Concept
    "T079": "CONC",  # Temporal Concept
    "T080": "CONC",  # Qualitative Concept
    "T081": "CONC",  # Quantitative Concept
    "T082": "CONC",  # Spatial Concept
    "T089": "CONC",  # Regulation or Law
    "T102": "CONC",  # Group Attribute
    "T170": "CONC",  # Intellectual Product
    "T171": "CONC",  # Language
    "T185": "CONC",  # Classification

    # DEVICES (DEVI)
    "T074": "DEVI",  # Medical Device
    "T075": "DEVI",  # Research Device

    # DISORDERS (DISO)
    "T019": "DISO",  # Congenital Abnormality (also anatomical)
    "T020": "DISO",  # Acquired Abnormality (also anatomical)
    "T037": "DISO",  # Injury or Poisoning
    "T046": "DISO",  # Pathologic Function
    "T047": "DISO",  # Disease or Syndrome
    "T048": "DISO",  # Mental or Behavioral Dysfunction
    "T049": "DISO",  # Cell or Molecular Dysfunction
    "T050": "DISO",  # Experimental Model of Disease
    "T184": "DISO",  # Sign or Symptom
    "T190": "DISO",  # Anatomical Abnormality
    "T191": "DISO",  # Neoplastic Process

    # GENES & MOLECULAR SEQUENCES (GENE)
    "T028": "GENE",  # Gene or Genome
    "T085": "GENE",  # Molecular Sequence
    "T086": "GENE",  # Nucleotide Sequence
    "T087": "GENE",  # Amino Acid Sequence
    "T088": "GENE",  # Carbohydrate Sequence

    # GEOGRAPHIC AREAS (GEOG)
    "T083": "GEOG",  # Geographic Area

    # LIVING BEINGS (LIVB)
    "T001": "LIVB",  # Organism
    "T002": "LIVB",  # Plant
    "T004": "LIVB",  # Fungus
    "T005": "LIVB",  # Virus
    "T007": "LIVB",  # Bacterium
    "T008": "LIVB",  # Animal
    "T010": "LIVB",  # Vertebrate
    "T011": "LIVB",  # Amphibian
    "T012": "LIVB",  # Bird
    "T013": "LIVB",  # Fish
    "T014": "LIVB",  # Reptile
    "T015": "LIVB",  # Mammal
    "T016": "LIVB",  # Human
    "T096": "LIVB",  # Group
    "T097": "LIVB",  # Professional or Occupational Group
    "T098": "LIVB",  # Population Group
    "T099": "LIVB",  # Family Group
    "T100": "LIVB",  # Age Group
    "T101": "LIVB",  # Patient or Disabled Group
    "T194": "LIVB",  # Archaeon
    "T204": "LIVB",  # Eukaryote

    # OBJECTS (OBJC)
    "T071": "OBJC",  # Entity
    "T072": "OBJC",  # Physical Object
    "T073": "OBJC",  # Manufactured Object

    # OCCUPATIONS (OCCU)
    "T090": "OCCU",  # Occupation or Discipline
    "T091": "OCCU",  # Biomedical Occupation or Discipline

    # ORGANIZATIONS (ORGA)
    "T092": "ORGA",  # Organization
    "T093": "ORGA",  # Health Care Related Organization
    "T094": "ORGA",  # Professional Society
    "T095": "ORGA",  # Self-help or Relief Organization

    # PHENOMENA (PHEN)
    "T034": "PHEN",  # Laboratory or Test Result
    "T038": "PHEN",  # Biologic Function
    "T067": "PHEN",  # Phenomenon or Process
    "T068": "PHEN",  # Human-caused Phenomenon or Process
    "T069": "PHEN",  # Environmental Effect of Humans
    "T070": "PHEN",  # Natural Phenomenon or Process

    # PHYSIOLOGY (PHYS)
    "T032": "PHYS",  # Organism Attribute
    "T033": "PHYS",  # Finding
    "T039": "PHYS",  # Physiologic Function
    "T040": "PHYS",  # Organism Function
    "T041": "PHYS",  # Mental Process
    "T042": "PHYS",  # Organ or Tissue Function
    "T043": "PHYS",  # Cell Function
    "T044": "PHYS",  # Molecular Function
    "T045": "PHYS",  # Genetic Function

    # PROCEDURES (PROC)
    "T058": "PROC",  # Health Care Activity
    "T059": "PROC",  # Laboratory Procedure
    "T060": "PROC",  # Diagnostic Procedure
    "T061": "PROC",  # Therapeutic or Preventive Procedure
    "T062": "PROC",  # Research Activity
    "T063": "PROC",  # Molecular Biology Research Technique
}


def get_category_from_tui(tui: str) -> SemanticCategory:
    """
    Get semantic category from TUI.

    Args:
        tui: Type Unique Identifier (e.g., "T047")

    Returns:
        SemanticCategory enum value
    """
    sem_group = TUI_TO_SEMANTIC_GROUP.get(tui)
    if sem_group:
        return SEMANTIC_GROUP_TO_CATEGORY.get(sem_group, SemanticCategory.UNKNOWN)
    return SemanticCategory.UNKNOWN


def get_category_from_semantic_group(sem_group: str) -> SemanticCategory:
    """
    Get semantic category from UMLS semantic group abbreviation.

    Args:
        sem_group: Semantic group abbreviation (e.g., "DISO", "PROC")

    Returns:
        SemanticCategory enum value
    """
    return SEMANTIC_GROUP_TO_CATEGORY.get(sem_group, SemanticCategory.UNKNOWN)


def get_semantic_group(tui: str) -> Optional[str]:
    """
    Get UMLS semantic group from TUI.

    Args:
        tui: Type Unique Identifier (e.g., "T047")

    Returns:
        Semantic group abbreviation (e.g., "DISO") or None
    """
    return TUI_TO_SEMANTIC_GROUP.get(tui)


# Category display names for UI/logging
CATEGORY_DISPLAY_NAMES = {
    SemanticCategory.POPULATION_CONTEXT: "Population/Context",
    SemanticCategory.CONDITION_DISEASE: "Condition/Disease",
    SemanticCategory.INTERVENTION_EXPOSURE: "Intervention/Exposure",
    SemanticCategory.OUTCOME_MEASURE: "Outcome/Measure",
    SemanticCategory.ANATOMY_SYSTEM: "Anatomy/System",
    SemanticCategory.MECHANISM_BIOLOGICAL: "Mechanism/Biological",
    SemanticCategory.OBJECT_DEVICE: "Object/Device",
    SemanticCategory.UNKNOWN: "Unknown",
}


# Neuroscience-relevant TUIs with descriptions (top 30 from research)
NEUROSCIENCE_TUIS = {
    "T047": "Disease or Syndrome",
    "T184": "Sign or Symptom",
    "T048": "Mental or Behavioral Dysfunction",
    "T046": "Pathologic Function",
    "T023": "Body Part, Organ, Component",
    "T025": "Cell",
    "T026": "Cell Component",
    "T029": "Body Location or Region",
    "T042": "Organ or Tissue Function",
    "T041": "Mental Process",
    "T043": "Cell Function",
    "T044": "Molecular Function",
    "T061": "Therapeutic or Preventive Procedure",
    "T060": "Diagnostic Procedure",
    "T059": "Laboratory Procedure",
    "T033": "Finding",
    "T034": "Laboratory or Test Result",
    "T121": "Pharmacologic Substance",
    "T116": "Amino Acid, Peptide, Protein",
    "T123": "Biologically Active Substance",
    "T125": "Hormone",
    "T126": "Enzyme",
    "T028": "Gene or Genome",
    "T074": "Medical Device",
    "T037": "Injury or Poisoning",
    "T191": "Neoplastic Process",
    "T019": "Congenital Abnormality",
    "T020": "Acquired Abnormality",
    "T049": "Cell or Molecular Dysfunction",
    "T050": "Experimental Model of Disease",
}


if __name__ == "__main__":
    # Quick test
    print("Semantic Type Classification Test")
    print("=" * 50)

    test_tuis = ["T047", "T061", "T042", "T023", "T116", "T074", "T100"]
    for tui in test_tuis:
        category = get_category_from_tui(tui)
        sem_group = get_semantic_group(tui)
        desc = NEUROSCIENCE_TUIS.get(tui, "N/A")
        print(f"{tui} ({desc}): {sem_group} → {category.value}")
