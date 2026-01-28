from src.analysis.game_analyzer import GameAnalyzer
from src.database.models import Game, get_session


def reanalyze_some():
    session = get_session()
    games = session.query(Game).filter_by(analyzed=True).limit(2).all()
    session.close()

    with GameAnalyzer() as analyzer:
        for game in games:
            print(f"Re-analyzing {game.id}...")
            analyzer.analyze_game(game)


if __name__ == "__main__":
    reanalyze_some()
