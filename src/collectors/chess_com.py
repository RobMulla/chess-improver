"""Chess.com game collector."""
import requests
from typing import List, Dict, Optional
from datetime import datetime
from src.collectors.base import BaseCollector


class ChessComCollector(BaseCollector):
    """Collector for chess.com games."""

    BASE_URL = "https://api.chess.com/pub"

    def __init__(self, username: str):
        super().__init__(username)
        self.headers = {
            "User-Agent": "ChessImprover/1.0 (Personal chess improvement tool)"
        }

    def get_all_games(self) -> List[Dict]:
        """Download all games for the user from chess.com."""
        all_games = []
        
        # Get list of monthly archives
        archives_url = f"{self.BASE_URL}/player/{self.username}/games/archives"
        
        try:
            response = requests.get(archives_url, headers=self.headers, timeout=10)
            response.raise_for_status()
            archives = response.json().get("archives", [])
            
            # Reverse to download newest games first
            archives = list(reversed(archives))
            
            print(f"📦 Found {len(archives)} monthly archives")
            
            # Download games from each archive
            for archive_url in archives:
                self.rate_limit()
                games = self._get_archive_games(archive_url)
                all_games.extend(games)
                print(f"  📥 Downloaded {len(games)} games from {archive_url.split('/')[-2:]}")
            
            return all_games
            
        except requests.RequestException as e:
            print(f"❌ Error fetching archives: {e}")
            return []

    def _get_archive_games(self, archive_url: str) -> List[Dict]:
        """Download games from a specific monthly archive."""
        try:
            response = requests.get(archive_url, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.json().get("games", [])
        except requests.RequestException as e:
            print(f"❌ Error fetching archive {archive_url}: {e}")
            return []

    def parse_game_data(self, raw_game: Dict) -> Optional[Dict]:
        """Parse chess.com game data into standard format."""
        try:
            # Determine player color
            white_player = raw_game.get("white", {}).get("username", "").lower()
            player_color = "white" if white_player == self.username.lower() else "black"
            
            # Get ratings
            if player_color == "white":
                player_rating = raw_game.get("white", {}).get("rating")
                opponent_rating = raw_game.get("black", {}).get("rating")
                opponent_name = raw_game.get("black", {}).get("username")
            else:
                player_rating = raw_game.get("black", {}).get("rating")
                opponent_rating = raw_game.get("white", {}).get("rating")
                opponent_name = raw_game.get("white", {}).get("username")
            
            # Get PGN
            pgn = raw_game.get("pgn", "")
            
            # Extract opening info
            opening_name, eco = self.extract_opening_from_pgn(pgn)
            
            # Parse date (Unix timestamp)
            end_time = raw_game.get("end_time")
            game_date = datetime.fromtimestamp(end_time) if end_time else datetime.now()
            
            # Get time control
            time_control = raw_game.get("time_control", "")
            
            # Get result
            white_result = raw_game.get("white", {}).get("result", "")
            black_result = raw_game.get("black", {}).get("result", "")
            
            # Determine game result (1-0, 0-1, 1/2-1/2)
            if "win" in white_result.lower():
                result = "1-0"
            elif "win" in black_result.lower():
                result = "0-1"
            else:
                result = "1/2-1/2"
            
            return {
                "platform": "chess.com",
                "game_id": raw_game.get("url", "").split("/")[-1],
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
    username = os.getenv("CHESS_COM_USERNAME")
    
    if username:
        with ChessComCollector(username) as collector:
            collector.sync_games(limit=10)  # Test with 10 games
    else:
        print("❌ CHESS_COM_USERNAME not set in .env")
