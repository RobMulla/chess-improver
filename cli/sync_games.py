"""Sync games from chess platforms."""
import argparse
import os
from dotenv import load_dotenv
from src.collectors.chess_com import ChessComCollector
from src.collectors.lichess import LichessCollector

load_dotenv()


def sync_chess_com(username: str, limit: Optional[int] = None):
    """Sync games from chess.com."""
    print(f"\n♟️  Syncing Chess.com games for {username}")
    print("=" * 60)
    with ChessComCollector(username) as collector:
        count = collector.sync_games(limit=limit)
    print(f"✅ Chess.com sync complete: {count} games\n")


def sync_lichess(username: str, limit: Optional[int] = None):
    """Sync games from Lichess."""
    print(f"\n♟️  Syncing Lichess games for {username}")
    print("=" * 60)
    with LichessCollector(username) as collector:
        count = collector.sync_games(limit=limit)
    print(f"✅ Lichess sync complete: {count} games\n")


def main():
    parser = argparse.ArgumentParser(description="Download chess games from platforms")
    parser.add_argument(
        "--platform",
        choices=["chess.com", "lichess", "both"],
        default="both",
        help="Platform to sync from",
    )
    parser.add_argument(
        "--username", help="Username (overrides .env)", default=None
    )
    parser.add_argument(
        "--limit", type=int, help="Limit number of games to download", default=None
    )
    
    args = parser.parse_args()
    
    # Get usernames from args or env
    chess_com_username = args.username or os.getenv("CHESS_COM_USERNAME")
    lichess_username = args.username or os.getenv("LICHESS_USERNAME")
    
    if args.platform in ["chess.com", "both"]:
        if chess_com_username:
            sync_chess_com(chess_com_username, args.limit)
        else:
            print("⚠️  No chess.com username provided (use --username or set CHESS_COM_USERNAME in .env)")
    
    if args.platform in ["lichess", "both"]:
        if lichess_username:
            sync_lichess(lichess_username, args.limit)
        else:
            print("⚠️  No Lichess username provided (use --username or set LICHESS_USERNAME in .env)")
    
    print("\n🎉 All done!")


if __name__ == "__main__":
    from typing import Optional
    main()
