"""Additional tests for Phase 1 features: cache, jobs, classification."""
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.analysis.cache import AnalysisCache, get_cache
from src.analysis.move_classifier import MoveClassifier
import chess


class TestRedisCache:
    """Test Redis caching functionality."""
    
    def test_cache_initialization(self):
        """Test cache can be initialized."""
        cache = AnalysisCache()
        assert cache is not None
        # Should work even if Redis is down
    
    def test_cache_set_and_get(self):
        """Test basic cache operations."""
        cache = get_cache()
        
        test_fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
        test_data = {"score": 50, "best_move": "e7e5", "depth": 20}
        
        # Set
        success = cache.set_evaluation(test_fen, test_data)
        if cache.enabled:
            assert success == True
            
            # Get
            retrieved = cache.get_evaluation(test_fen)
            assert retrieved == test_data
    
    def test_cache_miss(self):
        """Test cache miss returns None."""
        cache = get_cache()
        result = cache.get_evaluation("nonexistent_fen")
        assert result is None
    
    def test_cache_stats(self):
        """Test cache statistics."""
        cache = get_cache()
        stats = cache.get_stats()
        
        assert "enabled" in stats
        if stats["enabled"]:
            assert "cache_hits" in stats or "total_keys" in stats


class TestMoveClassificationThresholds:
    """Test that move classification actually detects mistakes."""
    
    def test_perfect_move_is_best(self):
        """Test perfect move (0 eval drop) is classified as best."""
        result = MoveClassifier.classify_move(
            prev_eval=100,
            curr_eval=100,  # Same eval (playing best move)
            best_eval=100,
            is_white_turn=True
        )
        assert result['classification'] in ['best', 'excellent', 'good']
        assert result['is_mistake'] == False
        assert result['eval_drop'] == 0
    
    def test_small_mistake_detected(self):
        """Test small mistake (50cp) is classified as inaccuracy."""
        result = MoveClassifier.classify_move(
            prev_eval=100,
            curr_eval=50,   # Lost 50cp
            best_eval=100,
            is_white_turn=True
        )
        # Should be inaccuracy (50-100cp range)
        assert result['classification'] in ['inaccuracy', 'good']
        assert result['eval_drop'] >= 0
    
    def test_mistake_detected(self):
        """Test mistake (150cp drop) is properly classified."""
        result = MoveClassifier.classify_move(
            prev_eval=100,
            curr_eval=-50,  # Lost 150cp
            best_eval=100,
            is_white_turn=True
        )
        assert result['classification'] == 'mistake'
        assert result['is_mistake'] == True
        assert result['eval_drop'] >= 100
    
    def test_blunder_detected(self):
        """Test blunder (300cp drop) is properly classified."""
        result = MoveClassifier.classify_move(
            prev_eval=100,
            curr_eval=-200,  # Lost 300cp  
            best_eval=100,
            is_white_turn=True
        )
        assert result['classification'] == 'blunder'
        assert result['is_blunder'] == True
        assert result['eval_drop'] >= 200
    
    def test_black_perspective(self):
        """Test classification works from Black's perspective."""
        # For Black, negative eval = advantage
        # Going from -100 (slight advantage) to +200 (losing) = 300cp blunder
        result = MoveClassifier.classify_move(
            prev_eval=-100,  # Black was slightly better
            curr_eval=200,   # Now White is winning (Black blundered!)
            best_eval=-100,  # Best was to maintain -100
            is_white_turn=False  # Black to move
        )
        assert result['classification'] == 'blunder'
        assert result['is_blunder'] == True
        # Win% loss should be significant (going from ~59% to ~25% = ~34% loss)


class TestGamePhaseDetection:
    """Test FEN-based game phase detection."""
    
    def test_starting_position_is_opening(self):
        """Test starting position detected as opening."""
        fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
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


class TestAccuracyCalculation:
    """Test accuracy calculation formula."""
    
    def test_perfect_play_is_100_percent(self):
        """Test all best moves = 100% accuracy."""
        classifications = [{'classification': 'best', 'eval_drop': 0}] * 20
        accuracy = MoveClassifier.calculate_accuracy_from_moves(classifications)
        assert accuracy == 100.0
    
    def test_all_blunders_is_low_accuracy(self):
        """Test all blunders = very low accuracy."""
        # Big blunders with Win% losses
        classifications = [{'classification': 'blunder', 'eval_drop': 300, 'win_loss': 25.0}] * 20
        accuracy = MoveClassifier.calculate_accuracy_from_moves(classifications)
        assert 48 < accuracy < 52  # Formula: 100 - (25*2) = 50%
    
    def test_mixed_moves_reasonable_accuracy(self):
        """Test mix of moves gives reasonable accuracy."""
        classifications = (
            [{'classification': 'best', 'eval_drop': 0}] * 10 +
            [{'classification': 'good', 'eval_drop': 30}] * 5 +
            [{'classification': 'mistake', 'eval_drop': 150}] * 3 +
            [{'classification': 'blunder', 'eval_drop': 300}] * 2
        )
        accuracy = MoveClassifier.calculate_accuracy_from_moves(classifications)
        assert 90.0 < accuracy < 96.0  # Mixed moves should be high-90s


class TestBackgroundJobs:
    """Test RQ background job system."""
    
    def test_queue_import(self):
        """Test we can import job queue components."""
        try:
            from redis import Redis
            from rq import Queue
            assert True
        except ImportError:
            pytest.skip("Redis/RQ not available")
    
    def test_worker_import(self):
        """Test worker module can be imported."""
        try:
            from src.workers.analyzer_worker import analyze_game_task
            assert analyze_game_task is not None
        except ImportError as e:
            pytest.fail(f"Worker import failed: {e}")


def run_tests():
    """Run all tests."""
    print("🧪 Running Extended Test Suite...\n")
    
    exit_code = pytest.main([
        __file__,
        "-v",
        "-s",
        "--tb=short",
        "-k", "not test_queue_import"  # Skip if Redis not running
    ])
    
    if exit_code == 0:
        print("\n✅ All tests passed!")
    else:
        print(f"\n❌ Some tests failed (exit code {exit_code})")
    
    return exit_code


if __name__ == "__main__":
    run_tests()
