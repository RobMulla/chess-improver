"""Enhanced move classification for detailed game statistics."""
from typing import Dict, Optional


class MoveClassifier:
    """Classifies chess moves based on evaluation changes."""
    
    # Thresholds for move classification (centipawns)
    # Made MUCH stricter to actually detect mistakes
    BRILLIANT_THRESHOLD = 300  # Sacrificial move that maintains advantage
    BEST_THRESHOLD = 10        # Perfect move (<10cp loss)
    EXCELLENT_THRESHOLD = 25   # Near-perfect (10-25cp loss)
    GOOD_THRESHOLD = 50        # Solid move (25-50cp loss)
    INACCURACY_THRESHOLD = 100 # Sub-optimal (50-100cp loss)
    MISTAKE_THRESHOLD = 200    # Clear error (100-200cp loss)
    # Blunder is anything above MISTAKE_THRESHOLD (200cp+)
    
    @staticmethod
    def classify_move(
        prev_eval: float,
        curr_eval: float,
        best_eval: float,
        is_white_turn: bool,
        is_book_move: bool = False
    ) -> Dict:
        """
        Classify a move based on WIN% loss (not centipawns).
        
        Uses Lichess's Win% conversion for accurate classification
        that matches Chess.com/Lichess standards.
        
        Args:
            prev_eval: Evaluation before move (in centipawns)
            curr_eval: Evaluation after  move (in centipawns)
            best_eval: Best possible evaluation (from engine)
            is_white_turn: Whether it's white's turn
            is_book_move: Whether move is from opening book
            
        Returns:
            Dict with classification, eval_drop, win_loss, and flags
        """
        from src.analysis.win_chance import win_chance_loss, classify_by_win_loss
        
        if is_book_move:
            return {
                "classification": "book",
                "eval_drop": 0,
                "win_loss": 0,
                "is_mistake": False,
                "is_blunder": False,
                "is_miss": False
            }
        
        # Calculate both CP drop (for backward compat) and Win% loss
        if is_white_turn:
            eval_drop = best_eval - curr_eval
        else:
            eval_drop = curr_eval - best_eval
        
        eval_drop = max(0, eval_drop)
        
        # Calculate Win% loss (the key metric)
        win_loss = win_chance_loss(best_eval, curr_eval, is_white_turn)
        
        # Classify by Win% loss
        result = classify_by_win_loss(win_loss)
        
        # Add eval_drop for compatibility
        result["eval_drop"] = eval_drop
        
        # Detect "Great" moves (best move in critical position)
        # Critical = position with high evaluation swing potential (>300cp range)
        if result["classification"] == "best":
            position_complexity = abs(best_eval - prev_eval)
            if position_complexity > 300:
                result["classification"] = "great"
        
        # TODO: Detect "Brilliant" moves (sacrifices that work)
        # Requires checking material balance before/after
        
        return result
    
    @staticmethod
    def calculate_accuracy_from_moves(classifications: list) -> float:
        """
        Calculate overall accuracy from move classifications.
        
        Prefers Win% loss if available, falls back to CP-based calculation.
        """
        if not classifications:
            return 0.0
        
        # Try Win% based calculation first (more accurate)
        if classifications[0].get("win_loss") is not None:
            from src.analysis.win_chance import calculate_accuracy_from_win_losses
            win_losses = [c.get("win_loss", 0) for c in classifications]
            return calculate_accuracy_from_win_losses(win_losses)
        
        # Fall back to old CP-based calculation
        total_eval_drop = sum(c.get("eval_drop", 0) for c in classifications)
        num_moves = len(classifications)
        
        # Average eval drop per move
        avg_drop = total_eval_drop / num_moves if num_moves > 0 else 0
        
        # Convert to accuracy percentage (chess.com formula approximation)
        # Perfect play (0 drop) = 100%, each 10cp drop reduces accuracy
        accuracy = max(0, 100 - (avg_drop / 10))
        
        return round(accuracy, 1)
    
    @staticmethod
    def classify_game_phase(fen: str, move_number: int) -> str:
        """
        Determine game phase from position (FEN) and move number.
        
        More accurate than move number alone:
        - Opening: Early moves with most pieces on board
        - Middlegame: Active pieces, queens still on board
        - Endgame: Queens traded or few pieces remaining
        
        Args:
            fen: Position in FEN notation
            move_number: Move number in the game
            
        Returns:
            "opening", "middlegame", or "endgame"
        """
        # Parse FEN to get piece placement
        board_section = fen.split(' ')[0]
        
        # Count pieces (excluding kings and pawns)
        pieces = board_section.replace('/', '')
        
        # Count major and minor pieces for each side
        white_queens = pieces.count('Q')
        black_queens = pieces.count('q')
        white_rooks = pieces.count('R')
        black_rooks = pieces.count('r')
        white_bishops = pieces.count('B')
        black_bishops = pieces.count('b')
        white_knights = pieces.count('N')
        black_knights = pieces.count('n')
        
        # Total major pieces (queens + rooks)
        total_major = white_queens + black_queens + white_rooks + black_rooks
        
        # Total minor pieces (bishops + knights)
        total_minor = white_bishops + black_bishops + white_knights + black_knights
        
        # Total non-pawn, non-king pieces
        total_pieces = total_major + total_minor
        
        # Game phase classification
        # Endgame: No queens OR very few pieces left
        if (white_queens == 0 and black_queens == 0) or total_pieces <= 6:
            return "endgame"
        
        # Opening: Early moves with most pieces still on board
        # (14+ pieces remaining, typically first 10-15 moves)
        if move_number <= 12 and total_pieces >= 14:
            return "opening"
        
        # Middlegame: Everything else
        return "middlegame"

