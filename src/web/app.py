"""Flask web application for chess improvement system."""
from datetime import datetime

from flask import Flask, Response, jsonify, redirect, render_template, request, url_for
from sqlalchemy import func

from src.database.models import DailyPlan, Game, Insight, Opening, Position, get_session
from src.training.plan_generator import PlanGenerator

# Background job queue setup
try:
    from redis import Redis
    from rq import Queue

    redis_conn = Redis()
    analysis_queue = Queue("analysis", connection=redis_conn)
    queue_enabled = True
    print("✅ Background job queue enabled")
except Exception as e:
    print(f"⚠️ Job queue disabled: {e}")
    queue_enabled = False
    analysis_queue = None

app = Flask(__name__)


@app.route("/")
def index():
    """Dashboard homepage."""
    session = get_session()

    # Get today's plan
    today = datetime.utcnow().date()
    plan = session.query(DailyPlan).filter(func.date(DailyPlan.date) == today).first()

    # Get recent insights
    recent_accuracy = (
        session.query(Insight)
        .filter_by(metric_name="avg_accuracy", time_period="last_30_days")
        .order_by(Insight.generated_at.desc())
        .first()
    )

    # Game stats
    total_games = session.query(Game).count()
    analyzed_games = session.query(Game).filter_by(analyzed=True).count()

    # Top openings
    top_openings = (
        session.query(Opening)
        .filter(Opening.games_played >= 3)
        .order_by(Opening.games_played.desc())
        .limit(5)
        .all()
    )

    session.close()

    return render_template(
        "dashboard.html",
        plan=plan,
        recent_accuracy=recent_accuracy,
        total_games=total_games,
        analyzed_games=analyzed_games,
        top_openings=top_openings,
    )


@app.route("/settings", methods=["GET", "POST"])
def settings():
    """Settings and Import page."""
    from src.database.models import UserConfig

    session = get_session()

    success = False

    if request.method == "POST":
        # Save settings
        usernames = {
            "chess_com_username": request.form.get("chess_com_username"),
            "lichess_username": request.form.get("lichess_username"),
        }

        for key, value in usernames.items():
            if value is not None:  # Empty string is fine, None means missing from form
                config = session.query(UserConfig).get(key)
                if not config:
                    config = UserConfig(key=key)
                    session.add(config)
                config.value = value.strip()
                config.updated_at = datetime.utcnow()

        session.commit()
        success = True

    # Load settings
    configs = session.query(UserConfig).all()
    config_dict = {c.key: c.value for c in configs}

    session.close()

    return render_template("settings.html", config=config_dict, success=success)


@app.route("/api/sync-games", methods=["POST"])
def api_sync_games():
    """Start game sync background job."""
    if not queue_enabled:
        return jsonify({"success": False, "error": "Background queue not available"}), 503

    from src.database.models import UserConfig
    from src.workers.import_worker import sync_games_task

    data = request.json or {}
    username = data.get("username")
    platform = data.get("platform")

    jobs = []
    errors = []

    session = get_session()

    # helper to queue job
    def queue_sync(plat, user):
        try:
            job = analysis_queue.enqueue(sync_games_task, plat, user, job_timeout="10m")
            jobs.append({"platform": plat, "job_id": job.id})
        except Exception as e:
            errors.append(f"Failed to queue {plat}: {str(e)}")

    if username and platform:
        # Explicit request
        queue_sync(platform, username)
    else:
        # Auto-detect from settings
        chess_user = session.query(UserConfig).get("chess_com_username")
        lichess_user = session.query(UserConfig).get("lichess_username")

        found_config = False

        if chess_user and chess_user.value:
            queue_sync("chess.com", chess_user.value)
            found_config = True

        if lichess_user and lichess_user.value:
            queue_sync("lichess", lichess_user.value)
            found_config = True

        if not found_config:
            session.close()
            return jsonify({"success": False, "error": "No accounts configured in Settings"}), 400

    session.close()

    if errors:
        return jsonify({"success": False, "jobs": jobs, "errors": errors}), 500

    return jsonify(
        {
            "success": True,
            "jobs": jobs,
            "status": "queued",
            "message": f"Queued {len(jobs)} sync jobs",
        }
    )


@app.route("/plan")
@app.route("/plan/<date_str>")
def daily_plan(date_str=None):
    """View daily training plan."""
    session = get_session()

    # Parse date
    if date_str:
        plan_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    else:
        plan_date = datetime.utcnow().date()

    # Get plan
    plan = session.query(DailyPlan).filter(func.date(DailyPlan.date) == plan_date).first()

    session.close()

    return render_template("daily_plan.html", plan=plan, plan_date=plan_date)


@app.route("/plan/generate", methods=["POST"])
def generate_plan():
    """Generate new daily plan."""
    generator = PlanGenerator()
    plan = generator.generate_plan()
    generator.close()

    return redirect(url_for("daily_plan"))


@app.route("/plan/task/<int:plan_id>/<int:task_id>/complete", methods=["POST"])
def complete_task(plan_id, task_id):
    """Mark a task as complete."""
    session = get_session()

    plan = session.query(DailyPlan).get(plan_id)
    if plan:
        tasks = plan.tasks
        for task in tasks:
            if task["id"] == task_id:
                task["completed"] = not task["completed"]  # Toggle
                break

        plan.tasks = tasks
        session.commit()

    session.close()

    return jsonify({"success": True})


@app.route("/games")
def games_list():
    """List all games."""
    session = get_session()

    page = request.args.get("page", 1, type=int)
    per_page = 20

    games_query = session.query(Game).order_by(Game.date.desc())
    total_games = games_query.count()
    games = games_query.limit(per_page).offset((page - 1) * per_page).all()

    session.close()

    return render_template(
        "games_list.html",
        games=games,
        page=page,
        total_games=total_games,
        per_page=per_page,
    )


@app.route("/games/<int:game_id>")
def view_game(game_id):
    """View a specific game."""
    session = get_session()

    game = session.query(Game).get(game_id)

    if not game:
        session.close()
        return "Game not found", 404

    # Determine result text
    is_win = (game.result == "1-0" and game.player_color == "white") or (
        game.result == "0-1" and game.player_color == "black"
    )
    is_draw = game.result == "1/2-1/2"

    # Determine result text
    if is_win:
        result_text = "Win"
    elif is_draw:
        result_text = "Draw"
    else:
        result_text = "Loss"

    # Fetch analysis positions
    positions_db = (
        session.query(Position).filter_by(game_id=game_id).order_by(Position.move_number).all()
    )
    positions = []
    for pos in positions_db:
        positions.append(
            {
                "move_number": pos.move_number,
                "evaluation": pos.evaluation,
                "classification": pos.move_classification,
                "is_mistake": pos.is_mistake,
                "is_blunder": pos.is_blunder,
                "eval_drop": pos.eval_drop,
            }
        )

    session.close()

    return render_template(
        "game_viewer.html",
        game=game,
        pgn=game.pgn,
        positions=positions,
        is_win=is_win,
        is_draw=is_draw,
        result_text=result_text,
    )


@app.route("/games/<int:game_id>/star", methods=["POST"])
def toggle_star(game_id):
    """Toggle starred status of a game."""
    session = get_session()

    game = session.query(Game).get(game_id)

    if not game:
        session.close()
        return jsonify({"error": "Game not found"}), 404

    game.starred = not game.starred
    session.commit()

    starred = game.starred
    session.close()

    return jsonify({"success": True, "starred": starred})


@app.route("/games/<int:game_id>/analyze", methods=["POST"])
def analyze_game_route(game_id):
    """Analyze a specific game."""
    from src.analysis.game_analyzer import GameAnalyzer

    session = get_session()
    game = session.query(Game).get(game_id)

    if not game:
        session.close()
        return jsonify({"success": False, "error": "Game not found"}), 404

    session.close()

    try:
        with GameAnalyzer() as analyzer:
            result = analyzer.analyze_game(game, save_to_db=True)

        return jsonify({"success": True, "result": result})
    except Exception as e:
        import traceback

        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/games/<int:game_id>/analyze", methods=["POST"])
def queue_game_analysis(game_id):
    """Queue a game for background analysis (non-blocking)."""
    if not queue_enabled:
        return jsonify({"error": "Background jobs not available"}), 503

    session = get_session()
    game = session.query(Game).get(game_id)

    if not game:
        session.close()
        return jsonify({"error": "Game not found"}), 404

    try:
        from src.workers.analyzer_worker import analyze_game_task

        job = analysis_queue.enqueue(
            analyze_game_task,
            game_id,
            job_timeout="30m",
            result_ttl=3600,  # Keep result for 1 hour
        )

        session.close()
        return jsonify(
            {
                "success": True,
                "job_id": job.id,
                "status": "queued",
                "message": f"Game {game_id} queued for analysis",
            }
        )
    except Exception as e:
        session.close()
        return jsonify({"error": str(e)}), 500


@app.route("/api/analyze-games", methods=["POST"])
def bulk_analyze_games():
    """Queue multiple games for analysis."""
    if not queue_enabled:
        return jsonify({"error": "Background jobs not available"}), 503

    data = request.json
    game_ids = data.get("game_ids", [])

    if not game_ids:
        return jsonify({"success": False, "error": "No game IDs provided"}), 400

    queued_count = 0
    errors = []

    from src.workers.analyzer_worker import analyze_game_task

    for game_id in game_ids:
        try:
            analysis_queue.enqueue(analyze_game_task, game_id, job_timeout="30m", result_ttl=3600)
            queued_count += 1
        except Exception as e:
            errors.append(f"Game {game_id}: {str(e)}")

    return jsonify({"success": True, "queued": queued_count, "errors": errors})


@app.route("/api/jobs/<job_id>", methods=["GET"])
def get_job_status(job_id):
    """Check status of a background job."""
    if not queue_enabled:
        return jsonify({"error": "Background jobs not available"}), 503

    try:
        from rq.job import Job

        job = Job.fetch(job_id, connection=redis_conn)

        response = {
            "job_id": job.id,
            "status": job.get_status(),
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "meta": job.meta,
        }

        if job.is_finished:
            response["result"] = job.result
        elif job.is_failed:
            response["error"] = str(job.exc_info)

        return jsonify(response)
    except Exception as e:
        return jsonify({"error": str(e)}), 404


@app.route("/api/cache/stats", methods=["GET"])
def cache_stats():
    """Get cache statistics."""
    from src.analysis.cache import get_cache

    cache = get_cache()
    return jsonify(cache.get_stats())


@app.route("/api/cache/clear", methods=["POST"])
def clear_cache():
    """Clear all cached evaluations."""
    from src.analysis.cache import get_cache

    cache = get_cache()
    deleted = cache.clear_all()
    return jsonify({"deleted": deleted, "message": f"Cleared {deleted} cached evaluations"})


@app.route("/openings")
def openings_list():
    """List opening statistics."""
    from sqlalchemy import case, func

    session = get_session()

    # Get filter parameters
    color_filter = request.args.get("color")

    # Aggregate opening stats from games table
    query = (
        session.query(
            Game.opening_name,
            Game.player_color,
            func.count(Game.id).label("total_games"),
            func.sum(
                case(
                    (
                        (Game.result == "1-0") & (Game.player_color == "white")
                        | (Game.result == "0-1") & (Game.player_color == "black"),
                        1,
                    ),
                    else_=0,
                )
            ).label("wins"),
            func.sum(case((Game.result == "1/2-1/2", 1), else_=0)).label("draws"),
        )
        .filter(Game.opening_name != None)
        .filter(Game.opening_name != "")
    )

    # Apply color filter
    if color_filter:
        query = query.filter(Game.player_color == color_filter)

    query = query.group_by(Game.opening_name, Game.player_color).order_by(
        func.count(Game.id).desc()
    )

    opening_stats = query.limit(100).all()

    # Format results
    openings = []
    for stat in opening_stats:
        total = stat.total_games
        wins = stat.wins or 0
        draws = stat.draws or 0
        losses = total - wins - draws
        win_rate = (wins / total * 100) if total > 0 else 0

        openings.append(
            {
                "name": stat.opening_name,
                "color": stat.player_color,
                "games_played": total,
                "wins": wins,
                "draws": draws,
                "losses": losses,
                "win_rate": win_rate,
            }
        )

    session.close()

    return render_template("openings.html", openings=openings, color_filter=color_filter)


@app.route("/insights")
def insights():
    """View insights and analytics."""
    session = get_session()

    accuracy_insights = (
        session.query(Insight)
        .filter_by(category="accuracy")
        .order_by(Insight.generated_at.desc())
        .all()
    )

    session.close()

    return render_template("insights.html", accuracy_insights=accuracy_insights)


@app.route("/practice")
def practice_mistakes():
    """Interactive practice for past mistakes."""
    return render_template("practice.html")


@app.route("/api/practice/positions")
def api_practice_positions():
    """Get positions for practice and create session."""

    from sqlalchemy.orm import joinedload

    from src.database.models import Game, Position, PracticeSession

    color = request.args.get("color", "both")
    mistake_type = request.args.get("mistake_type", "both")
    phase = request.args.get("phase", "all")
    limit = int(request.args.get("limit", 20))

    session = get_session()

    # Create Session Record
    new_session = PracticeSession(
        settings={"color": color, "mistake_type": mistake_type, "phase": phase},
        total_positions=0,  # Will update later or after fetch
    )
    session.add(new_session)

    # Base query: Positions that are mistakes OR blunders
    query = session.query(Position).join(Game).options(joinedload(Position.game))

    # Mistake Type Filter
    if mistake_type == "blunder":
        query = query.filter(Position.is_blunder == True)
    elif mistake_type == "mistake":
        query = query.filter(Position.is_mistake == True)
    else:
        # Both (Mistake OR Blunder)
        from sqlalchemy import or_

        query = query.filter(or_(Position.is_mistake == True, Position.is_blunder == True))

    # Phase Filter
    if phase != "all":
        query = query.filter(Position.game_phase == phase)

    # Color Filter
    if color != "both":
        query = query.filter(Game.player_color == color)

    # Fetch content
    from sqlalchemy.sql.expression import func

    positions = query.order_by(func.random()).limit(limit).all()

    # Update session total
    new_session.total_positions = len(positions)
    session.commit()
    session_id = new_session.id

    result = []
    for p in positions:
        result.append(
            {
                "id": p.id,
                "fen": p.fen,
                "move_number": p.move_number,
                "game_phase": p.game_phase,
                "best_move": p.best_move,
                "game": {
                    "opening_name": p.game.opening_name,
                    "opponent_name": p.game.opponent_name,
                    "opponent_rating": p.game.opponent_rating,
                    "player_color": p.game.player_color,
                },
            }
        )

    session.close()

    return jsonify({"session_id": session_id, "positions": result})


@app.route("/api/practice/check", methods=["POST"])
def api_practice_check():
    """Check user move against engine best move and save attempt."""
    from src.database.models import Position, PracticeAttempt, PracticeSession

    data = request.json
    session_id = data.get("session_id")
    position_id = data.get("position_id")
    user_move = data.get("user_move")  # UCI format e.g. e2e4
    time_taken = data.get("time_taken", 0)
    gave_up = data.get("gave_up", False)

    session = get_session()
    position = session.query(Position).get(position_id)

    if not position:
        session.close()
        return jsonify({"success": False, "error": "Position not found"}), 404

    # Compare moves
    if gave_up:
        is_correct = False
    else:
        is_correct = user_move == position.best_move

    # Save Attempt
    if session_id:
        practice_session = session.query(PracticeSession).get(session_id)
        if practice_session:
            attempt = PracticeAttempt(
                session_id=session_id,
                position_id=position_id,
                user_move=user_move,
                is_correct=is_correct,
                time_taken=time_taken,
            )
            session.add(attempt)

            # Update Score
            if is_correct:
                practice_session.score += 1

            session.commit()

    response = {"correct": is_correct, "best_move": position.best_move, "user_move": user_move}

    session.close()
    return jsonify(response)


@app.route("/moves")
def moves_browser():
    """Browse all analyzed positions/moves."""
    from sqlalchemy.orm import joinedload

    session = get_session()

    # Get filters
    classification = request.args.get("classification")
    phase = request.args.get("phase")
    page = request.args.get("page", 1, type=int)
    per_page = 50

    # Base query with eager loading of game relationship
    query = (
        session.query(Position)
        .join(Game)
        .options(joinedload(Position.game))  # Eager load to prevent DetachedInstanceError
        .filter(Position.move_classification.isnot(None))
    )

    # Apply filters
    if classification:
        query = query.filter(Position.move_classification == classification)
    if phase:
        query = query.filter(Position.game_phase == phase)

    # Get total count
    total_positions = query.count()
    total_games = session.query(Game).filter(Game.analyzed == True).count()

    # Get paginated results
    positions = (
        query.order_by(Position.id.desc()).offset((page - 1) * per_page).limit(per_page).all()
    )

    # Don't close session yet - needed for template rendering
    # session.close()  # REMOVED - let Flask handle cleanup

    return render_template(
        "moves.html",
        positions=positions,
        total_positions=total_positions,
        total_games=total_games,
        page=page,
    )


@app.route("/repertoire")
def repertoire():
    """Opening repertoire builder."""
    from src.database.models import OpeningRepertoire

    session = get_session()
    repertoires = session.query(OpeningRepertoire).filter_by(is_active=True).all()
    session.close()

    return render_template("repertoire.html", repertoires=repertoires)


@app.route("/repertoire/add", methods=["POST"])
def add_repertoire():
    """Add new opening line to repertoire."""
    from src.database.models import OpeningRepertoire

    data = request.json
    session = get_session()

    repertoire = OpeningRepertoire(
        name=data["name"],
        color=data["color"],
        starting_position=data.get("starting_position", "start"),
        moves=data.get("moves", []),
        notes=data.get("notes", ""),
    )

    session.add(repertoire)
    session.commit()
    session.close()

    return jsonify({"success": True})


@app.route("/repertoire/practice/<int:id>")
def practice_repertoire(id):
    """Practice specific repertoire line."""
    from src.database.models import OpeningRepertoire

    session = get_session()
    repertoire = session.query(OpeningRepertoire).get(id)
    session.close()

    if not repertoire:
        return "Repertoire not found", 404

    return render_template("practice_repertoire.html", repertoire=repertoire)


@app.route("/games/<int:game_id>/export")
def export_game_pgn(game_id):
    """Export game PGN."""
    session = get_session()
    game = session.query(Game).get(game_id)
    session.close()

    if not game:
        return "Game not found", 404

    return Response(
        game.pgn,
        mimetype="application/x-chess-pgn",
        headers={
            "Content-Disposition": f"attachment;filename=game_{game.platform}_{game.game_id}.pgn"
        },
    )


if __name__ == "__main__":
    app.run(debug=True, port=5555)
