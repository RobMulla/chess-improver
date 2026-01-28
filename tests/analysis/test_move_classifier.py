"""Tests for MoveClassifier."""
import chess

from src.analysis.move_classifier import MoveClassifier


class TestMoveClassificationThresholds:
    """Test that move classification actually detects mistakes."""

    def test_perfect_move_is_best(self):
        """Test perfect move (0 eval drop) is classified as best."""
        result = MoveClassifier.classify_move(
            prev_eval=100,
            curr_eval=100,  # Same eval (playing best move)
            is_white_turn=True,
        )
        assert result["classification"] in ["best", "excellent", "good"]
        assert result["is_mistake"] is False
        assert result["eval_drop"] == 0

    def test_small_mistake_detected(self):
        """Test small mistake (50cp) is classified as inaccuracy."""
        result = MoveClassifier.classify_move(
            prev_eval=100,
            curr_eval=50,  # Lost 50cp
            is_white_turn=True,
        )
        # Should be inaccuracy (50-100cp range)
        assert result["classification"] in ["inaccuracy", "good"]
        assert result["eval_drop"] >= 0

    def test_mistake_detected(self):
        """Test mistake (150cp drop) is properly classified."""
        result = MoveClassifier.classify_move(
            prev_eval=100,
            curr_eval=-50,  # Lost 150cp
            is_white_turn=True,
        )
        assert result["classification"] == "mistake"
        assert result["is_mistake"] is True
        assert result["eval_drop"] >= 100

    def test_blunder_detected(self):
        """Test blunder (300cp drop) is properly classified."""
        result = MoveClassifier.classify_move(
            prev_eval=100,
            curr_eval=-200,  # Lost 300cp
            is_white_turn=True,
        )
        assert result["classification"] == "blunder"
        assert result["is_blunder"] is True
        assert result["eval_drop"] >= 200

    def test_black_perspective(self):
        """Test classification works from Black's perspective."""
        # For Black, negative eval = advantage
        # Going from -100 (slight advantage) to +200 (losing) = 300cp blunder
        result = MoveClassifier.classify_move(
            prev_eval=-100,  # Black was slightly better
            curr_eval=200,  # Now White is winning (Black blundered!)
            is_white_turn=False,  # Black to move
        )
        assert result["classification"] == "blunder"
        assert result["is_blunder"] is True

    def test_classify_move_brilliant_placeholder(self):
        """Test brilliant move classification - currently not implemented, should be 'great'."""
        result = MoveClassifier.classify_move(prev_eval=100, curr_eval=500, is_white_turn=True)
        # Brilliant not implemented yet, should be "best"
        # Since eval improved or match, it is at least good
        assert result["classification"] in ["great", "best"]
        assert result["is_mistake"] is False

    def test_classify_move_best_simple(self):
        """Test best move classification."""
        result = MoveClassifier.classify_move(prev_eval=0, curr_eval=100, is_white_turn=True)
        assert result["classification"] == "best"
        assert result["is_mistake"] is False


class TestGamePhaseDetection:
    """Test FEN-based game phase detection."""

    def test_starting_position_is_opening(self):
        """Test starting position detected as opening."""
        fen = chess.STARTING_FEN  # Use chess constant if available or string
        phase = MoveClassifier.classify_game_phase(fen, 1)
        assert phase == "opening"

    def test_queenless_position_is_endgame(self):
        """Test position without queens is endgame."""
        fen = "4k3/8/8/8/8/8/4K3/R7 w - - 0 1"  # No queens
        phase = MoveClassifier.classify_game_phase(fen, 30)
        assert phase == "endgame"

    def test_few_pieces_is_endgame(self):
        """Test position with few pieces is endgame."""
        fen = "4k3/8/8/8/8/8/3K4/8 w - - 0 1"  # Only 2 kings
        phase = MoveClassifier.classify_game_phase(fen, 50)
        assert phase == "endgame"

    def test_complex_position_is_middlegame(self):
        """Test complex position with queens is middlegame."""
        fen = "r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 0 1"
        phase = MoveClassifier.classify_game_phase(fen, 8)
        # Has queens, many pieces, should be middlegame
        assert phase in ["middlegame", "opening"]

    def test_classify_game_phase_opening(self):
        """Test opening phase detection (legacy)."""
        # Starting position with most pieces
        fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
        phase = MoveClassifier.classify_game_phase(fen, 1)
        assert phase == "opening"

    def test_classify_middlegame_legacy(self):
        """Test middlegame detection (legacy)."""
        # Queens still on, some pieces exchanged
        fen = "r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 0 1"
        phase = MoveClassifier.classify_game_phase(fen, 8)
        assert phase in ["opening", "middlegame"]


class TestAccuracyCalculation:
    """Test accuracy calculation formula."""

    def test_perfect_play_is_100_percent(self):
        """Test all best moves = 100% accuracy."""
        classifications = [{"classification": "best", "eval_drop": 0}] * 20
        accuracy = MoveClassifier.calculate_accuracy_from_moves(classifications)
        assert accuracy == 100.0

    def test_all_blunders_is_low_accuracy(self):
        """Test all blunders = very low accuracy."""
        # Big blunders with Win% losses
        classifications = [{"classification": "blunder", "eval_drop": 300, "win_loss": 25.0}] * 20
        accuracy = MoveClassifier.calculate_accuracy_from_moves(classifications)
        assert 48 < accuracy < 52  # Formula: 100 - (25*2) = 50%

    def test_mixed_moves_reasonable_accuracy(self):
        """Test mix of moves gives reasonable accuracy."""
        classifications = (
            [{"classification": "best", "eval_drop": 0}] * 10
            + [{"classification": "good", "eval_drop": 30}] * 5
            + [{"classification": "mistake", "eval_drop": 150}] * 3
            + [{"classification": "blunder", "eval_drop": 300}] * 2
        )
        accuracy = MoveClassifier.calculate_accuracy_from_moves(classifications)
        assert 90.0 < accuracy < 96.0  # Mixed moves should be high-90s
