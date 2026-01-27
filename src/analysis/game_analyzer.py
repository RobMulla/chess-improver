"""Game analyzer using Stockfish."""

from datetime import datetime
from io import StringIO
from typing import Optional

import chess
import chess.pgn

from src.analysis.engine import StockfishAnalyzer
from src.database.models import Game, Position, get_session


class GameAnalyzer:
    """Analyze chess games with Stockfish."""

    def __init__(self, stockfish_path: Optional[str] = None):
        self.analyzer = StockfishAnalyzer(stockfish_path=stockfish_path)
        self.session = get_session()

    def __enter__(self):
        self.analyzer.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.analyzer.disconnect()
        self.session.close()

    def analyze_game(self, game: Game, save_to_db: bool = True) -> dict:
        """
        Analyze a complete game with detailed statistics.

        Args:
            game: Game object from database
            save_to_db: Whether to save analysis to database

        Returns:
            Dict with analysis summary
        """
        from src.analysis.move_classifier import MoveClassifier

        # Merge game into this session to avoid detached instance issues
        game = self.session.merge(game)

        print(f"🔍 Analyzing game {game.game_id}...")

        try:
            # Parse PGN
            pgn = StringIO(game.pgn)
            chess_game = chess.pgn.read_game(pgn)

            if not chess_game:
                print(f"⚠️ Could not parse PGN for game {game.game_id}")
                return {}

            # Extract Opening Info if missing
            if not game.opening_name or not game.opening_eco:
                game.opening_name = chess_game.headers.get("Opening", "")
                if not game.opening_name and "ECOUrl" in chess_game.headers:
                    game.opening_name = (
                        chess_game.headers.get("ECOUrl", "")
                        .split("/")[-1]
                        .replace("-", " ")
                        .title()
                    )

                game.opening_eco = chess_game.headers.get("ECO", "")

            # Initialize counters
            positions_data = []
            move_counts = {
                "brilliant": 0,
                "great": 0,
                "best": 0,
                "excellent": 0,
                "good": 0,
                "book": 0,
                "inaccuracy": 0,
                "mistake": 0,
                "miss": 0,
                "blunder": 0,
            }

            opening_classifications = []
            middlegame_classifications = []
            endgame_classifications = []
            all_classifications = []
            opponent_classifications = []

            # Setup board and move number
            board = chess_game.board()
            move_number = 0

            # Initial analysis of starting position
            initial_analysis = self.analyzer.analyze_position(board)
            prev_eval = initial_analysis["evaluation"]
            prev_best_move = initial_analysis["best_move"]

            for move in chess_game.mainline_moves():
                move_number += 1

                # Setup context before move
                current_fen = board.fen()
                is_white_turn = board.turn
                phase = MoveClassifier.classify_game_phase(current_fen, move_number)

                # Make the move to get post-move position
                board.push(move)

                # Analyze new position (Post-move Eval)
                analysis = self.analyzer.analyze_position(board)
                curr_eval = analysis["evaluation"]
                curr_best_move = analysis["best_move"]

                # Determine if this was player's move
                # Note: board.turn is now the opponent's turn (after push)
                # So we check the turn *before* the push (is_white_turn)
                is_player_move = (is_white_turn and game.player_color == "white") or (
                    not is_white_turn and game.player_color == "black"
                )

                move_class = None
                if move_number > 0:
                    is_book = False  # TODO: Book check

                    # Classify based on shift from Prev -> Curr
                    move_class = MoveClassifier.classify_move(
                        prev_eval, curr_eval, is_white_turn, is_book
                    )

                    # Store classification
                    if is_player_move:
                        classification = move_class["classification"]
                        if classification in move_counts:
                            move_counts[classification] += 1

                        if phase == "opening":
                            opening_classifications.append(move_class)
                        elif phase == "middlegame":
                            middlegame_classifications.append(move_class)
                        else:
                            endgame_classifications.append(move_class)

                        all_classifications.append(move_class)
                    else:
                        opponent_classifications.append(move_class)

                # Store position data for THIS move
                position_data = {
                    "game_id": game.id,
                    "move_number": move_number,
                    "fen": current_fen,  # FEN *before* move (standard convention)
                    "evaluation": prev_eval,  # Eval *before* move (Context for the move)
                    "best_move": prev_best_move,  # Best move available *before*
                    "player_move": move.uci(),
                    "is_mistake": move_class["is_mistake"] if move_class else False,
                    "is_blunder": move_class["is_blunder"] if move_class else False,
                    "eval_drop": move_class["eval_drop"] if move_class else 0,
                    "move_classification": move_class["classification"] if move_class else None,
                    "game_phase": phase,
                }
                positions_data.append(position_data)

                # Update state for next iteration
                prev_eval = curr_eval
                prev_best_move = curr_best_move

            # Calculate accuracies
            overall_accuracy = MoveClassifier.calculate_accuracy_from_moves(all_classifications)
            opponent_accuracy = MoveClassifier.calculate_accuracy_from_moves(
                opponent_classifications
            )
            opening_accuracy = MoveClassifier.calculate_accuracy_from_moves(opening_classifications)
            middlegame_accuracy = MoveClassifier.calculate_accuracy_from_moves(
                middlegame_classifications
            )
            endgame_accuracy = MoveClassifier.calculate_accuracy_from_moves(endgame_classifications)

            # Prepare summary
            summary = {
                "game_id": game.id,
                "total_moves": move_number,
                "player_accuracy": overall_accuracy,
                "opponent_accuracy": opponent_accuracy,
                "opening_accuracy": opening_accuracy,
                "middlegame_accuracy": middlegame_accuracy,
                "endgame_accuracy": endgame_accuracy,
                "move_counts": move_counts,
                "analyzed": True,
            }

            # Save to database
            if save_to_db:
                self._save_analysis(game, positions_data, summary)

            print(
                f"  ✓ Moves: {move_number} | Accuracy: {overall_accuracy}% | Mistakes: {move_counts['mistake']} | Blunders: {move_counts['blunder']}"
            )

            return summary

        except Exception as e:
            print(f"❌ Error analyzing game: {e}")
            import traceback

            traceback.print_exc()
            return {}

    def _save_analysis(self, game: Game, positions_data: list[dict], summary: dict):
        """Save analysis results to database."""
        try:
            # Delete existing positions for this game
            self.session.query(Position).filter_by(game_id=game.id).delete()

            # Create new positions
            for pos_data in positions_data:
                position = Position(**pos_data)
                self.session.add(position)

            # Update game with statistics
            game.analyzed = True
            game.analysis_date = datetime.utcnow()
            game.total_moves = summary["total_moves"]
            game.player_accuracy = summary["player_accuracy"]
            game.opponent_accuracy = summary["opponent_accuracy"]
            game.opening_accuracy = summary["opening_accuracy"]
            game.middlegame_accuracy = summary["middlegame_accuracy"]
            game.endgame_accuracy = summary["endgame_accuracy"]

            # Update move counts
            move_counts = summary["move_counts"]
            game.brilliant_moves = move_counts.get("brilliant", 0)
            game.great_moves = move_counts.get("great", 0)
            game.best_moves = move_counts.get("best", 0)
            game.excellent_moves = move_counts.get("excellent", 0)
            game.good_moves = move_counts.get("good", 0)
            game.inaccuracy_moves = move_counts.get("inaccuracy", 0)
            game.mistake_moves = move_counts.get("mistake", 0)
            game.miss_moves = move_counts.get("miss", 0)
            game.blunder_moves = move_counts.get("blunder", 0)

            # Explicitly add to session and commit
            self.session.add(game)
            self.session.commit()
            print("  💾 Saved to database")

        except Exception as e:
            self.session.rollback()
            print(f"❌ Error saving analysis: {e}")
            import traceback

            traceback.print_exc()

    def analyze_unanalyzed_games(self, limit: Optional[int] = None):
        """Analyze all unanalyzed games in database."""
        unanalyzed = self.session.query(Game).filter_by(analyzed=False).order_by(Game.date.desc())

        if limit:
            unanalyzed = unanalyzed.limit(limit)

        games = unanalyzed.all()

        print(f"\n📊 Found {len(games)} unanalyzed games")
        print("=" * 60)

        for i, game in enumerate(games, 1):
            print(f"\n[{i}/{len(games)}] {game.platform} - {game.date.date()}")
            self.analyze_game(game)

        print("\n✅ Analysis complete!")


if __name__ == "__main__":
    # Test game analysis
    with GameAnalyzer() as analyzer:
        analyzer.analyze_unanalyzed_games(limit=5)
