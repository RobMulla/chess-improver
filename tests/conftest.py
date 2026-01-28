import os
import sys

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))  # noqa

import pytest  # noqa: E402

from src.database.models import init_db  # noqa: E402


@pytest.fixture
def test_db():
    """Create test database."""
    os.environ["DATABASE_URL"] = "sqlite:///test_chess.db"
    init_db()

    yield

    # Cleanup
    if os.path.exists("test_chess.db"):
        os.remove("test_chess.db")
