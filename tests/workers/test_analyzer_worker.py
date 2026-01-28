"""Tests for Analyzer Worker."""
from unittest.mock import MagicMock, patch

import pytest

from src.database.models import Game
from src.workers.analyzer_worker import analyze_game_task


class TestAnalyzerWorker:
    """Test analyzer worker background task."""

    @pytest.fixture
    def mock_db_session(self):
        """Mock database session."""
        with patch("src.workers.analyzer_worker.get_session") as mock_get:
            mock_session = MagicMock()
            mock_get.return_value = mock_session
            yield mock_session

    @pytest.fixture
    def mock_analyzer(self):
        """Mock GameAnalyzer."""
        with patch("src.workers.analyzer_worker.GameAnalyzer") as mock_cls:
            mock_instance = MagicMock()
            mock_cls.return_value.__enter__.return_value = mock_instance
            yield mock_instance

    def test_game_not_found(self, mock_db_session):
        """Test handling when game doesn't exist."""
        # Setup mock to return None when finding game
        mock_db_session.query.return_value.get.return_value = None

        result = analyze_game_task(999)

        assert "error" in result
        assert result["error"] == "Game not found"
        mock_db_session.close.assert_called_once()

    def test_analysis_success(self, mock_db_session, mock_analyzer):
        """Test successful analysis."""
        # Mock game
        mock_game = MagicMock(spec=Game)
        mock_db_session.query.return_value.get.return_value = mock_game

        # Mock analysis result
        expected_result = {"accuracy": 90.0}
        mock_analyzer.analyze_game.return_value = expected_result

        result = analyze_game_task(1)

        assert result == expected_result
        mock_analyzer.analyze_game.assert_called_once_with(mock_game, save_to_db=True)
        mock_db_session.close.assert_called_once()

    def test_analysis_failure(self, mock_db_session, mock_analyzer):
        """Test handling of analysis exceptions."""
        mock_game = MagicMock(spec=Game)
        mock_db_session.query.return_value.get.return_value = mock_game

        # Make analysis fail
        mock_analyzer.analyze_game.side_effect = Exception("Stockfish crashed")

        result = analyze_game_task(1)

        assert "error" in result
        assert "Stockfish crashed" in result["error"]
        mock_db_session.close.assert_called_once()
