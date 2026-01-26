"""Test analysis on one game."""
from src.analysis.game_analyzer import GameAnalyzer
from src.database.models import get_session, Game

# Analyze ONE game to test
session = get_session()
game = session.query(Game).order_by(Game.date.desc()).first()
session.close()

print(f"Testing analysis on game {game.id} from {game.date}...")

with GameAnalyzer() as analyzer:
    result = analyzer.analyze_game(game, save_to_db=True)
    print(f"\nAnalysis complete!")
    print(f"Result: {result}")

# Verify it saved
session2 = get_session()
updated_game = session2.query(Game).get(game.id)
print(f"\nVerification:")
print(f"  analyzed: {updated_game.analyzed}")
print(f"  accuracy: {updated_game.player_accuracy}")
print(f"  total_moves: {updated_game.total_moves}")
print(f"  brilliant: {updated_game.brilliant_moves}")
session2.close()
