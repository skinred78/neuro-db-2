"""
Unit tests for semantic classification Phase 1 implementation.
Tests semantic_types.py, expansion_rules.py, and umls.py integration.
"""

import unittest
from unittest.mock import Mock, patch
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from poc_api_first.semantic_types import (
    SemanticCategory,
    TUI_TO_SEMANTIC_GROUP,
    get_category_from_tui
)
from poc_api_first.expansion_rules import (
    EXPANSION_RULES,
    filter_by_category,
    get_expansion_rule
)


class TestSemanticTypes(unittest.TestCase):
    """Test semantic_types.py functionality"""

    def test_semantic_category_enum_exists(self):
        """Verify 8 SemanticCategory enum values exist (7 + UNKNOWN)"""
        expected_categories = {
            'POPULATION_CONTEXT',
            'CONDITION_DISEASE',
            'INTERVENTION_EXPOSURE',
            'OUTCOME_MEASURE',
            'ANATOMY_SYSTEM',
            'MECHANISM_BIOLOGICAL',
            'OBJECT_DEVICE',
            'UNKNOWN'
        }
        actual_categories = {cat.name for cat in SemanticCategory}
        self.assertEqual(expected_categories, actual_categories,
                        f"Expected 8 categories (7 + UNKNOWN), got: {actual_categories}")

    def test_tui_mapping_size(self):
        """Verify TUI_TO_SEMANTIC_GROUP has 100+ entries"""
        self.assertGreaterEqual(len(TUI_TO_SEMANTIC_GROUP), 100,
                               f"Expected 100+ TUI entries, got {len(TUI_TO_SEMANTIC_GROUP)}")

    def test_tui_mapping_correctness(self):
        """Test get_category_from_tui() returns correct categories"""
        test_cases = {
            # ANATOMY_SYSTEM
            'T023': SemanticCategory.ANATOMY_SYSTEM,  # Body Part, Organ, or Organ Component
            'T029': SemanticCategory.ANATOMY_SYSTEM,  # Body Location or Region

            # CONDITION_DISEASE
            'T047': SemanticCategory.CONDITION_DISEASE,  # Disease or Syndrome
            'T048': SemanticCategory.CONDITION_DISEASE,  # Mental or Behavioral Dysfunction

            # OUTCOME_MEASURE (Physiology)
            'T039': SemanticCategory.OUTCOME_MEASURE,  # Physiologic Function
            'T040': SemanticCategory.OUTCOME_MEASURE,  # Organism Function

            # INTERVENTION_EXPOSURE (Chemicals)
            'T109': SemanticCategory.INTERVENTION_EXPOSURE,  # Organic Chemical
            'T121': SemanticCategory.INTERVENTION_EXPOSURE,  # Pharmacologic Substance

            # MECHANISM_BIOLOGICAL (Genes)
            'T028': SemanticCategory.MECHANISM_BIOLOGICAL,  # Gene or Genome
            'T116': SemanticCategory.MECHANISM_BIOLOGICAL,  # Amino Acid, Peptide, or Protein

            # INTERVENTION_EXPOSURE (Procedures)
            'T060': SemanticCategory.INTERVENTION_EXPOSURE,  # Diagnostic Procedure
            'T061': SemanticCategory.INTERVENTION_EXPOSURE,  # Therapeutic or Preventive Procedure

            # UNKNOWN (invalid TUI)
            'T999': SemanticCategory.UNKNOWN,
            'INVALID': SemanticCategory.UNKNOWN
        }

        for tui, expected_category in test_cases.items():
            actual_category = get_category_from_tui(tui)
            self.assertEqual(actual_category, expected_category,
                           f"TUI {tui}: expected {expected_category}, got {actual_category}")


class TestExpansionRules(unittest.TestCase):
    """Test expansion_rules.py functionality"""

    def test_expansion_rules_structure(self):
        """Verify EXPANSION_RULES dict has 8 entries (7 categories + UNKNOWN)"""
        expected_keys = {
            SemanticCategory.POPULATION_CONTEXT,
            SemanticCategory.CONDITION_DISEASE,
            SemanticCategory.INTERVENTION_EXPOSURE,
            SemanticCategory.OUTCOME_MEASURE,
            SemanticCategory.ANATOMY_SYSTEM,
            SemanticCategory.MECHANISM_BIOLOGICAL,
            SemanticCategory.OBJECT_DEVICE,
            SemanticCategory.UNKNOWN
        }
        actual_keys = set(EXPANSION_RULES.keys())
        self.assertEqual(expected_keys, actual_keys,
                        f"Expected 8 category keys (7 + UNKNOWN), got: {actual_keys}")

    def test_expansion_rules_have_forbidden_lists(self):
        """Verify each rule has forbidden_patterns list"""
        for category, rule in EXPANSION_RULES.items():
            self.assertTrue(hasattr(rule, 'forbidden_patterns'),
                         f"Category {category} missing forbidden_patterns")
            self.assertIsInstance(rule.forbidden_patterns, list,
                                f"Category {category} forbidden_patterns not a list")

    def test_filter_by_category_removes_forbidden(self):
        """Test filter_by_category() correctly removes forbidden terms"""
        # Test case: ANATOMY_SYSTEM with pathway suffix (should be blocked)
        anatomy_expansions = [
            'frontal lobe',
            'dopaminergic pathway',  # Should be filtered
            'visual cortex'
        ]

        filtered = filter_by_category(anatomy_expansions, SemanticCategory.ANATOMY_SYSTEM)

        self.assertIn('frontal lobe', filtered)
        self.assertNotIn('dopaminergic pathway', filtered,
                        "Anti-drift pattern failed: 'pathway$' should block 'dopaminergic pathway'")
        self.assertIn('visual cortex', filtered)

    def test_anti_drift_pathway_pattern(self):
        """Test anti-drift patterns work (e.g., 'pathway$' blocks 'dopaminergic pathway')"""
        test_expansions = [
            'mesolimbic pathway',
            'neural pathway',
            'signaling pathway',
            'pathway analysis',  # Should pass (not ending with pathway)
        ]

        filtered = filter_by_category(test_expansions, SemanticCategory.ANATOMY_SYSTEM)

        # All terms ending with 'pathway' should be filtered
        self.assertNotIn('mesolimbic pathway', filtered)
        self.assertNotIn('neural pathway', filtered)
        self.assertNotIn('signaling pathway', filtered)

        # Term with 'pathway' in middle should pass
        self.assertIn('pathway analysis', filtered)

    def test_anti_drift_disease_patterns(self):
        """Test CONDITION_DISEASE anti-drift patterns"""
        test_expansions = [
            'dopamine receptor',      # Should be filtered (receptor$)
            'dopaminergic pathway',   # Should be filtered (pathway$)
            'cell signaling',         # Should be filtered (signaling$)
            'receptor activation',    # Should be filtered (activation$)
            'depression disorder',    # Should pass
            'Alzheimers disease',     # Should pass
        ]

        filtered = filter_by_category(test_expansions, SemanticCategory.CONDITION_DISEASE)

        # These should be filtered out
        self.assertNotIn('dopamine receptor', filtered)
        self.assertNotIn('dopaminergic pathway', filtered)
        self.assertNotIn('cell signaling', filtered)
        self.assertNotIn('receptor activation', filtered)

        # These should pass
        self.assertIn('depression disorder', filtered)
        self.assertIn('Alzheimers disease', filtered)

    def test_unknown_category_no_filtering(self):
        """Test UNKNOWN category has no filtering rules"""
        unknown_rule = EXPANSION_RULES[SemanticCategory.UNKNOWN]
        self.assertEqual(len(unknown_rule.forbidden_patterns), 0,
                        "UNKNOWN category should have no forbidden patterns")


class TestUMLSIntegration(unittest.TestCase):
    """Test umls.py integration with semantic classification"""

    @patch.dict(os.environ, {'UMLS_API_KEY': 'mock_api_key'})
    def test_umls_imports_work(self):
        """Test umls.py imports work without errors"""
        try:
            from poc_api_first.clients.umls import UMLSClient
            self.assertTrue(True, "Import succeeded")
        except Exception as e:
            self.fail(f"Import failed: {e}")

    @patch.dict(os.environ, {'UMLS_API_KEY': 'mock_api_key'})
    def test_umls_client_instantiation(self):
        """Test UMLSClient can be instantiated"""
        from poc_api_first.clients.umls import UMLSClient
        try:
            client = UMLSClient(api_key='mock_key')
            self.assertIsNotNone(client)
        except Exception as e:
            self.fail(f"UMLSClient instantiation failed: {e}")


class TestSemanticClassificationConfig(unittest.TestCase):
    """Test SemanticClassificationConfig in test_configurations.py"""

    @patch.dict(os.environ, {'UMLS_API_KEY': 'mock_api_key'})
    def test_config_instantiation(self):
        """Test SemanticClassificationConfig can be instantiated"""
        from poc_api_first.tests.test_configurations import SemanticClassificationConfig
        try:
            config = SemanticClassificationConfig()
            self.assertIsNotNone(config)
            self.assertTrue(hasattr(config, 'name'))
            self.assertTrue(hasattr(config, 'umls_client'))
            self.assertTrue(hasattr(config, 'classify_term'))
        except Exception as e:
            self.fail(f"SemanticClassificationConfig instantiation failed: {e}")

    @patch.dict(os.environ, {'UMLS_API_KEY': 'mock_api_key'})
    def test_config_attributes(self):
        """Test SemanticClassificationConfig has required attributes"""
        from poc_api_first.tests.test_configurations import SemanticClassificationConfig
        config = SemanticClassificationConfig()

        # Check name attribute
        self.assertEqual(config.name, "SemanticClassification")

        # Check boolean flags
        self.assertTrue(config.use_neurodb)
        self.assertTrue(config.use_umls)
        self.assertFalse(config.use_pubtator)

        # Check methods exist
        self.assertTrue(hasattr(config, 'classify_term'))
        self.assertTrue(hasattr(config, 'get_filtered_synonyms'))
        self.assertTrue(hasattr(config, 'run'))


def run_tests():
    """Run all tests and return results"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestSemanticTypes))
    suite.addTests(loader.loadTestsFromTestCase(TestExpansionRules))
    suite.addTests(loader.loadTestsFromTestCase(TestUMLSIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestSemanticClassificationConfig))

    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result


if __name__ == '__main__':
    result = run_tests()

    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Total Tests: {result.testsRun}")
    print(f"Passed: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failed: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("="*70)

    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)
