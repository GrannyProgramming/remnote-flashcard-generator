"""
Pytest configuration and fixtures for RemNote Flashcard Generator tests.
"""

import pytest
import sys
import os
from pathlib import Path

# Add src directory to path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

# Set up test environment
os.environ.setdefault("TESTING", "1")

@pytest.fixture(scope="session")
def test_data_dir():
    """Fixture providing test data directory path."""
    return Path(__file__).parent / "test_data"

@pytest.fixture(scope="session") 
def sample_content_file():
    """Fixture providing path to sample content file."""
    content_dir = Path(__file__).parent.parent / "content"
    sample_file = content_dir / "ml_system_design.yaml"
    if sample_file.exists():
        return sample_file
    return None

@pytest.fixture
def mock_api_key(monkeypatch):
    """Fixture providing mock API keys for testing."""
    monkeypatch.setenv("OPENAI_API_KEY", "test_openai_key")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test_anthropic_key")
