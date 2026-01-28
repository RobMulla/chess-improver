"""Golden test: Compare our analysis to Chess.com's for game 148322637444."""

import sys

from src.analysis.game_analyzer import GameAnalyzer
from src.database.models import Game, get_session

# Chess.com's analysis results for RobM83 in this game
EXPECTED_RESULTS = {
    "accuracy": 87.6,
    "brilliant": 0,
    "great": 1,
    "best": 30,
    "excellent": 27,
    "good": 8,
    "inaccuracy": 1,
    "mistake": 0,
    "miss": 2,
    "blunder": 0,
}

print("🎯 Golden Test: Chess.com Game 148322637444")
print("=" * 60)
print("\nChess.com Analysis (Expected):")
print(f"  Accuracy: {EXPECTED_RESULTS['accuracy']}%")
print(f"  Great: {EXPECTED_RESULTS['great']}")
print(f"  Best: {EXPECTED_RESULTS['best']}")
print(f"  Excellent: {EXPECTED_RESULTS['excellent']}")
print(f"  Good: {EXPECTED_RESULTS['good']}")
print(f"  Inaccuracy: {EXPECTED_RESULTS['inaccuracy']}")
print(f"  Mistake: {EXPECTED_RESULTS['mistake']}")
print(f"  Miss: {EXPECTED_RESULTS['miss']}")
print(f"  Blunder: {EXPECTED_RESULTS['blunder']}")

# Get the game from database
session = get_session()
game = session.query(Game).filter_by(game_id="148322637444").first()

if not game:
    print("\n❌ Game not found in database!")
    print("   Run: python scripts/import_games.py to import it first")
    session.close()
    sys.exit(1)

print(f"\n✓ Found game: {game.date} vs {game.opponent_name or 'Unknown'}")
print(f"  Result: {game.result}, Playing as: {game.player_color}")

# Analyze it
print("\n🔍 Analyzing with our tool...\n")

with GameAnalyzer() as analyzer:
    result = analyzer.analyze_game(game, save_to_db=True)

session.close()

# Compare results
print("\n" + "=" * 60)
print("Our Analysis vs Chess.com:")
print("=" * 60)

our_accuracy = result["player_accuracy"]
accuracy_diff = abs(our_accuracy - EXPECTED_RESULTS["accuracy"])

print("\n📊 Accuracy:")
print(f"  Chess.com: {EXPECTED_RESULTS['accuracy']}%")
print(f"  Our tool:  {our_accuracy:.1f}%")
print(f"  Difference: {accuracy_diff:.1f}%")

if accuracy_diff <= 5.0:
    print("  ✅ MATCH (within 5%)")
else:
    print(f"  ❌ MISMATCH (off by {accuracy_diff:.1f}%)")

print("\n📈 Move Classifications:")
print(f"{'Category':<12} {'Chess.com':<10} {'Our Tool':<10} {'Status'}")
print("-" * 45)

categories = ["brilliant", "great", "best", "excellent", "good", "inaccuracy", "mistake", "blunder"]
total_diff = 0

for cat in categories:
    expected = EXPECTED_RESULTS[cat]
    actual = result["move_counts"].get(cat, 0)
    diff = abs(expected - actual)
    total_diff += diff

    status = "✅" if diff <= 2 else "❌"
    print(f"{cat:<12} {expected:<10} {actual:<10} {status}")

# Handle "miss" separately (we don't have this category)
miss_expected = EXPECTED_RESULTS["miss"]
print(f"{'miss':<12} {miss_expected:<10} {'N/A':<10} ⚠️ (not implemented)")

print("\n" + "=" * 60)
if accuracy_diff <= 5.0 and total_diff <= 10:
    print("✅ PASS: Results match Chess.com closely!")
    print("   Our analyzer is working correctly.")
else:
    print("❌ FAIL: Results differ significantly")
    print(f"   Accuracy off by: {accuracy_diff:.1f}%")
    print(f"   Total move classification diff: {total_diff}")
    print("\n🔧 Next steps:")
    print("   - Check thresholds in move_classifier.py")
    print("   - Verify Stockfish depth matches Chess.com")
    print("   - Compare move-by-move evaluations")
print("=" * 60)
