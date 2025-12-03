"""
Capability Checker Utility

Checks if a config supports specific evaluation metrics based on CAPABILITY_MATRIX.
Prevents applying semantic metrics to configs without semantic classification.
"""

from typing import Dict

# Import CAPABILITY_MATRIX from test_configurations
# Using dynamic import to avoid circular dependency issues
def _get_capability_matrix() -> Dict:
    """Lazy load CAPABILITY_MATRIX to avoid circular imports."""
    from poc_api_first.tests.test_configurations import CAPABILITY_MATRIX
    return CAPABILITY_MATRIX


class CapabilityChecker:
    """Check if config supports specific evaluation metrics."""

    @staticmethod
    def supports_semantic_classification(config_name: str) -> bool:
        """Check if config can produce semantic classifications."""
        matrix = _get_capability_matrix()
        return matrix.get(config_name, {}).get(
            'supports_semantic_classification', False
        )

    @staticmethod
    def get_applicable_metrics(config_name: str) -> Dict[str, bool]:
        """
        Get dict of which metric types apply to this config.

        Args:
            config_name: Name of the configuration (e.g., 'UMLSPubTator')

        Returns:
            Dict with metric type keys and bool values for applicability
        """
        return {
            'quantitative': True,  # Always applicable
            'semantic_accuracy': CapabilityChecker.supports_semantic_classification(config_name)
        }

    @staticmethod
    def get_capabilities(config_name: str) -> Dict[str, bool]:
        """
        Get full capabilities dict for a config.

        Args:
            config_name: Name of the configuration

        Returns:
            Dict with all capability keys and their values
        """
        matrix = _get_capability_matrix()
        return matrix.get(config_name, {
            'supports_semantic_classification': False,
            'supports_abbreviation_expansion': False,
            'supports_component_detection': False,
            'supports_synonym_expansion': False
        })
