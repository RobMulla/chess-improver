import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.web.app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"

    with app.test_client() as client:
        with app.app_context():
            import src.web.app
            from src.database.models import Base, Game, Position

            engine = create_engine("sqlite:///:memory:")
            Base.metadata.create_all(engine)

            Session = sessionmaker(bind=engine)
            test_session = Session()

            # Monkeypatch get_session in app module
            original_get_session = src.web.app.get_session
            src.web.app.get_session = lambda: test_session

            # Seed data
            from datetime import datetime

            game = Game(
                platform="chess.com",
                game_id="test_game_1",
                pgn="[Test]",
                date=datetime.fromisoformat("2024-01-01T12:00:00"),
                player_color="white",
                opponent_name="TestOpp",
                opening_name="Italian Game",
                analyzed=True,
            )
            test_session.add(game)
            test_session.commit()

            pos = Position(
                game_id=game.id,
                fen="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
                move_number=10,
                is_mistake=True,
                is_blunder=True,
                best_move="e2e4",
                game_phase="opening",
                eval_drop=100.0,
            )
            test_session.add(pos)
            test_session.commit()

            yield client

            # Teardown
            src.web.app.get_session = original_get_session
            test_session.close()
            Base.metadata.drop_all(engine)


def test_practice_positions(client):
    """Test fetching practice positions."""
    response = client.get("/api/practice/positions?limit=5")
    assert response.status_code == 200
    data = response.json

    assert "positions" in data
    assert "session_id" in data
    assert len(data["positions"]) > 0
    assert data["positions"][0]["best_move"] == "e2e4"


def test_practice_check_correct(client):
    """Test checking a correct move."""
    # First get a position to know the ID
    response = client.get("/api/practice/positions")
    data = response.json
    pos_id = data["positions"][0]["id"]
    session_id = data["session_id"]

    # Check Correct Move
    check_resp = client.post(
        "/api/practice/check",
        json={"session_id": session_id, "position_id": pos_id, "user_move": "e2e4"},
    )

    assert check_resp.status_code == 200
    result = check_resp.json
    assert result["correct"] is True
    assert result["best_move"] == "e2e4"


def test_practice_check_incorrect(client):
    """Test checking an incorrect move."""
    response = client.get("/api/practice/positions")
    data = response.json
    pos_id = data["positions"][0]["id"]
    session_id = data["session_id"]

    # Check Incorrect Move
    check_resp = client.post(
        "/api/practice/check",
        json={"session_id": session_id, "position_id": pos_id, "user_move": "a2a3"},
    )

    assert check_resp.status_code == 200
    result = check_resp.json
    assert result["correct"] is False
    assert result["best_move"] == "e2e4"


def test_practice_give_up(client):
    """Test giving up on a move."""
    response = client.get("/api/practice/positions")
    data = response.json
    pos_id = data["positions"][0]["id"]
    session_id = data["session_id"]

    # Give Up
    check_resp = client.post(
        "/api/practice/check",
        json={"session_id": session_id, "position_id": pos_id, "gave_up": True},
    )

    assert check_resp.status_code == 200
    result = check_resp.json
    assert result["correct"] is False
    assert result["best_move"] == "e2e4"
