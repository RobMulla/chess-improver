"""Background job worker for game analysis."""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.analysis.game_analyzer import GameAnalyzer
from src.database.models import get_session, Game
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def analyze_game_task(game_id: int) -> dict:
    """
    Background task to analyze a game

.
    
    Args:
        game_id: ID of game to analyze
        
    Returns:
        Analysis result dict
    """
    logger.info(f"🔍 Starting analysis of game {game_id}")
    
    session = get_session()
    game = session.query(Game).get(game_id)
    
    if not game:
        logger.error(f"❌ Game {game_id} not found")
        session.close()
        return {"error": "Game not found"}
    
    try:
        with GameAnalyzer() as analyzer:
            result = analyzer.analyze_game(game, save_to_db=True)
            logger.info(f"✅ Completed analysis of game {game_id}")
            return result
    except Exception as e:
        logger.error(f"❌ Analysis failed for game {game_id}: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}
    finally:
        session.close()


if __name__ == "__main__":
    # For testing
    if len(sys.argv) > 1:
        game_id = int(sys.argv[1])
        result = analyze_game_task(game_id)
        print(f"Result: {result}")
