"""Tests for win chance calculations."""

import pytest

from src.analysis.win_chance import (
    calculate_accuracy_from_win_losses,
    centipawns_to_win_chance,
    classify_by_win_loss,
    win_chance_loss,
)


class TestCentipawnsToWinChance:
    """Test CP to Win% conversion."""

    def test_equal_position(self):
        """Test 0cp = 50% win chance."""
        assert abs(centipawns_to_win_chance(0) - 50.0) < 0.1

    def test_small_advantage(self):
        """Test +100cp ≈ 59% win chance."""
        win_chance = centipawns_to_win_chance(100)
        assert 58 < win_chance < 60

    def test_significant_advantage(self):
        """Test +300cp ≈ 75% win chance."""
        win_chance = centipawns_to_win_chance(300)
        assert 74 < win_chance < 76

    def test_winning_position(self):
        """Test +600cp ≈ 90% win chance."""
        win_chance = centipawns_to_win_chance(600)
        assert 89 < win_chance < 91

    def test_disadvantage(self):
        """Test -300cp ≈ 25% win chance."""
        win_chance = centipawns_to_win_chance(-300)
        assert 24 < win_chance < 26

    def test_symmetric(self):
        """Test that +X and -X are symmetric around 50%."""
        win_plus = centipawns_to_win_chance(200)
        win_minus = centipawns_to_win_chance(-200)
        assert abs((win_plus - 50) - (50 - win_minus)) < 0.1


class TestWinChanceLoss:
    """Test win% loss calculations."""

    def test_perfect_move_white(self):
        """Test perfect move for white (no loss)."""
        # Best move maintains +100cp advantage
        loss = win_chance_loss(100, 100, is_white_turn=True)
        assert loss < 0.1  # Nearly 0

    def test_perfect_move_black(self):
        """Test perfect move for black (no loss)."""
        # Best move maintains -100cp (black advantage)
        loss = win_chance_loss(-100, -100, is_white_turn=False)
        assert loss < 0.1

    def test_small_mistake_white(self):
        """Test small mistake for white."""
        # Drop from +100 to 0 (equal)
        loss = win_chance_loss(100, 0, is_white_turn=True)
        # Should lose about 9% win chance (59% → 50%)
        assert 8 < loss < 10

    def test_big_blunder_white(self):
        """Test blunder for white."""
        # Drop from +100 to -300 (now losing)
        loss = win_chance_loss(100, -300, is_white_turn=True)
        # Should lose about 34% win chance (59% → 25%)
        assert 33 < loss < 35

    def test_can_not_gain(self):
        """Test that win% loss is never negative."""
        # Playing better than "best" shouldn't happen
        loss = win_chance_loss(0, 100, is_white_turn=True)
        assert loss == 0  # Can't gain by deviating


class TestClassifyByWinLoss:
    """Test move classification."""

    def test_best_move(self):
        """Test classification of best move."""
        result = classify_by_win_loss(0.4)  # 0.4% loss
        assert result["classification"] == "best"
        assert result["is_mistake"] is False

    def test_excellent_move(self):
        """Test excellent move classification."""
        result = classify_by_win_loss(2.0)  # 2% loss
        assert result["classification"] == "excellent"
        assert result["is_mistake"] is False

    def test_good_move(self):
        """Test good move classification."""
        result = classify_by_win_loss(4.0)  # 4% loss
        assert result["classification"] == "good"
        assert result["is_mistake"] is False

    def test_inaccuracy(self):
        """Test inaccuracy classification."""
        result = classify_by_win_loss(8.0)  # 8% loss
        assert result["classification"] == "inaccuracy"
        assert result["is_mistake"] is True
        assert result["is_blunder"] is False

    def test_mistake(self):
        """Test mistake classification."""
        result = classify_by_win_loss(12.0)  # 12% loss
        assert result["classification"] == "mistake"
        assert result["is_mistake"] is True
        assert result["is_miss"] is True

    def test_blunder(self):
        """Test blunder classification."""
        result = classify_by_win_loss(20.0)  # 20% loss
        assert result["classification"] == "blunder"
        assert result["is_blunder"] is True


class TestAccuracyCalculation:
    """Test accuracy calculation from win losses."""

    def test_perfect_play(self):
        """Test 100% accuracy for perfect play."""
        win_losses = [0, 0, 0, 0, 0]
        accuracy = calculate_accuracy_from_win_losses(win_losses)
        assert accuracy == 100.0

    def test_good_play(self):
        """Test ~90% accuracy for good play."""
        win_losses = [1, 2, 3, 2, 1, 3, 2]  # Avg 2% loss
        accuracy = calculate_accuracy_from_win_losses(win_losses)
        assert 94 < accuracy < 98  # Should be ~96%

    def test_mistakes(self):
        """Test lower accuracy with mistakes."""
        win_losses = [1, 2, 10, 2, 1, 12, 2]  # Avg ~4.3% loss
        accuracy = calculate_accuracy_from_win_losses(win_losses)
        assert 88 < accuracy < 94  # Should be ~91%

    def test_blunders(self):
        """Test much lower accuracy with blunders."""
        win_losses = [2, 3, 20, 2, 25, 3, 2]  # Avg ~8.1% loss
        accuracy = calculate_accuracy_from_win_losses(win_losses)
        assert 80 < accuracy < 88  # Should be ~84%


def run_tests():
    """Run all win chance tests."""
    print("🧪 Testing Win% Conversion Algorithm...\n")

    exit_code = pytest.main([__file__, "-v", "-s", "--tb=short"])

    if exit_code == 0:
        print("\n✅ All Win% tests passed!")
    else:
        print(f"\n❌ Some tests failed (exit code {exit_code})")

    return exit_code


if __name__ == "__main__":
    run_tests()
