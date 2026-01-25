"""Analyze games with Stockfish."""
import argparse
from src.analysis.game_analyzer import GameAnalyzer


def main():
    parser = argparse.ArgumentParser(description="Analyze chess games with Stockfish")
    parser.add_argument(
        "--limit",
        type=int,
        help="Limit number of games to analyze",
        default=None,
    )
    parser.add_argument(
        "--stockfish-path",
        help="Path to Stockfish executable",
        default=None,
    )
    
    args = parser.parse_args()
    
    print("\n♟️  Chess Game Analyzer")
    print("=" * 60)
    
    with GameAnalyzer(stockfish_path=args.stockfish_path) as analyzer:
        analyzer.analyze_unanalyzed_games(limit=args.limit)
    
    print("\n🎉 Analysis complete!")


if __name__ == "__main__":
    main()
