"""Find and analyze games with actual mistakes."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.database.models import get_session, Game
from src.analysis.game_analyzer import GameAnalyzer

# Get LONGER losses (more likely to have mistakes)
session = get_session()

print("Finding games with mistakes...")

# Get losses with at least 20 moves
longer_losses = (session.query(Game)
                .filter(Game.result.in_(['0-1', '1-0']))
                .filter(Game.analyzed == False)
                .filter(Game.total_moves == None)  # Not analyzed yet
                .order_by(Game.date.desc())
                .limit(30)
                .all())

# Filter for games that were likely full games (not blitz timeout)
filtered = []
for game in longer_losses:
    # Count moves in PGN
    move_count = game.pgn.count('.') if game.pgn else 0
    if move_count >= 20:  # At least 20 moves
        filtered.append(game)
        if len(filtered) >= 10:
            break

session.close()

if not filtered:
    print("No suitable games found!")
    sys.exit(0)

print(f"\n🎯 Analyzing {len(filtered)} longer games for mistakes...\n")

mistake_count = 0
blunder_count = 0

with GameAnalyzer() as analyzer:
    for i, game in enumerate(filtered, 1):
        print(f"[{i}/{len(filtered)}] Game from {game.date}")
        
        try:
            analysis = analyzer.analyze_game(game, save_to_db=True)
            
            mistakes = analysis.get('move_counts', {}).get('mistake', 0)
            blunders = analysis.get('move_counts', {}).get('blunder', 0)
            accuracy = analysis.get('player_accuracy', 0)
            
            mistake_count += mistakes
            blunder_count += blunders
            
            print(f"   ✓ Accuracy: {accuracy:.1f}% | Mistakes: {mistakes} | Blunders: {blunders}")
            
            if mistakes + blunders > 0:
                print(f"   🎯 Found {mistakes + blunders} training positions!")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")

print(f"\n{'='*60}")
print(f"✅ Done!")
print(f"   Total mistakes: {mistake_count}")
print(f"   Total blunders: {blunder_count}")
print(f"   Total practice positions: {mistake_count + blunder_count}")
print(f"{'='*60}")
