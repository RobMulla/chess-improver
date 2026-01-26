"""Quick script to find and analyze one game that likely has mistakes."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.database.models import get_session, Game
from src.analysis.game_analyzer import GameAnalyzer

# Get one game where user LOST (more likely to have mistakes)
session = get_session()

# Try to find a longer loss
game = (session.query(Game)
        .filter(Game.result == '0-1')  # Loss as white
        .filter(Game.analyzed == False)
        .filter(Game.pgn.contains('1. e4'))  # Has some moves
        .order_by(Game.date.desc())
        .first())

if not game:
    print("No suitable game found, trying black losses...")
    game = (session.query(Game)
            .filter(Game.result == '1-0')  # Loss as black
            .filter(Game.analyzed == False)
            .order_by(Game.date.desc())
            .first())

if not game:
    print("❌ No unanalyzed games found!")
    session.close()
    sys.exit(1)

print(f"📊 Analyzing game from {game.date}")
print(f"   Result: {game.result}, Color: {game.player_color}")
print(f"   Opponent: {game.opponent_rating or 'Unknown'}\n")

# Analyze it
with GameAnalyzer() as analyzer:
    result = analyzer.analyze_game(game, save_to_db=True)

session.close()

print("\n✅ Analysis complete!")
print(f"   Accuracy: {result['player_accuracy']:.1f}%")
print(f"   Mistakes: {result['move_counts'].get('mistake', 0)}")
print(f"   Blunders: {result['move_counts'].get('blunder', 0)}")
print(f"   Inaccuracies: {result['move_counts'].get('inaccuracy', 0)}")

total_bad = (result['move_counts'].get('mistake', 0) + 
             result['move_counts'].get('blunder', 0) +
             result['move_counts'].get('inaccuracy', 0))

if total_bad > 0:
    print(f"\n🎯 Found {total_bad} practice positions!")
else:
    print("\n⚠️ Still no mistakes found - might need to adjust thresholds")
