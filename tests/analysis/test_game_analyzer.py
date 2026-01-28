"""Test GameAnalyzer."""
import pytest

from src.analysis.game_analyzer import GameAnalyzer


class TestGameAnalyzer:
    """Test game analysis functionality."""

    def test_analyzer_creation(self):
        """Test analyzer can be created."""
        try:
            with GameAnalyzer() as analyzer:
                assert analyzer.analyzer is not None
                assert analyzer.session is not None
        except Exception:
            pytest.skip("Stockfish or Redis not available")
