"""Analyze latest 100 games with updated classifier."""
from src.analysis.game_analyzer import GameAnalyzer
from src.database.models import get_session, Game

session = get_session()

# Get latest 100 games
games = session.query(Game).order_by(Game.date.desc()).limit(100).all()

print(f"🎯 Analyzing {len(games)} most recent games...")
print(f"This will take approximately {len(games) * 30} seconds (30s per game)")
print()

with GameAnalyzer() as analyzer:
    for i, game in enumerate(games, 1):
        print(f"[{i}/{len(games)}] Analyzing game from {game.date}...")
        try:
            result = analyzer.analyze_game(game, save_to_db=True)
        except Exception as e:
            print(f"  ❌ Error: {e}")
            continue

print()
print("✅ Analysis complete!")
print(f"Latest {len(games)} games analyzed with:")
print("  - FEN-based game phase detection")
print("  - Updated move classifier")
print("  - Comprehensive statistics")
print()
print("Practice system is ready to use!")

session.close()
