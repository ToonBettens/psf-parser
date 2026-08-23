from pathlib import Path

import pytest


@pytest.fixture
def psf_test_files():
    return Path(__file__).parent / "data"

