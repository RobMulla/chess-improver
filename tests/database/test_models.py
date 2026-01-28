"""Test suite for chess improvement system."""
from datetime import datetime

from src.database.models import Game, Opening, Position, get_session


class TestDatabase:
    """Test database models and operations."""

    def test_init_db(self, test_db):
        """Test database initialization."""
        session = get_session()
        assert session is not None
        session.close()

    def test_create_game(self, test_db):
        """Test creating a game record."""
        session = get_session()

        game = Game(
            platform="chess.com",
            game_id="test123",
            pgn='[Event "Test"]\n1. e4 e5',
            date=datetime.now(),
            time_control="600",
            result="1-0",
            player_color="white",
            player_rating=1500,
            opponent_rating=1480,
        )

        session.add(game)
        session.commit()

        retrieved = session.query(Game).filter_by(game_id="test123").first()
        assert retrieved is not None
        assert retrieved.platform == "chess.com"
        assert retrieved.player_rating == 1500

        session.close()

    def test_game_position_relationship(self, test_db):
        """Test relationship between games and positions."""
        session = get_session()

        game = Game(
            platform="lichess",
            game_id="test456",
            pgn='[Event "Test"]\n1. e4 e5',
            date=datetime.now(),
            result="1/2-1/2",
            player_color="white",
        )
        session.add(game)
        session.commit()

        position = Position(
            game_id=game.id,
            move_number=1,
            fen="rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1",
            evaluation=25,
            best_move="e7e5",
            player_move="e7e5",
        )
        session.add(position)
        session.commit()

        assert len(game.positions) == 1
        assert game.positions[0].move_number == 1

        session.close()

    def test_opening_statistics(self, test_db):
        """Test opening model."""
        session = get_session()

        opening = Opening(
            name="Italian Game",
            eco_code="C50",
            games_played=10,
            wins=6,
            draws=2,
            losses=2,
        )
        session.add(opening)
        session.commit()

        assert opening.win_rate == 0.7  # (6 + 0.5*2) / 10

        session.close()

    def test_game_save_and_load(self, test_db):
        """Test saving and loading a game (migrated)."""
        session = get_session()

        # Count games before
        count_before = session.query(Game).count()

        game = Game(
            platform="test",
            game_id="TEST_GAME_MIGRATED",
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
        loaded = session.query(Game).filter_by(game_id="TEST_GAME_MIGRATED").first()
        assert loaded is not None
        assert loaded.player_color == "white"

        # Cleanup
        session.delete(loaded)
        session.commit()
        session.close()

    def test_position_relationships_check(self, test_db):
        """Test Position -> Game relationship (migrated)."""
        session = get_session()

        # Get a position if exists or create
        pos = session.query(Position).first()
        if not pos:
            # Need a game first
            game = Game(platform="t", game_id="tpos", pgn="", date=datetime.now())
            session.add(game)
            session.commit()
            pos = Position(game_id=game.id, move_number=1, fen="start", evaluation=0)
            session.add(pos)
            session.commit()

        if pos:
            # Verify relationship works
            assert pos.game is not None
            assert pos.game.id == pos.game_id

        session.close()
