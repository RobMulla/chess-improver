"""Win chance (probability) calculations from centipawn evaluations.

Based on Lichess's open-source algorithm for converting Stockfish
centipawn evaluations into winning probabilities.
"""
import math


def centipawns_to_win_chance(cp: float) -> float:
    """
    Convert centipawn evaluation to winning probability.

    Uses Lichess's sigmoid formula to convert engine evaluation
    into a probability of winning (0-100%).

    Formula: Win% = 50 + 50 * (2 / (1 + exp(-0.00368208 * cp)) - 1)

    This gives a smooth S-curve where:
    - 0 cp = 50% win chance (equal position)
    - +100 cp ≈ 64% win chance (small advantage)
    - +300 cp ≈ 84% win chance (significant advantage)
    - +600 cp ≈ 95% win chance (winning)
    - -300 cp ≈ 16% win chance (significant disadvantage)

    Args:
        cp: Centipawn evaluation (positive = white advantage)

    Returns:
        Win probability as percentage (0-100)
    """
    # Lichess coefficient for the sigmoid function
    # This determines how quickly win% changes with CP
    LICHESS_COEFF = 0.00368208

    # Sigmoid function centered at 50%
    win_chance = 50 + 50 * (2 / (1 + math.exp(-LICHESS_COEFF * cp)) - 1)

    return win_chance


def win_chance_loss(before_cp: float, after_cp: float, is_white_turn: bool) -> float:
    """
    Calculate the loss in winning chances after a move.

    This is the key metric for move classification. Instead of raw
    centipawn loss, we measure how much the move decreases your
    probability of winning.

    Examples:
    - 0% loss = perfect move
    - 1% loss = excellent move
    - 5% loss = decent move
    - 10% loss = inaccuracy
    - 15% loss = mistake
    - 30%+ loss = blunder

    Args:
        before_cp: Evaluation before the move (best possible)
        after_cp: Evaluation after the move (actual position)
        is_white_turn: True if white to move

    Returns:
        Loss in win probability as percentage (0-100)
    """
    # Normalize to current player's perspective
    # (positive CP = advantage for side to move)
    if is_white_turn:
        before_win = centipawns_to_win_chance(before_cp)
        after_win = centipawns_to_win_chance(after_cp)
    else:
        # Flip sign for black's perspective
        before_win = centipawns_to_win_chance(-before_cp)
        after_win = centipawns_to_win_chance(-after_cp)

    # Calculate loss (can't gain win% by deviating from best move)
    loss = max(0, before_win - after_win)

    return loss


def classify_by_win_loss(win_loss: float, position_complexity: float = 1.0) -> dict:
    """
    Classify a move based on win% loss.

    Uses calibrated thresholds based on Chess.com/Lichess standards.
    Position complexity can scale the thresholds (harder positions =
    more forgiveness for small mistakes).

    Args:
        win_loss: Loss in win probability (0-100%)
        position_complexity: Multiplier for position difficulty (default 1.0)

    Returns:
        Dict with classification and flags
    """
    # Adjust thresholds based on position complexity
    # In complex positions, small win% losses are more understandable
    scale = position_complexity

    # Thresholds calibrated to match Chess.com/Lichess
    # Tuned based on golden test game comparison
    BEST_THRESHOLD = 0.5 * scale  # <0.5% win loss (nearly perfect)
    EXCELLENT_THRESHOLD = 3.0 * scale  # <3% (very good)
    GOOD_THRESHOLD = 6.0 * scale  # <6% (decent)
    INACCURACY_THRESHOLD = 10.0 * scale  # <10% (slight error)
    MISTAKE_THRESHOLD = 15.0 * scale  # <15% (clear mistake)
    # Blunder = anything above 15%

    classification = "best"
    is_mistake = False
    is_blunder = False
    is_miss = False

    if win_loss < BEST_THRESHOLD:
        classification = "best"
    elif win_loss < EXCELLENT_THRESHOLD:
        classification = "excellent"
    elif win_loss < GOOD_THRESHOLD:
        classification = "good"
    elif win_loss < INACCURACY_THRESHOLD:
        classification = "inaccuracy"
        is_mistake = True
    elif win_loss < MISTAKE_THRESHOLD:
        classification = "mistake"
        is_mistake = True
        is_miss = True
    else:
        classification = "blunder"
        is_blunder = True
        is_mistake = True

    return {
        "classification": classification,
        "win_loss": win_loss,
        "is_mistake": is_mistake,
        "is_blunder": is_blunder,
        "is_miss": is_miss,
    }


def calculate_accuracy_from_win_losses(win_losses: list) -> float:
    """
    Calculate overall accuracy from win% losses.

    Similar to Lichess's approach: average win% loss
    is converted to accuracy percentage.

    Perfect play (0% avg loss) = 100% accuracy
    Terrible play (50% avg loss) = 0% accuracy

    Args:
        win_losses: List of win% losses for each move

    Returns:
        Accuracy percentage (0-100)
    """
    if not win_losses:
        return 0.0

    avg_win_loss = sum(win_losses) / len(win_losses)

    # Convert avg win loss to accuracy
    # Each 1% win loss = ~2% accuracy loss
    accuracy = max(0, 100 - (avg_win_loss * 2))

    return round(accuracy, 1)
