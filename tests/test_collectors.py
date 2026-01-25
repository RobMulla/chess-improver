"""Test chess game collectors."""
import pytest
from unittest.mock import Mock, patch
from src.collectors.chess_com import ChessComCollector
from src.collectors.lichess import LichessCollector


class TestChessComCollector:
    """Test chess.com game collector."""
    
    def test_collector_initialization(self):
        """Test collector can be initialized."""
        collector = ChessComCollector("testuser")
        assert collector.username == "testuser"
        assert collector.BASE_URL == "https://api.chess.com/pub"
    
    @patch('requests.get')
    def test_get_archives(self, mock_get):
        """Test fetching archive list."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "archives": [
                "https://api.chess.com/pub/player/testuser/games/2024/01",
                "https://api.chess.com/pub/player/testuser/games/2024/02"
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        collector = ChessComCollector("testuser")
        # Would need to mock the full flow
    
    def test_parse_game_data(self):
        """Test parsing chess.com game data."""
        collector = ChessComCollector("testuser")
        
        raw_game = {
            "url": "https://www.chess.com/game/live/12345",
            "pgn": "[Event \"Live Chess\"]\n1. e4 e5",
            "end_time": 1706198400,
            "time_control": "600",
            "white": {
                "username": "testuser",
                "rating": 1500,
                "result": "win"
            },
            "black": {
                "username": "opponent",
                "rating": 1480,
                "result": "checkmated"
            }
        }
        
        parsed = collector.parse_game_data(raw_game)
        
        assert parsed is not None
        assert parsed["platform"] == "chess.com"
        assert parsed["game_id"] == "12345"
        assert parsed["player_color"] == "white"
        assert parsed["player_rating"] == 1500
        assert parsed["opponent_rating"] == 1480
        assert parsed["result"] == "1-0"


class TestLichessCollector:
    """Test Lichess game collector."""
    
    def test_collector_initialization(self):
        """Test collector can be initialized."""
        collector = LichessCollector("testuser")
        assert collector.username == "testuser"
        assert collector.BASE_URL == "https://lichess.org/api"
    
    def test_parse_game_data(self):
        """Test parsing Lichess game data."""
        collector = LichessCollector("testuser")
        
        raw_game = {
            "id": "abc123",
            "pgn": "[Event \"Rated Game\"]\n1. e4 e5",
            "createdAt": 1706198400000,
            "clock": {
                "initial": 600,
                "increment": 0
            },
            "players": {
                "white": {
                    "user": {"name": "testuser"},
                    "rating": 1500
                },
                "black": {
                    "user": {"name": "opponent"},
                    "rating": 1480
                }
            },
            "winner": "white",
            "opening": {
                "name": "Italian Game",
                "eco": "C50"
            }
        }
        
        parsed = collector.parse_game_data(raw_game)
        
        assert parsed is not None
        assert parsed["platform"] == "lichess"
        assert parsed["game_id"] == "abc123"
        assert parsed["player_color"] == "white"
        assert parsed["player_rating"] == 1500
        assert parsed["result"] == "1-0"
        assert parsed["opening_name"] == "Italian Game"
        assert parsed["opening_eco"] == "C50"
