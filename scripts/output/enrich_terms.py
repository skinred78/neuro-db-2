#!/usr/bin/env python3
"""
Enrich NINDS neuroscience terms with verified data.
"""
import csv

# Define the enriched data based on Gemini verification
enriched_data = [
    {
        "Term": "Anemia",
        "Term Two": "",
        "Definition": "Anemia is a condition in which a person's blood does not produce enough healthy red blood cells which provide oxygen to body tissues. This can cause weakness and fatigue.",
        "Closest MeSH term": "",
        "Synonym 1": "Anaemia",
        "Synonym 2": "Bloodlessness",
        "Synonym 3": "",
        "Abbreviation": "",
        "UK Spelling": "Anaemia",
        "US Spelling": "Anemia",
        "Noun Form of Word": "Anemia",
        "Verb Form of Word": "",
        "Adjective Form of Word": "Anemic",
        "Adverb Form of Word": "Anemically",
        "Commonly Associated Term 1": "Hemoglobin",
        "Commonly Associated Term 2": "Hypoxia",
        "Commonly Associated Term 3": "Erythropoietin",
        "Commonly Associated Term 4": "Cognitive Impairment",
        "Commonly Associated Term 5": "Paresthesia",
        "Commonly Associated Term 6": "Fatigue",
        "Commonly Associated Term 7": "Iron-Deficiency Anemia",
        "Commonly Associated Term 8": "Bone Marrow"
    },
    {
        "Term": "Apraxia",
        "Term Two": "",
        "Definition": "Apraxia is the loss of the ability to perform skilled movements and gestures. For example, a person may no longer be able to wink, lick their lips, or complete the steps required to bathe or dress themselves.",
        "Closest MeSH term": "",
        "Synonym 1": "Dyspraxia",
        "Synonym 2": "",
        "Synonym 3": "",
        "Abbreviation": "",
        "UK Spelling": "",
        "US Spelling": "",
        "Noun Form of Word": "Apraxia",
        "Verb Form of Word": "",
        "Adjective Form of Word": "Apraxic",
        "Adverb Form of Word": "",
        "Commonly Associated Term 1": "Aphasia",
        "Commonly Associated Term 2": "Dysarthria",
        "Commonly Associated Term 3": "Parietal Lobe",
        "Commonly Associated Term 4": "Frontal Lobe",
        "Commonly Associated Term 5": "Ideomotor Apraxia",
        "Commonly Associated Term 6": "Ideational Apraxia",
        "Commonly Associated Term 7": "Motor Planning",
        "Commonly Associated Term 8": "Stroke"
    },
    {
        "Term": "Atrial Fibrillation",
        "Term Two": "",
        "Definition": "Atrial fibrillation is a rapid, irregular, weak beating of the left atrium or upper chamber of the heart. It can cause blood clots and is a major risk factor for ischemic stroke.",
        "Closest MeSH term": "",
        "Synonym 1": "Auricular Fibrillation",
        "Synonym 2": "",
        "Synonym 3": "",
        "Abbreviation": "AFib",
        "UK Spelling": "",
        "US Spelling": "",
        "Noun Form of Word": "Atrial Fibrillation",
        "Verb Form of Word": "",
        "Adjective Form of Word": "Atrial Fibrillatory",
        "Adverb Form of Word": "",
        "Commonly Associated Term 1": "Ischemic Stroke",
        "Commonly Associated Term 2": "Thromboembolism",
        "Commonly Associated Term 3": "Tachycardia",
        "Commonly Associated Term 4": "Palpitations",
        "Commonly Associated Term 5": "Anticoagulation",
        "Commonly Associated Term 6": "Cardioversion",
        "Commonly Associated Term 7": "Hemodynamic Instability",
        "Commonly Associated Term 8": "Heart Failure"
    },
    {
        "Term": "Atrophy",
        "Term Two": "",
        "Definition": "Atrophy is the process of wasting away or deteriorating in cells, tissues, and organs.",
        "Closest MeSH term": "",
        "Synonym 1": "Wasting",
        "Synonym 2": "Degeneration",
        "Synonym 3": "Deterioration",
        "Abbreviation": "",
        "UK Spelling": "",
        "US Spelling": "",
        "Noun Form of Word": "Atrophy",
        "Verb Form of Word": "Atrophy",
        "Adjective Form of Word": "Atrophic",
        "Adverb Form of Word": "",
        "Commonly Associated Term 1": "Neurodegeneration",
        "Commonly Associated Term 2": "Cerebral Atrophy",
        "Commonly Associated Term 3": "Neuronal Loss",
        "Commonly Associated Term 4": "Muscle Wasting",
        "Commonly Associated Term 5": "Alzheimer's Disease",
        "Commonly Associated Term 6": "Multiple Sclerosis",
        "Commonly Associated Term 7": "Hippocampus",
        "Commonly Associated Term 8": "Apoptosis"
    },
    {
        "Term": "Autosomal Recessive Disorders",
        "Term Two": "",
        "Definition": "Autosomal recessive disorders refers to disorders in which means both parents carry and pass on a copy of a defective gene to the affected person.",
        "Closest MeSH term": "",
        "Synonym 1": "Autosomal Recessive Disease",
        "Synonym 2": "Autosomal Recessive Defect",
        "Synonym 3": "",
        "Abbreviation": "AR",
        "UK Spelling": "",
        "US Spelling": "",
        "Noun Form of Word": "Autosome",
        "Verb Form of Word": "",
        "Adjective Form of Word": "Autosomal Recessive",
        "Adverb Form of Word": "Autosomally",
        "Commonly Associated Term 1": "Autosomal Inheritance",
        "Commonly Associated Term 2": "Recessive Trait",
        "Commonly Associated Term 3": "Carrier",
        "Commonly Associated Term 4": "Autosomal Dominant",
        "Commonly Associated Term 5": "Cystic Fibrosis",
        "Commonly Associated Term 6": "Sickle Cell Anemia",
        "Commonly Associated Term 7": "Tay-Sachs Disease",
        "Commonly Associated Term 8": "Phenylketonuria"
    }
]

# Define column headers (22 columns per schema)
fieldnames = [
    "Term", "Term Two", "Definition", "Closest MeSH term",
    "Synonym 1", "Synonym 2", "Synonym 3", "Abbreviation",
    "UK Spelling", "US Spelling",
    "Noun Form of Word", "Verb Form of Word", "Adjective Form of Word", "Adverb Form of Word",
    "Commonly Associated Term 1", "Commonly Associated Term 2", "Commonly Associated Term 3",
    "Commonly Associated Term 4", "Commonly Associated Term 5", "Commonly Associated Term 6",
    "Commonly Associated Term 7", "Commonly Associated Term 8"
]

# Write enriched CSV
output_path = "/Users/sam/NeuroDB-2/scripts/output/A_NINDS_enriched_neuro.csv"
with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(enriched_data)

print(f"✓ Enriched CSV written to: {output_path}")
print(f"✓ Total terms enriched: {len(enriched_data)}")
