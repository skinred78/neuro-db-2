"""
Centralized configuration from environment variables.

Loads settings from .env file and provides defaults for optional values.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
PROJECT_ROOT = Path(__file__).parent.parent
load_dotenv(PROJECT_ROOT / '.env')


class Config:
    """Centralized configuration from environment variables."""

    # API Keys
    UMLS_API_KEY = os.getenv('UMLS_API_KEY')

    # Redis Configuration
    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))
    REDIS_DB = int(os.getenv('REDIS_DB', '0'))

    @classmethod
    def redis_url(cls) -> str:
        """Get Redis connection URL."""
        return f"redis://{cls.REDIS_HOST}:{cls.REDIS_PORT}/{cls.REDIS_DB}"

    # Test Configuration
    TEST_PARALLEL = os.getenv('TEST_PARALLEL', 'true').lower() == 'true'
    TEST_WORKERS = int(os.getenv('TEST_WORKERS', '5'))
    TEST_OUTPUT_DIR = os.getenv('TEST_OUTPUT_DIR', 'poc_api_first/results')

    # API Rate Limits
    UMLS_RATE_PER_SEC = int(os.getenv('UMLS_RATE_LIMIT_PER_SEC', '20'))
    UMLS_RATE_PER_HOUR = int(os.getenv('UMLS_RATE_LIMIT_PER_HOUR', '5000'))
    PUBTATOR_RATE_PER_SEC = int(os.getenv('PUBTATOR_RATE_LIMIT_PER_SEC', '10'))
    PUBTATOR_RATE_PER_HOUR = int(os.getenv('PUBTATOR_RATE_LIMIT_PER_HOUR', '1000'))

    # Data Paths (repo-relative)
    NEURODB_DATA_PATH = PROJECT_ROOT / 'data' / 'neuro_terms.json'

    @classmethod
    def verify(cls) -> None:
        """
        Verify required configuration.

        Raises:
            ValueError: If required configuration is missing or invalid
        """
        errors = []

        # Check required API key
        if not cls.UMLS_API_KEY:
            errors.append("UMLS_API_KEY not set in environment (.env file or environment variables)")

        # Check data file exists
        if not cls.NEURODB_DATA_PATH.exists():
            errors.append(f"NeuroDB data not found: {cls.NEURODB_DATA_PATH}")

        # Validate Redis port
        if not (1 <= cls.REDIS_PORT <= 65535):
            errors.append(f"Invalid REDIS_PORT: {cls.REDIS_PORT} (must be 1-65535)")

        # Validate test workers
        if not (1 <= cls.TEST_WORKERS <= 50):
            errors.append(f"Invalid TEST_WORKERS: {cls.TEST_WORKERS} (must be 1-50)")

        # Validate rate limits
        if cls.UMLS_RATE_PER_SEC < 1:
            errors.append(f"Invalid UMLS_RATE_LIMIT_PER_SEC: {cls.UMLS_RATE_PER_SEC} (must be >= 1)")
        if cls.UMLS_RATE_PER_HOUR < 1:
            errors.append(f"Invalid UMLS_RATE_LIMIT_PER_HOUR: {cls.UMLS_RATE_PER_HOUR} (must be >= 1)")
        if cls.PUBTATOR_RATE_PER_SEC < 1:
            errors.append(f"Invalid PUBTATOR_RATE_LIMIT_PER_SEC: {cls.PUBTATOR_RATE_PER_SEC} (must be >= 1)")
        if cls.PUBTATOR_RATE_PER_HOUR < 1:
            errors.append(f"Invalid PUBTATOR_RATE_LIMIT_PER_HOUR: {cls.PUBTATOR_RATE_PER_HOUR} (must be >= 1)")

        if errors:
            raise ValueError(f"Configuration errors:\n  - " + "\n  - ".join(errors))

    @classmethod
    def summary(cls) -> str:
        """
        Get configuration summary (for debugging/verification).

        Returns:
            Human-readable configuration summary with sensitive data masked
        """
        return f"""Configuration Summary:
  API Keys:
    UMLS_API_KEY: {'***' + cls.UMLS_API_KEY[-4:] if cls.UMLS_API_KEY else 'NOT SET'}

  Redis:
    Host: {cls.REDIS_HOST}
    Port: {cls.REDIS_PORT}
    DB: {cls.REDIS_DB}
    URL: {cls.redis_url()}

  Testing:
    Parallel: {cls.TEST_PARALLEL}
    Workers: {cls.TEST_WORKERS}
    Output Dir: {cls.TEST_OUTPUT_DIR}

  Rate Limits:
    UMLS: {cls.UMLS_RATE_PER_SEC} req/s, {cls.UMLS_RATE_PER_HOUR} req/hr
    PubTator: {cls.PUBTATOR_RATE_PER_SEC} req/s, {cls.PUBTATOR_RATE_PER_HOUR} req/hr

  Data Paths:
    NeuroDB: {cls.NEURODB_DATA_PATH} ({'EXISTS' if cls.NEURODB_DATA_PATH.exists() else 'MISSING'})
"""
