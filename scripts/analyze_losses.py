"""Analyze recent losses to populate practice system."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.database.models import get_session, Game
from src.analysis.game_analyzer import GameAnalyzer

# Get recent losses
session = get_session()
losses = (session.query(Game)
          .filter(Game.result == '0-1')  # Losses as white
          .filter(Game.analyzed == False)
          .order_by(Game.date.desc())
          .limit(10)
          .all())

black_losses = (session.query(Game)
                .filter(Game.result == '1-0')  # Losses as black
                .filter(Game.analyzed == False)
                .order_by(Game.date.desc())
                .limit(10)
                .all())

all_losses = losses + black_losses
session.close()

print(f"🎯 Analyzing {len(all_losses)} recent losses for practice data...")
print(f"   (Looking for mistakes to train on)\n")

mistake_count = 0
blunder_count = 0

with GameAnalyzer() as analyzer:
    for i, game in enumerate(all_losses, 1):
        result_emoji = "❌" if game.result in ['0-1', '1-0'] else "="
        print(f"\n[{i}/{len(all_losses)}] {result_emoji} Game from {game.date} vs {game.opponent_rating or 'N/A'}")
        
        try:
            analysis = analyzer.analyze_game(game, save_to_db=True)
            
            # Track mistakes
            mistakes = analysis.get('move_counts', {}).get('mistake', 0)
            blunders = analysis.get('move_counts', {}).get('blunder', 0)
            mistake_count += mistakes
            blunder_count += blunders
            
            print(f"   ✓ Accuracy: {analysis.get('player_accuracy', 0):.1f}% | Mistakes: {mistakes} | Blunders: {blunders}")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")

print(f"\n{'='*60}")
print(f"✅ Analysis complete!")
print(f"   Total mistakes found: {mistake_count}")
print(f"   Total blunders found: {blunder_count}")
print(f"   Practice system now has real data! 🎉")
print(f"{'='*60}")
