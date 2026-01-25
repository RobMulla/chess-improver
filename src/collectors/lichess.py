"""Lichess game collector."""
import requests
from typing import List, Dict, Optional
from datetime import datetime
import chess.pgn
from io import StringIO
from src.collectors.base import BaseCollector


class LichessCollector(BaseCollector):
    """Collector for Lichess games."""

    BASE_URL = "https://lichess.org/api"

    def __init__(self, username: str, api_token: Optional[str] = None):
        super().__init__(username)
        self.headers = {
            "Accept": "application/x-ndjson"  # Newline-delimited JSON
        }
        if api_token:
            self.headers["Authorization"] = f"Bearer {api_token}"

    def get_all_games(self) -> List[Dict]:
        """Download all games for the user from Lichess."""
        games_url = f"{self.BASE_URL}/games/user/{self.username}"
        
        params = {
            "max": 1000,  # Max per request
            "pgnInJson": "true",  # Include PGN in response
            "clocks": "false",
            "evals": "false",
            "opening": "true"
        }
        
        all_games = []
        
        try:
            print(f"📥 Downloading games from Lichess...")
            response = requests.get(
                games_url,
                headers=self.headers,
                params=params,
                timeout=30,
                stream=True
            )
            response.raise_for_status()
            
            # Parse NDJSON response (one JSON object per line)
            for line in response.iter_lines():
                if line:
                    import json
                    game = json.loads(line)
                    all_games.append(game)
            
            print(f"📦 Downloaded {len(all_games)} games")
            return all_games
            
        except requests.RequestException as e:
            print(f"❌ Error fetching games: {e}")
            return []

    def parse_game_data(self, raw_game: Dict) -> Optional[Dict]:
        """Parse Lichess game data into standard format."""
        try:
            # Get players
            white_player = raw_game.get("players", {}).get("white", {}).get("user", {}).get("name", "").lower()
            black_player = raw_game.get("players", {}).get("black", {}).get("user", {}).get("name", "").lower()
            
            # Determine player color
            player_color = "white" if white_player == self.username.lower() else "black"
            
            # Get ratings
            players = raw_game.get("players", {})
            if player_color == "white":
                player_rating = players.get("white", {}).get("rating")
                opponent_rating = players.get("black", {}).get("rating")
                opponent_name = players.get("black", {}).get("user", {}).get("name")
            else:
                player_rating = players.get("black", {}).get("rating")
                opponent_rating = players.get("white", {}).get("rating")
                opponent_name = players.get("white", {}).get("user", {}).get("name")
            
            # Get PGN
            pgn = raw_game.get("pgn", "")
            
            # Get opening info (Lichess provides this directly)
            opening = raw_game.get("opening", {})
            opening_name = opening.get("name")
            eco = opening.get("eco")
            
            # Parse date
            created_at = raw_game.get("createdAt")
            game_date = datetime.fromtimestamp(created_at / 1000) if created_at else datetime.now()
            
            # Get time control
            clock = raw_game.get("clock", {})
            if clock:
                initial = clock.get("initial", 0) // 60  # Convert to minutes
                increment = clock.get("increment", 0)
                time_control = f"{initial}+{increment}"
            else:
                time_control = raw_game.get("speed", "correspondence")
            
            # Get result
            status = raw_game.get("status")
            winner = raw_game.get("winner")
            
            if winner == "white":
                result = "1-0"
            elif winner == "black":
                result = "0-1"
            else:
                result = "1/2-1/2"
            
            return {
                "platform": "lichess",
                "game_id": raw_game.get("id", ""),
                "pgn": pgn,
                "date": game_date,
                "time_control": time_control,
                "result": result,
                "player_color": player_color,
                "player_rating": player_rating,
                "opponent_rating": opponent_rating,
                "opponent_name": opponent_name,
                "opening_name": opening_name,
                "opening_eco": eco,
            }
            
        except Exception as e:
            print(f"⚠️ Error parsing game: {e}")
            return None


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    username = os.getenv("LICHESS_USERNAME")
    
    if username:
        with LichessCollector(username) as collector:
            collector.sync_games(limit=10)  # Test with 10 games
    else:
        print("❌ LICHESS_USERNAME not set in .env")
