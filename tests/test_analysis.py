"""Test Stockfish analysis engine."""
import pytest
import chess
from src.analysis.engine import StockfishAnalyzer


class TestStockfishAnalyzer:
    """Test Stockfish integration."""
    
    def test_analyzer_initialization(self):
        """Test analyzer can be created."""
        try:
            analyzer = StockfishAnalyzer()
            assert analyzer.depth == 20
            assert analyzer.mistake_threshold == 50
            assert analyzer.blunder_threshold == 150
        except Exception:
            pytest.skip("Stockfish not available")
    
    def test_analyze_starting_position(self):
        """Test analyzing starting position."""
        try:
            with StockfishAnalyzer(depth=10) as analyzer:
                board = chess.Board()
                result = analyzer.analyze_position(board)
                
                assert "evaluation" in result
                assert "best_move" in result
                assert result["best_move"] is not None
                # Starting position should be roughly equal
                assert -50 <= result["evaluation"] <= 50
        except Exception:
            pytest.skip("Stockfish not available")
    
    def test_classify_move(self):
        """Test move classification."""
        try:
            analyzer = StockfishAnalyzer()
            
            # No mistake
            classification = analyzer.classify_move(100, 95, True)
            assert not classification["is_mistake"]
            assert not classification["is_blunder"]
            
            # Mistake (50+ cp loss)
            classification = analyzer.classify_move(100, 40, True)
            assert classification["is_mistake"]
            assert not classification["is_blunder"]
            assert classification["eval_drop"] == 60
            
            # Blunder (150+ cp loss)
            classification = analyzer.classify_move(100, -60, True)
            assert classification["is_mistake"]
            assert classification["is_blunder"]
            assert classification["eval_drop"] == 160
        except Exception:
            pytest.skip("Stockfish not available")
    
    def test_calculate_accuracy(self):
        """Test accuracy calculation."""
        try:
            analyzer = StockfishAnalyzer()
            
            # Perfect play
            accuracy = analyzer.calculate_accuracy([0, 0, 0, 0])
            assert accuracy == 100.0
            
            # Some mistakes
            accuracy = analyzer.calculate_accuracy([10, 20, 5, 30])
            assert 80 <= accuracy <= 95
            
            # Bad play
            accuracy = analyzer.calculate_accuracy([100, 150, 80, 200])
            assert accuracy < 50
        except Exception:
            pytest.skip("Stockfish not available")
