"""Worker for importing games from chess platforms."""
import io
from datetime import datetime

import chess.pgn
import requests

from src.database.models import Game, get_session


def parse_pgn_date(pgn_headers):
    """Extract date from PGN headers."""
    date_str = pgn_headers.get("Date", "")
    time_str = pgn_headers.get("UTCTime", "00:00:00")
    try:
        # PGN format is usually YYYY.MM.DD
        date_str = date_str.replace("?", "01")  # Handle ???? or 2024.??.??
        dt_str = f"{date_str} {time_str}"
        return datetime.strptime(dt_str, "%Y.%m.%d %H:%M:%S")
    except ValueError:
        return datetime.utcnow()


from rq import get_current_job


def sync_games_task(platform, username):
    """Background task to sync games."""
    job = get_current_job()
    if job:
        job.meta["status"] = "running"
        job.meta["progress"] = 0
        job.save_meta()

    print(f"🔄 Syncing games for {username} on {platform}...")

    session = get_session()
    new_games_count = 0

    try:
        if platform == "chess.com":
            new_games_count = sync_chess_com(session, username, job)
        elif platform == "lichess":
            new_games_count = sync_lichess(session, username, job)
        else:
            print(f"❌ Unknown platform: {platform}")
            if job:
                job.meta["status"] = "failed"
                job.meta["error"] = f"Unknown platform: {platform}"
                job.save_meta()
            return

        print(f"✅ Sync complete. Imported {new_games_count} new games.")
        if job:
            job.meta["status"] = "completed"
            job.meta["progress"] = 100
            job.meta["imported_count"] = new_games_count
            job.save_meta()

    except Exception as e:
        print(f"❌ Sync failed: {e}")
        if job:
            job.meta["status"] = "failed"
            job.meta["error"] = str(e)
            job.save_meta()
        raise e
    finally:
        session.close()


def sync_chess_com(session, username, job=None):
    """Sync games from Chess.com."""
    # Get archives (monthly endpoints)
    headers = {"User-Agent": "ChessImprover/1.0 (contact: your@email.com)"}
    archives_url = f"https://api.chess.com/pub/player/{username}/games/archives"

    try:
        resp = requests.get(archives_url, headers=headers, timeout=10)
        resp.raise_for_status()
        archives = resp.json().get("archives", [])
    except Exception as e:
        print(f"Failed to fetch archives: {e}")
        return 0

    # Process only most recent month for speed in this iteration
    archives = archives[-3:]

    total_archives = len(archives)
    count = 0

    for i, url in enumerate(archives):
        try:
            # Update progress
            if job:
                job.meta["progress"] = int((i / total_archives) * 100)
                job.save_meta()

            print(f"Fetching {url}...")
            resp = requests.get(url, headers=headers, timeout=20)
            if resp.status_code != 200:
                continue

            games = resp.json().get("games", [])
            for game_data in games:
                pgn_text = game_data.get("pgn")
                if not pgn_text:
                    continue

                game_url = game_data.get("url")
                game_id = f"chesscom_{game_url.split('/')[-1]}"

                # Check exist
                if session.query(Game).filter_by(game_id=game_id).first():
                    continue

                pgn_io = io.StringIO(pgn_text)
                chess_game = chess.pgn.read_game(pgn_io)

                if not chess_game:
                    continue

                headers_pgn = chess_game.headers

                game_record = Game(
                    platform="chess.com",
                    game_id=game_id,
                    pgn=pgn_text,
                    date=parse_pgn_date(headers_pgn),
                    result=headers_pgn.get("Result", "*"),
                    player_color="white"
                    if headers_pgn.get("White", "").lower() == username.lower()
                    else "black",
                    player_rating=int(
                        headers_pgn.get(
                            "WhiteElo"
                            if headers_pgn.get("White", "").lower() == username.lower()
                            else "BlackElo",
                            0,
                        )
                    ),
                    opponent_rating=int(
                        headers_pgn.get(
                            "BlackElo"
                            if headers_pgn.get("White", "").lower() == username.lower()
                            else "WhiteElo",
                            0,
                        )
                    ),
                    opponent_name=headers_pgn.get(
                        "Black"
                        if headers_pgn.get("White", "").lower() == username.lower()
                        else "White",
                        "Unknown",
                    ),
                    opening_name=headers_pgn.get("ECOUrl", "")
                    .split("/")[-1]
                    .replace("-", " ")
                    .title()
                    if "ECOUrl" in headers_pgn
                    else "?",
                    opening_eco=headers_pgn.get("ECO", ""),
                    time_control=headers_pgn.get("TimeControl", ""),
                )

                session.add(game_record)
                count += 1

            session.commit()

        except Exception as e:
            print(f"Error processing archive {url}: {e}")
            session.rollback()

    return count


def sync_lichess(session, username, job=None):
    """Sync games from Lichess."""
    # Lichess export API
    # Max to avoid timeout for now: 100
    url = f"https://lichess.org/api/games/user/{username}"
    params = {"max": 100, "pgnInJson": "true", "opening": "true", "clocks": "false"}
    headers = {"Accept": "application/x-ndjson"}

    if job:
        job.meta["progress"] = 10  # Started
        job.save_meta()

    try:
        resp = requests.get(url, params=params, headers=headers, stream=True, timeout=30)
        resp.raise_for_status()
    except Exception as e:
        print(f"Failed to fetch Lichess games: {e}")
        return 0

    if job:
        job.meta["progress"] = 20  # Downloaded
        job.save_meta()

    count = 0

    # Re-request as plain PGN for simplicity
    try:
        resp = requests.get(url, params={"max": 50}, timeout=30)
        pgn_data = resp.text
    except:
        return 0

    pgn_io = io.StringIO(pgn_data)
    games_processed = 0

    while True:
        chess_game = chess.pgn.read_game(pgn_io)
        if chess_game is None:
            break

        games_processed += 1
        if job and games_processed % 5 == 0:
            job.meta["progress"] = 20 + int((games_processed / 50) * 80)  # rough estimate
            job.save_meta()

        headers_pgn = chess_game.headers
        site_url = headers_pgn.get("Site", "")
        if not site_url:
            continue

        game_id = f"lichess_{site_url.split('/')[-1]}"

        if session.query(Game).filter_by(game_id=game_id).first():
            continue

        exporter = chess.pgn.StringExporter(headers=True, variations=True, comments=True)
        pgn_str = chess_game.accept(exporter)

        game_record = Game(
            platform="lichess",
            game_id=game_id,
            pgn=pgn_str,
            date=parse_pgn_date(headers_pgn),
            result=headers_pgn.get("Result", "*"),
            player_color="white"
            if headers_pgn.get("White", "").lower() == username.lower()
            else "black",
            player_rating=int(
                headers_pgn.get(
                    "WhiteElo"
                    if headers_pgn.get("White", "").lower() == username.lower()
                    else "BlackElo",
                    0,
                )
                or 0
            ),
            opponent_rating=int(
                headers_pgn.get(
                    "BlackElo"
                    if headers_pgn.get("White", "").lower() == username.lower()
                    else "WhiteElo",
                    0,
                )
                or 0
            ),
            opponent_name=headers_pgn.get(
                "Black" if headers_pgn.get("White", "").lower() == username.lower() else "White",
                "Unknown",
            ),
            opening_name=headers_pgn.get("Opening", "?"),
            opening_eco=headers_pgn.get("ECO", ""),
            time_control=headers_pgn.get("TimeControl", ""),
        )

        session.add(game_record)
        count += 1

    session.commit()
    return count
