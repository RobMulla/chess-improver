"""Base collector class for chess platforms."""
import requests
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
import time
from datetime import datetime
import chess.pgn
from io import StringIO
from src.database.models import get_session, Game


class BaseCollector(ABC):
    """Base class for game collectors."""

    def __init__(self, username: str):
        self.username = username
        self.session = get_session()
        self.rate_limit_delay = 0.1  # seconds between requests

    @abstractmethod
    def get_all_games(self) -> List[Dict]:
        """Download all games for the user."""
        pass

    @abstractmethod
    def parse_game_data(self, raw_game: Dict) -> Dict:
        """Parse platform-specific game data into standard format."""
        pass

    def rate_limit(self):
        """Apply rate limiting."""
        time.sleep(self.rate_limit_delay)

    def extract_opening_from_pgn(self, pgn_text: str) -> tuple[Optional[str], Optional[str]]:
        """Extract opening name and ECO code from PGN."""
        try:
            pgn = StringIO(pgn_text)
            game = chess.pgn.read_game(pgn)
            if game:
                opening_name = game.headers.get("Opening")
                eco = game.headers.get("ECO")
                
                # Chess.com uses ECOUrl instead of Opening header
                if not opening_name and eco:
                    opening_name = self._eco_to_opening_name(eco)
                elif not opening_name:
                    eco_url = game.headers.get("ECOUrl", "")
                    if eco_url:
                        # Extract opening name from URL like "https://www.chess.com/openings/Kings-Pawn-Opening..."
                        parts = eco_url.split("/openings/")
                        if len(parts) > 1:
                            opening_slug = parts[1].split("?")[0]
                            opening_name = opening_slug.replace("-", " ").title()
                
                return opening_name, eco
        except Exception as e:
            print(f"⚠️  Error parsing PGN: {e}")
        return None, None
    
    def _eco_to_opening_name(self, eco: str) -> str:
        """Map ECO code to opening name."""
        # Basic ECO to opening name mapping (first letter classification)
        eco_map = {
            'A': 'Flank Openings',
            'B': 'Semi-Open Games',
            'C': 'Open Games', 
            'D': "Queen's Pawn Game",
            'E': 'Indian Defenses'
        }
        
        # More specific mappings
        specific_eco = {
            'C44': "King's Pawn Game",
            'C50': 'Italian Game',
            'C42': 'Petrov Defense',
            'C45': 'Scotch Game',
            'B20': 'Sicilian Defense',
            'B00': 'Uncommon King Pawn Opening',
            'D00': "Queen's Pawn Game",
            'E00': 'Indian Defense',
        }
        
        # Try specific first, then fall back to general
        return specific_eco.get(eco, eco_map.get(eco[0] if eco else '', 'Unknown Opening'))

    def parse_result(self, result_str: str, player_color: str) -> str:
        """Parse game result."""
        if result_str == "1-0":
            return "win" if player_color == "white" else "loss"
        elif result_str == "0-1":
            return "loss" if player_color == "white" else "win"
        elif result_str == "1/2-1/2":
            return "draw"
        return "unknown"

    def save_game(self, game_data: Dict) -> Optional[Game]:
        """Save game to database."""
        try:
            # Check if game already exists
            existing = (
                self.session.query(Game)
                .filter_by(game_id=game_data["game_id"])
                .first()
            )
            if existing:
                return existing

            # Create new game
            game = Game(**game_data)
            self.session.add(game)
            self.session.commit()
            return game
        except Exception as e:
            self.session.rollback()
            print(f"❌ Error saving game: {e}")
            return None

    def sync_games(self, limit: Optional[int] = None) -> int:
        """Sync games from platform to database."""
        print(f"🔄 Syncing games for {self.username} from {self.__class__.__name__}...")
        
        try:
            raw_games = self.get_all_games()
            
            if limit:
                raw_games = raw_games[:limit]
            
            saved_count = 0
            for raw_game in raw_games:
                game_data = self.parse_game_data(raw_game)
                if game_data and self.save_game(game_data):
                    saved_count += 1
                self.rate_limit()
            
            print(f"✅ Synced {saved_count} games")
            return saved_count
            
        except Exception as e:
            print(f"❌ Error syncing games: {e}")
            return 0

    def close(self):
        """Close database session."""
        self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
