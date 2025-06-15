import pytest
from pathlib import Path

@pytest.fixture
def psf_test_files():
    return Path(__file__).parent / "data"

