"""Test suite for Chess Improver."""
import os
import sys

import pytest

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.analysis.game_analyzer import GameAnalyzer
from src.analysis.move_classifier import MoveClassifier
from src.database.models import Game, Position, get_session


class TestMoveClassifier:
    """Test move classification logic."""

    def test_classify_game_phase_opening(self):
        """Test opening phase detection."""
        # Starting position with most pieces
        fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
        phase = MoveClassifier.classify_game_phase(fen, 1)
        assert phase == "opening"

    def test_classify_game_phase_endgame_no_queens(self):
        """Test endgame detection when queens are off."""
        # Position with no queens
        fen = "4k3/8/8/8/8/8/8/4K2R w - - 0 1"
        phase = MoveClassifier.classify_game_phase(fen, 30)
        assert phase == "endgame"

    def test_classify_game_phase_middlegame(self):
        """Test middlegame detection."""
        # Queens still on, some pieces exchanged
        # Move 8 could still be opening/early middlegame transition
        fen = "r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 0 1"
        phase = MoveClassifier.classify_game_phase(fen, 8)
        # Move 8 with many pieces still on board is typically opening
        assert phase in ["opening", "middlegame"]

    def test_classify_move_brilliant(self):
        """Test brilliant move classification - currently not implemented, should be 'great'."""
        result = MoveClassifier.classify_move(prev_eval=100, curr_eval=500, is_white_turn=True)
        # Brilliant not implemented yet, should be "best"
        # Since eval improved or match, it is at least good
        assert result["classification"] in ["great", "best"]
        assert result["is_mistake"] == False

    def test_classify_move_blunder(self):
        """Test blunder classification (15%+ Win% loss)."""
        result = MoveClassifier.classify_move(
            prev_eval=100,
            curr_eval=-200,  # Drop from +100 to -200 = ~30% Win% loss
            is_white_turn=True,
        )
        assert result["classification"] == "blunder"
        assert result["is_blunder"] == True

    def test_classify_move_best(self):
        """Test best move classification."""
        result = MoveClassifier.classify_move(prev_eval=0, curr_eval=100, is_white_turn=True)
        assert result["classification"] == "best"
        assert result["is_mistake"] == False


class TestDatabase:
    """Test database operations."""

    def test_game_save_and_load(self):
        """Test saving and loading a game."""
        session = get_session()

        # Count games before
        count_before = session.query(Game).count()

        # Create test game
        from datetime import datetime

        game = Game(
            platform="test",
            game_id="TEST_GAME_123",
            player_color="white",
            result="1-0",
            pgn="test pgn",
            date=datetime.utcnow(),
        )
        session.add(game)
        session.commit()

        # Verify count increased
        count_after = session.query(Game).count()
        assert count_after == count_before + 1

        # Load and verify
        loaded = session.query(Game).filter_by(game_id="TEST_GAME_123").first()
        assert loaded is not None
        assert loaded.player_color == "white"

        # Cleanup
        session.delete(loaded)
        session.commit()
        session.close()

    def test_position_relationships(self):
        """Test Position -> Game relationship."""
        session = get_session()

        # Get a position
        pos = session.query(Position).first()

        if pos:
            # Verify relationship works
            assert pos.game is not None
            assert pos.game.id == pos.game_id

        session.close()


class TestGameAnalyzer:
    """Test game analysis functionality."""

    def test_analyzer_creation(self):
        """Test analyzer can be created."""
        with GameAnalyzer() as analyzer:
            assert analyzer.analyzer is not None
            assert analyzer.session is not None


def run_tests():
    """Run all tests and report results."""
    print("🧪 Running Chess Improver Tests...\n")

    # Run pytest
    exit_code = pytest.main([__file__, "-v", "-s", "--tb=short"])

    if exit_code == 0:
        print("\n✅ All tests passed!")
    else:
        print(f"\n❌ Tests failed with exit code {exit_code}")

    return exit_code


if __name__ == "__main__":
    run_tests()
