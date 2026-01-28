"""Tests for OpeningAnalyzer."""
from datetime import datetime

import pytest

from src.analysis.opening_analyzer import OpeningAnalyzer
from src.database.models import Game, Opening, get_session


class TestOpeningAnalyzer:
    """Test integrated opening analysis."""

    @pytest.fixture
    def analyzer(self, test_db):
        """Create analyzer with test db."""
        analyzer = OpeningAnalyzer()
        yield analyzer
        analyzer.close()

    def test_analyze_no_games(self, analyzer):
        """Test analysis with no games."""
        analyzer.analyze_openings()
        session = get_session()
        count = session.query(Opening).count()
        session.close()
        assert count == 0

    def test_analyze_openings_stats(self, analyzer):
        """Test calculation of opening stats."""
        session = get_session()

        # Create games for "Italian Game"
        # 1 Win (White)
        g1 = Game(
            platform="test",
            game_id="g1",
            player_color="white",
            result="1-0",
            opening_name="Italian Game",
            opening_eco="C50",
            date=datetime(2024, 1, 1),
            pgn="[Test]",
        )
        # 1 Loss (Black) - result 1-0 means White won, so Black lost
        g2 = Game(
            platform="test",
            game_id="g2",
            player_color="black",
            result="1-0",
            opening_name="Italian Game",
            opening_eco="C50",
            date=datetime(2024, 1, 2),
            pgn="[Test]",
        )
        # 1 Draw
        g3 = Game(
            platform="test",
            game_id="g3",
            player_color="white",
            result="1/2-1/2",
            opening_name="Italian Game",
            opening_eco="C50",
            date=datetime(2024, 1, 3),
            pgn="[Test]",
        )

        session.add_all([g1, g2, g3])
        session.commit()

        # Run analysis
        analyzer.analyze_openings()

        # Verify
        op = session.query(Opening).filter_by(name="Italian Game").first()
        assert op is not None
        assert op.games_played == 3
        assert op.wins == 1
        assert op.losses == 1
        assert op.draws == 1
        assert op.eco_code == "C50"

        # Win rate should be (1 + 0.5) / 3 = 0.5
        assert abs(op.win_rate - 0.5) < 0.01

        session.close()

    def test_weak_openings(self, analyzer):
        """Test identification of weak openings."""
        session = get_session()

        # Create 5 losses for "Bad Opening"
        for i in range(5):
            g = Game(
                platform="test",
                game_id=f"bad_{i}",
                player_color="white",
                result="0-1",
                opening_name="Bad Opening",
                date=datetime(2024, 1, 1),
                pgn="[Test]",
            )
            session.add(g)

        # Create 5 wins for "Good Opening"
        for i in range(5):
            g = Game(
                platform="test",
                game_id=f"good_{i}",
                player_color="white",
                result="1-0",
                opening_name="Good Opening",
                date=datetime(2024, 1, 1),
                pgn="[Test]",
            )
            session.add(g)

        session.commit()

        analyzer.analyze_openings()
        weak = analyzer.get_weak_openings(min_games=3)

        assert len(weak) > 0
        assert weak[0].name == "Bad Opening"
        assert weak[0].win_rate == 0.0

        session.close()
