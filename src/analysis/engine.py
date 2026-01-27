"""Stockfish chess engine integration."""
import os
from typing import Optional

import chess
import chess.engine
from dotenv import load_dotenv

load_dotenv()


class StockfishAnalyzer:
    """Wrapper for Stockfish chess engine."""

    def __init__(
        self,
        stockfish_path: Optional[str] = None,
        depth: int = 20,
        time_limit: float = 1.0,
    ):
        """
        Initialize Stockfish analyzer.

        Args:
            stockfish_path: Path to Stockfish executable
            depth: Analysis depth (higher = stronger but slower)
            time_limit: Time limit per position in seconds
        """
        self.stockfish_path = stockfish_path or os.getenv(
            "STOCKFISH_PATH", "/usr/local/bin/stockfish"
        )
        self.depth = depth
        self.time_limit = time_limit
        self.engine = None

        # Thresholds
        self.mistake_threshold = int(os.getenv("MISTAKE_THRESHOLD_CP", "50"))
        self.blunder_threshold = int(os.getenv("BLUNDER_THRESHOLD_CP", "150"))

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()

    def connect(self):
        """Connect to Stockfish engine."""
        try:
            self.engine = chess.engine.SimpleEngine.popen_uci(self.stockfish_path)
            print(f"✅ Connected to Stockfish at {self.stockfish_path}")
        except Exception as e:
            print(f"❌ Failed to connect to Stockfish: {e}")
            print(f"   Check that Stockfish is installed at: {self.stockfish_path}")
            raise

    def disconnect(self):
        """Disconnect from engine."""
        if self.engine:
            self.engine.quit()
            self.engine = None

    def analyze_position(self, board: chess.Board) -> dict:
        """
        Analyze a position with Redis caching for speed.

        Returns:
            Dict with 'evaluation', 'best_move', 'mate_in' (if applicable)
        """
        if not self.engine:
            raise RuntimeError("Engine not connected. Call connect() first.")

        # Try cache first
        from src.analysis.cache import get_cache

        fen = board.fen()
        cache = get_cache()
        cached = cache.get_evaluation(fen)

        if cached is not None:
            # Convert cached format to expected format
            return {
                "evaluation": cached.get("score", 0),
                "best_move": cached.get("best_move"),
                "mate_in": None,  # Not cached currently
                "depth": cached.get("depth", 0),
            }

        # Cache miss - analyze with Stockfish
        try:
            info = self.engine.analyse(
                board,
                chess.engine.Limit(depth=self.depth, time=self.time_limit),
            )

            # Always get score from White's perspective for consistency
            score = info["score"].white()

            # Convert score to centipawns
            if score.is_mate():
                mate_in = score.mate()
                # Convert mate to large centipawn value (Positive = White wins)
                cp_score = 10000 if mate_in > 0 else -10000
                mate_info = mate_in
            else:
                cp_score = score.score()
                mate_info = None

            best_move = info.get("pv", [None])[0]

            result = {
                "evaluation": cp_score,
                "best_move": best_move.uci() if best_move else None,
                "mate_in": mate_info,
                "depth": info.get("depth", 0),
            }

            # Cache for next time
            cache.set_evaluation(
                fen, {"score": cp_score, "best_move": result["best_move"], "depth": result["depth"]}
            )

            return result

        except Exception as e:
            print(f"⚠️ Analysis error: {e}")
            return {
                "evaluation": 0,
                "best_move": None,
                "mate_in": None,
                "depth": 0,
            }

    def classify_move(
        self,
        prev_eval: float,
        curr_eval: float,
        side_to_move: bool,
    ) -> dict[str, any]:
        """
        Classify a move as mistake/blunder based on eval drop.

        Args:
            prev_eval: Evaluation before the move (from side's perspective)
            curr_eval: Evaluation after the move (from side's perspective)
            side_to_move: True if white, False if black

        Returns:
            Dict with is_mistake, is_blunder, eval_drop
        """
        # Flip evaluation if it's Black to move (engine always returns white perspective)
        if not side_to_move:
            prev_eval = -prev_eval
            curr_eval = -curr_eval

        # Eval drop (positive = worse position)
        eval_drop = prev_eval - curr_eval

        is_mistake = eval_drop >= self.mistake_threshold
        is_blunder = eval_drop >= self.blunder_threshold

        return {
            "is_mistake": is_mistake,
            "is_blunder": is_blunder,
            "eval_drop": eval_drop,
        }

    def calculate_accuracy(self, eval_drops: list[float]) -> float:
        """
        Calculate accuracy percentage based on eval drops.
        Uses a formula similar to chess.com's accuracy.

        Args:
            eval_drops: List of centipawn losses for each move

        Returns:
            Accuracy percentage (0-100)
        """
        if not eval_drops:
            return 100.0

        # Accuracy formula: penalize mistakes exponentially
        total_penalty = 0
        for drop in eval_drops:
            if drop > 0:
                # Exponential penalty for larger mistakes
                total_penalty += min(100, drop / 10)

        # Average penalty per move
        avg_penalty = total_penalty / len(eval_drops)

        # Convert to accuracy (0-100)
        accuracy = max(0, 100 - avg_penalty)

        return round(accuracy, 1)


if __name__ == "__main__":
    # Test Stockfish connection
    print("🧪 Testing Stockfish integration...\n")

    try:
        with StockfishAnalyzer() as analyzer:
            # Analyze starting position
            board = chess.Board()
            result = analyzer.analyze_position(board)

            print("Starting position analysis:")
            print(f"  Evaluation: {result['evaluation']} cp")
            print(f"  Best move: {result['best_move']}")
            print(f"  Depth: {result['depth']}")
            print("\n✅ Stockfish is working correctly!")

    except Exception as e:
        print(f"\n❌ Stockfish test failed: {e}")
        print("\nTo fix:")
        print("1. Download Stockfish from https://stockfishchess.org/download/")
        print("2. Set STOCKFISH_PATH in your .env file")
