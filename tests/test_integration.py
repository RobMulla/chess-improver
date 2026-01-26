"""Integration tests for game analysis pipeline."""
import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.analysis.game_analyzer import GameAnalyzer
from src.database.models import get_session, Game
from datetime import datetime


class TestGameAnalysisIntegration:
    """Test complete game analysis with real PGN data."""
    
    def test_analyze_simple_game(self):
        """Test analyzing a simple game with known result."""
        # Simple 4-move checkmate (Scholar's Mate)
        pgn = """[Event "Test Game"]
[Site "Test"]
[Date "2024.01.01"]
[White "Player1"]
[Black "Player2"]
[Result "1-0"]

1. e4 e5 2. Bc4 Nc6 3. Qh5 Nf6 4. Qxf7# 1-0"""
        
        session = get_session()
        game = Game(
            platform="test",
            game_id="TEST_SCHOLARS_MATE",
            pgn=pgn,
            date=datetime.utcnow(),
            result="1-0",
            player_color="white"
        )
        session.add(game)
        session.commit()
        
        try:
            with GameAnalyzer() as analyzer:
                result = analyzer.analyze_game(game, save_to_db=True)
                
                # Verify basic structure
                assert 'total_moves' in result
                assert 'player_accuracy' in result
                assert 'move_counts' in result
                
                # Should have positions
                assert result['total_moves'] > 0
                
                # White scored checkmate with simple moves, should be high accuracy
                assert result['player_accuracy'] >= 80.0
                
                print(f"\n  ✓ Scholar's Mate: {result['total_moves']} moves, "
                      f"{result['player_accuracy']:.1f}% accuracy")
                
        finally:
            # Cleanup
            session.delete(game)
            session.commit()
            session.close()
    
    def test_analyze_game_with_blunder(self):
        """Test game where Black hangs the queen (obvious blunder)."""
        # Game where Black blunders queen on move 2
        pgn = """[Event "Blunder Test"]
[Site "Test"]
[Date "2024.01.01"]
[White "AI"]
[Black "Player"]
[Result "1-0"]

1. e4 e5 2. Nf3 Qf6 3. Nxe5 Qxe5 4. d4 1-0"""
        
        session = get_session()
        game = Game(
            platform="test",
            game_id="TEST_BLUNDER",
            pgn=pgn,
            date=datetime.utcnow(),
            result="1-0",
            player_color="black"
        )
        session.add(game)
        session.commit()
        
        try:
            with GameAnalyzer() as analyzer:
                result = analyzer.analyze_game(game, save_to_db=True)
                
                # Black (us) should have lower accuracy due to weak opening
                # Qf6 is not a great move
                assert result['player_accuracy'] < 100.0
                
                print(f"\n  ✓ Blunder game: {result['player_accuracy']:.1f}% accuracy, "
                      f"{result['move_counts'].get('mistake', 0)} mistakes, "
                      f"{result['move_counts'].get('blunder', 0)} blunders")
                
        finally:
            session.delete(game)
            session.commit()
            session.close()
    
    def test_perfect_opening(self):
        """Test standard opening moves get high scores."""
        # Italian Game - well-known good moves
        pgn = """[Event "Perfect Opening"]
[Site "Test"]
[Date "2024.01.01"]
[White "Player"]
[Black "Opponent"]
[Result "*"]

1. e4 e5 2. Nf3 Nc6 3. Bc4 Bc5 4. d3 Nf6 5. O-O O-O *"""
        
        session = get_session()
        game = Game(
            platform="test",
            game_id="TEST_PERFECT_OPENING",
            pgn=pgn,
            date=datetime.utcnow(),
            result="1/2-1/2",
            player_color="white"
        )
        session.add(game)
        session.commit()
        
        try:
            with GameAnalyzer() as analyzer:
                result = analyzer.analyze_game(game, save_to_db=True)
                
                # Standard opening moves should score very high
                assert result['player_accuracy'] >= 95.0
                assert result['opening_accuracy'] >= 95.0
                
                # Should have mostly "best" or "great" moves
                best_moves = result['move_counts'].get('best', 0)
                great_moves = result['move_counts'].get('great', 0)
                total_good = best_moves + great_moves
                
                assert total_good >= result['total_moves'] * 0.7  # At least 70% good
                
                print(f"\n  ✓ Perfect opening: {result['opening_accuracy']:.1f}% accuracy, "
                      f"{best_moves} best moves, {great_moves} great moves")
                
        finally:
            session.delete(game)
            session.commit()
            session.close()
    
    def test_game_phase_classification(self):
        """Test that moves are properly classified by phase."""
        pgn = """[Event "Phase Test"]
[Site "Test"]
[Date "2024.01.01"]
[White "Player"]
[Black "Opponent"]
[Result "*"]

1. e4 e5 2. Nf3 Nc6 3. Bc4 Bc5 4. d3 Nf6 5. O-O O-O 
6. Nc3 d6 7. Bg5 h6 8. Bh4 g5 9. Bg3 Bg4 10. h3 Bxf3 
11. Qxf3 Nd4 12. Qd1 Qd7 13. Nd5 Nxd5 14. exd5 c6 
15. dxc6 bxc6 16. c3 Nc2 17. Qxc2 *"""
        
        session = get_session()
        game = Game(
            platform="test",
            game_id="TEST_PHASES",
            pgn=pgn,
            date=datetime.utcnow(),
            result="*",
            player_color="white"
        )
        session.add(game)
        session.commit()
        
        try:
            with GameAnalyzer() as analyzer:
                result = analyzer.analyze_game(game, save_to_db=True)
                
                # Should have opening, middlegame stats
                assert 'opening_accuracy' in result
                assert 'middlegame_accuracy' in result
                
                # All three phases should have some accuracy value
                assert result['opening_accuracy'] is not None
                assert result['middlegame_accuracy'] is not None
                
                print(f"\n  ✓ Phase test: Opening {result['opening_accuracy']:.1f}%, "
                      f"Middlegame {result['middlegame_accuracy']:.1f}%")
                
        finally:
            session.delete(game)
            session.commit()
            session.close()


class TestAccuracyFormula:
    """Test accuracy calculation matches expectations."""
    
    def test_zero_eval_drop_is_100_percent(self):
        """Test perfect moves = 100% accuracy."""
        from src.analysis.move_classifier import MoveClassifier
        
        # All perfect moves (0 eval drop)
        moves = [{'classification': 'best', 'eval_drop': 0}] * 10
        accuracy = MoveClassifier.calculate_accuracy_from_moves(moves)
        
        assert accuracy == 100.0
    
    def test_consistent_small_drops(self):
        """Test consistent small mistakes."""
        from src.analysis.move_classifier import MoveClassifier
        
        # All moves lose 20cp (good moves)
        moves = [{'classification': 'good', 'eval_drop': 20}] * 10
        accuracy = MoveClassifier.calculate_accuracy_from_moves(moves)
        
        # Average drop 20cp → accuracy should be 100 - (20/10) = 98.0
        assert 97.0 <= accuracy <= 99.0
    
    def test_one_big_blunder(self):
        """Test one blunder among perfect moves."""
        from src.analysis.move_classifier import MoveClassifier
        
        # 9 perfect + 1 blunder (300cp)
        moves = (
            [{'classification': 'best', 'eval_drop': 0}] * 9 +
            [{'classification': 'blunder', 'eval_drop': 300}] * 1
        )
        accuracy = MoveClassifier.calculate_accuracy_from_moves(moves)
        
        # Average drop: 300/10 = 30cp → accuracy = 100 - 3 = 97.0
        assert 96.0 <= accuracy <= 98.0


def run_integration_tests():
    """Run integration tests."""
    print("🧪 Running Integration Tests (with Stockfish)...\n")
    print("⚠️  This will take a minute - analyzing real games\n")
    
    exit_code = pytest.main([
        __file__,
        "-v",
        "-s",
        "--tb=short"
    ])
    
    if exit_code == 0:
        print("\n✅ All integration tests passed!")
    else:
        print(f"\n❌ Some tests failed (exit code {exit_code})")
    
    return exit_code


if __name__ == "__main__":
    run_integration_tests()
