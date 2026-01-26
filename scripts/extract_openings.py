"""Extract opening data from PGN files and update games."""
from src.database.models import get_session, Game
import chess.pgn
from io import StringIO


def extract_opening_from_pgn(pgn_text):
    """Extract opening name and ECO code from PGN."""
    try:
        pgn = StringIO(pgn_text)
        game = chess.pgn.read_game(pgn)
        if game:
            opening_name = game.headers.get("Opening")
            eco = game.headers.get("ECO")
            return opening_name, eco
    except Exception as e:
        pass
    return None, None


def extract_openings():
    """Extract and populate opening data for all games."""
    session = get_session()
    
    # Get games without opening data
    games = session.query(Game).filter(
        (Game.opening_name == None) | (Game.opening_name == '')
    ).all()
    
    print(f"📚 Extracting opening data from {len(games)} games...")
    
    updated = 0
    
    for game in games:
        if game.pgn:
            opening_name, eco = extract_opening_from_pgn(game.pgn)
            if opening_name:
                game.opening_name = opening_name
                game.opening_eco = eco
                updated += 1
                
                if updated % 1000 == 0:
                    print(f"  ✓ Processed {updated} games...")
                    session.commit()
    
    session.commit()
    session.close()
    
    print(f"✅ Updated {updated} games with opening data")
    return updated


if __name__ == "__main__":
    extract_openings()
