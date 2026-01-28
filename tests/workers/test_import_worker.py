"""Tests for Import Worker."""
from unittest.mock import MagicMock, patch

import pytest

from src.workers.import_worker import sync_games_task


class TestImportWorker:
    """Test import worker background tasks."""

    @pytest.fixture
    def mock_db_session(self):
        """Mock database session."""
        with patch("src.workers.import_worker.get_session") as mock_get:
            mock_session = MagicMock()
            mock_get.return_value = mock_session
            yield mock_session

    @pytest.fixture
    def mock_requests(self):
        """Mock requests."""
        with patch("src.workers.import_worker.requests") as mock_req:
            yield mock_req

    @pytest.fixture
    def mock_job(self):
        """Mock RQ job."""
        with patch("src.workers.import_worker.get_current_job") as mock_job_fn:
            mock_job = MagicMock()
            mock_job.meta = {}  # Use real dict
            mock_job_fn.return_value = mock_job
            yield mock_job

    def test_sync_unknown_platform(self, mock_db_session, mock_job):
        """Test syncing unknown platform."""
        sync_games_task("unknown_platform", "user")

        assert mock_job.meta["status"] == "failed"
        assert "Unknown platform" in mock_job.meta["error"]

    def test_sync_chess_com_success(self, mock_db_session, mock_requests, mock_job):
        """Test successful sync from Chess.com."""
        # Mock archives response
        mock_requests.get.return_value.json.return_value = {
            "archives": ["https://api.chess.com/pub/player/user/games/2024/01"]
        }
        mock_requests.get.return_value.status_code = 200

        # Mock games response
        # First call is archives, second is the archive url
        def side_effect(url, **kwargs):
            mock = MagicMock()
            mock.status_code = 200
            if "archives" in url:
                mock.json.return_value = {
                    "archives": ["https://api.chess.com/pub/player/user/games/2024/01"]
                }
            else:
                mock.json.return_value = {
                    "games": [
                        {
                            "url": "https://chess.com/game/123",
                            "pgn": '[Event "Test"]\n[Date "2024.01.01"]\n1. e4 e5',
                        }
                    ]
                }
            return mock

        mock_requests.get.side_effect = side_effect

        # Mock DB query to return None (game doesn't exist)
        mock_db_session.query.return_value.filter_by.return_value.first.return_value = None

        sync_games_task("chess.com", "user")

        assert mock_job.meta["status"] == "completed"
        assert mock_job.meta["imported_count"] == 1
        mock_db_session.add.assert_called()
        mock_db_session.commit.assert_called()

    def test_sync_chess_com_api_error(self, mock_db_session, mock_requests):
        """Test handling of Chess.com API error."""
        mock_requests.get.side_effect = Exception("API Error")

        # Should NOT raise exception, but log error and finish
        sync_games_task("chess.com", "user")
        # No assertions needed other than no raise, logic handles it gracefully

    def test_sync_lichess_success(self, mock_db_session, mock_requests, mock_job):
        """Test successful sync from Lichess."""
        # Mock stream response check
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = (
            '[Event "Test"]\n[Site "https://lichess.org/123"]\n[Date "2024.01.01"]\n1. e4 e5'
        )
        mock_requests.get.return_value = mock_response

        mock_db_session.query.return_value.filter_by.return_value.first.return_value = None

        sync_games_task("lichess", "user")

        assert mock_job.meta["status"] == "completed"
        # We mocked one game
        assert mock_job.meta["imported_count"] == 1
        mock_db_session.add.assert_called()
