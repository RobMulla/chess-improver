"""Game analyzer using Stockfish."""
import chess
import chess.pgn
from io import StringIO
from typing import List, Dict, Optional
from datetime import datetime
from src.analysis.engine import StockfishAnalyzer
from src.database.models import get_session, Game, Position


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

    def analyze_game(self, game: Game, save_to_db: bool = True) -> Dict:
        """
        Analyze a complete game.
        
        Args:
            game: Game object from database
            save_to_db: Whether to save analysis to database
            
        Returns:
            Dict with analysis summary
        """
        print(f"🔍 Analyzing game {game.game_id}...")
        
        try:
            # Parse PGN
            pgn = StringIO(game.pgn)
            chess_game = chess.pgn.read_game(pgn)
            
            if not chess_game:
                print(f"⚠️ Could not parse PGN for game {game.game_id}")
                return {}
            
            # Analyze positions
            board = chess_game.board()
            positions_data = []
            eval_drops = []
            mistakes = 0
            blunders = 0
            
            prev_eval = 0
            move_number = 0
            
            for move in chess_game.mainline_moves():
                move_number += 1
                
                # Get evaluation before the move
                analysis = self.analyzer.analyze_position(board)
                curr_eval = analysis["evaluation"]
                best_move = analysis["best_move"]
                
                # Determine if this is player's move
                is_white_turn = board.turn
                is_player_move = (
                    (is_white_turn and game.player_color == "white") or
                    (not is_white_turn and game.player_color == "black")
                )
                
                # Classify move quality (only for player moves)
                move_classification = {"is_mistake": False, "is_blunder": False, "eval_drop": 0}
                if is_player_move and move_number > 1:
                    move_classification = self.analyzer.classify_move(
                        prev_eval, curr_eval, is_white_turn
                    )
                    
                    if move_classification["is_mistake"]:
                        mistakes += 1
                    if move_classification["is_blunder"]:
                        blunders += 1
                    
                    # Track eval drops for accuracy
                    eval_drops.append(max(0, move_classification["eval_drop"]))
                
                # Store position data
                position_data = {
                    "game_id": game.id,
                    "move_number": move_number,
                    "fen": board.fen(),
                    "evaluation": curr_eval,
                    "best_move": best_move,
                    "player_move": move.uci(),
                    "is_mistake": move_classification["is_mistake"],
                    "is_blunder": move_classification["is_blunder"],
                    "eval_drop": move_classification["eval_drop"],
                }
                positions_data.append(position_data)
                
                # Make the move
                board.push(move)
                prev_eval = -curr_eval  # Flip for next side
            
            # Calculate accuracy
            accuracy = self.analyzer.calculate_accuracy(eval_drops) if eval_drops else None
            
            # Save to database
            if save_to_db:
                self._save_analysis(game, positions_data)
            
            summary = {
                "game_id": game.id,
                "total_moves": move_number,
                "mistakes": mistakes,
                "blunders": blunders,
                "accuracy": accuracy,
                "analyzed": True,
            }
            
            print(f"  ✓ Moves: {move_number} | Mistakes: {mistakes} | Blunders: {blunders} | Accuracy: {accuracy}%")
            
            return summary
            
        except Exception as e:
            print(f"❌ Error analyzing game: {e}")
            return {}

    def _save_analysis(self, game: Game, positions_data: List[Dict]):
        """Save analysis results to database."""
        try:
            # Delete existing positions for this game
            self.session.query(Position).filter_by(game_id=game.id).delete()
            
            # Create new positions
            for pos_data in positions_data:
                position = Position(**pos_data)
                self.session.add(position)
            
            # Update game as analyzed
            game.analyzed = True
            game.analysis_date = datetime.utcnow()
            
            self.session.commit()
            
        except Exception as e:
            self.session.rollback()
            print(f"❌ Error saving analysis: {e}")

    def analyze_unanalyzed_games(self, limit: Optional[int] = None):
        """Analyze all unanalyzed games in database."""
        unanalyzed = (
            self.session.query(Game)
            .filter_by(analyzed=False)
            .order_by(Game.date.desc())
        )
        
        if limit:
            unanalyzed = unanalyzed.limit(limit)
        
        games = unanalyzed.all()
        
        print(f"\n📊 Found {len(games)} unanalyzed games")
        print("=" * 60)
        
        for i, game in enumerate(games, 1):
            print(f"\n[{i}/{len(games)}] {game.platform} - {game.date.date()}")
            self.analyze_game(game)
        
        print(f"\n✅ Analysis complete!")


if __name__ == "__main__":
    # Test game analysis
    with GameAnalyzer() as analyzer:
        analyzer.analyze_unanalyzed_games(limit=5)
