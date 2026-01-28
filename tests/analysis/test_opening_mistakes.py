"""Tests for OpeningMistakes."""
from datetime import datetime

import pytest

from src.analysis.opening_mistakes import OpeningMistakeAnalyzer
from src.database.models import Game, Position, get_session


class TestOpeningMistakes:
    """Test integrated opening mistake analysis."""

    @pytest.fixture
    def analyzer(self, test_db):
        """Create analyzer with test db."""
        analyzer = OpeningMistakeAnalyzer()
        yield analyzer
        analyzer.close()

    def test_find_critical_positions(self, analyzer):
        """Test finding specific mistake patterns."""
        session = get_session()

        # Create a game
        game = Game(
            platform="test",
            game_id="g1",
            player_color="white",
            result="0-1",
            opening_name="Test Opening",
            date=datetime(2024, 1, 1),
            pgn="[Test]",
        )
        session.add(game)
        session.commit()

        # Create 2 mistakes at same position (FEN_A)
        # Move 5, Opening
        fen_a = "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2"

        p1 = Position(
            game_id=game.id,
            move_number=5,
            fen=fen_a,
            is_mistake=True,
            eval_drop=150,
            best_move="Nf3",
            player_move="h3",
        )
        p2 = Position(
            game_id=game.id,
            move_number=5,
            fen=fen_a,
            is_mistake=True,
            eval_drop=100,
            best_move="Nf3",
            player_move="h3",
        )

        # Create 1 mistake at different position (FEN_B)
        p3 = Position(
            game_id=game.id,
            move_number=4,
            fen="other_fen",
            is_mistake=True,
            eval_drop=200,
            best_move="e4",
            player_move="d4",
        )

        # Create 1 mistake in MiddleGame (Move 20) - Should be ignored
        p4 = Position(
            game_id=game.id,
            move_number=20,
            fen="middlegame_fen",
            is_mistake=True,
            eval_drop=300,
            best_move="Qxd5",
            player_move="Kf1",
        )

        session.add_all([p1, p2, p3, p4])
        session.commit()

        # Test finding positions (min_occurrences=2)
        critical = analyzer.find_critical_positions(min_occurrences=2)

        assert len(critical) == 1
        assert critical[0]["fen"] == fen_a
        assert critical[0]["count"] == 2
        assert critical[0]["avg_eval_drop"] == 125.0
        assert critical[0]["recommended_move"] == "Nf3"

        session.close()

    def test_get_practice_positions(self, analyzer):
        """Test formatting for practice."""
        session = get_session()
        game = Game(
            platform="test",
            game_id="p1",
            date=datetime(2024, 1, 1),
            opening_name="Practice Opening",
            pgn="[Test]",
        )
        session.add(game)
        session.commit()

        # Add mistake
        pos = Position(
            game_id=game.id,
            move_number=5,
            fen="practice_fen",
            is_mistake=True,
            eval_drop=100,
            best_move="e4",
            player_move="h4",
        )
        # Add duplicate to hit min count of 2 defaults or use min=1 if exposed
        # The method find_critical_positions uses default min=2.
        # So we add another one.
        pos2 = Position(
            game_id=game.id,
            move_number=5,
            fen="practice_fen",
            is_mistake=True,
            eval_drop=100,
            best_move="e4",
            player_move="h4",
        )
        session.add_all([pos, pos2])
        session.commit()

        practice = analyzer.get_practice_positions(limit=5)

        assert len(practice) == 1
        assert practice[0]["fen"] == "practice_fen"
        assert practice[0]["recommended_move"] == "e4"
        assert "mistakes" in practice[0]["description"]

        session.close()
