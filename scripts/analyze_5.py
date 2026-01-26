"""Analyze a few recent games to test."""
from src.analysis.game_analyzer import GameAnalyzer
from src.database.models import get_session, Game

session = get_session()
games = session.query(Game).filter_by(analyzed=False).order_by(Game.date.desc()).limit(5).all()
session.close()

print(f"Analyzing {len(games)} games...")

with GameAnalyzer() as analyzer:
    for i, game in enumerate(games, 1):
        print(f"\n[{i}/{len(games)}] Game from {game.date}")
        result = analyzer.analyze_game(game, save_to_db=True)

print("\n✅ Done! Check practice page should work now.")
