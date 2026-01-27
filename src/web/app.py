"""Flask web application for chess improvement system."""
from flask import Flask, render_template, request, jsonify, redirect, url_for
from datetime import datetime, date
from src.database.models import get_session, DailyPlan, Game, Opening, Insight, Position
from src.training.plan_generator import PlanGenerator
from sqlalchemy import func
import json

# Background job queue setup
try:
    from redis import Redis
    from rq import Queue
    redis_conn = Redis()
    analysis_queue = Queue('analysis', connection=redis_conn)
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
    plan = (
        session.query(DailyPlan)
        .filter(func.date(DailyPlan.date) == today)
        .first()
    )
    
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
    plan = (
        session.query(DailyPlan)
        .filter(func.date(DailyPlan.date) == plan_date)
        .first()
    )
    
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
    is_win = (game.result == "1-0" and game.player_color == "white") or (game.result == "0-1" and game.player_color == "black")
    is_draw = game.result == "1/2-1/2"
    
    if is_win:
        result_text = "Win"
    elif is_draw:
        result_text = "Draw"
    else:
        result_text = "Loss"
    
    session.close()
    
    return render_template(
        "game_viewer.html",
        game=game,
        pgn=game.pgn,
        is_win=is_win,
        is_draw=is_draw,
        result_text=result_text
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
            job_timeout='30m',
            result_ttl=3600  # Keep result for 1 hour
        )
        
        session.close()
        return jsonify({
            "success": True,
            "job_id": job.id,
            "status": "queued",
            "message": f"Game {game_id} queued for analysis"
        })
    except Exception as e:
        session.close()
        return jsonify({"error": str(e)}), 500


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


@app.route("/api/practice/positions", methods=["GET"])
def get_practice_positions():
    """Get mistake positions for practice with filters."""
    session = get_session()
    
    # Get filter parameters
    date_from = request.args.get("date_from")
    date_to = request.args.get("date_to")
    color = request.args.get("color", "both")
    mistake_type = request.args.get("mistake_type", "both")
    phase = request.args.get("phase", "all")
    limit = request.args.get("limit", 20, type=int)
    
    # Base query: only mistakes from player moves
    query = session.query(Position).join(Game).filter(
        (Position.is_mistake == True) | (Position.is_blunder == True)
    )
    
    # Apply filters
    if date_from:
        query = query.filter(Game.date >= date_from)
    if date_to:
        query = query.filter(Game.date <= date_to)
    if color != "both":
        query = query.filter(Game.player_color == color)
    if mistake_type == "blunder":
        query = query.filter(Position.is_blunder == True)
    elif mistake_type == "mistake":
        query = query.filter(Position.is_mistake == True, Position.is_blunder == False)
    if phase != "all":
        # Only filter if game_phase is set (not NULL)
        query = query.filter(Position.game_phase == phase)
    
    # Get positions, ordered randomly
    from sqlalchemy import func
    positions = query.order_by(func.random()).limit(limit).all()
    
    # Format response
    result = []
    for pos in positions:
        # Calculate game phase if not set
        game_phase = pos.game_phase
        if not game_phase:
            # Use FEN-based classification if available
            from src.analysis.move_classifier import MoveClassifier
            if pos.fen and pos.move_number:
                game_phase = MoveClassifier.classify_game_phase(pos.fen, pos.move_number)
            elif pos.move_number:
                # Fallback to simple move-based
                if pos.move_number <= 15:
                    game_phase = "opening"
                elif pos.move_number <= 40:
                    game_phase = "middlegame"
                else:
                    game_phase = "endgame"
        
        result.append({
            "id": pos.id,
            "fen": pos.fen,
            "best_move": pos.best_move,
            "player_move": pos.player_move,
            "move_number": pos.move_number,
            "game_phase": game_phase,
            "eval_drop": pos.eval_drop,
            "is_blunder": pos.is_blunder,
            "game_id": pos.game_id,
            "game": {
                "opening_name": pos.game.opening_name,
                "opponent_name": pos.game.opponent_name,
                "opponent_rating": pos.game.opponent_rating,
                "date": pos.game.date.isoformat() if pos.game.date else None
            }
        })
    
    session.close()
    return jsonify({"positions": result, "count": len(result)})


@app.route("/api/practice/check", methods=["POST"])
def check_practice_move():
    """Check if user's practice move is correct."""
    data = request.get_json()
    position_id = data.get("position_id")
    user_move = data.get("user_move")
    
    session = get_session()
    position = session.query(Position).get(position_id)
    
    if not position:
        session.close()
        return jsonify({"error": "Position not found"}), 404
    
    # Check if move matches best move
    correct = user_move == position.best_move
    
    response = {
        "correct": correct,
        "best_move": position.best_move,
        "user_move": user_move,
        "eval_drop": position.eval_drop if not correct else 0
    }
    
    session.close()
    return jsonify(response)


@app.route("/openings")
def openings_list():
    """List opening statistics."""
    from sqlalchemy import func, case
    
    session = get_session()
    
    # Get filter parameters
    color_filter = request.args.get('color')
    
    # Aggregate opening stats from games table
    query = session.query(
        Game.opening_name,
        Game.player_color,
        func.count(Game.id).label('total_games'),
        func.sum(
            case(
                (
                    (Game.result == '1-0') & (Game.player_color == 'white') |
                    (Game.result == '0-1') & (Game.player_color == 'black'),
                    1
                ),
                else_=0
            )
        ).label('wins'),
        func.sum(case((Game.result == '1/2-1/2', 1), else_=0)).label('draws'),
    ).filter(Game.opening_name != None).filter(Game.opening_name != '')
    
    # Apply color filter
    if color_filter:
        query = query.filter(Game.player_color == color_filter)
    
    query = query.group_by(Game.opening_name, Game.player_color).order_by(func.count(Game.id).desc())
    
    opening_stats = query.limit(100).all()
    
    # Format results
    openings = []
    for stat in opening_stats:
        total = stat.total_games
        wins = stat.wins or 0
        draws = stat.draws or 0
        losses = total - wins - draws
        win_rate = (wins / total * 100) if total > 0 else 0
        
        openings.append({
            'name': stat.opening_name,
            'color': stat.player_color,
            'games_played': total,
            'wins': wins,
            'draws': draws,
            'losses': losses,
            'win_rate': win_rate
        })
    
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
    query = (session.query(Position)
             .join(Game)
             .options(joinedload(Position.game))  # Eager load to prevent DetachedInstanceError
             .filter(Position.move_classification.isnot(None)))
    
    # Apply filters
    if classification:
        query = query.filter(Position.move_classification == classification)
    if phase:
        query = query.filter(Position.game_phase == phase)
    
    # Get total count
    total_positions = query.count()
    total_games = session.query(Game).filter(Game.analyzed == True).count()
    
    # Get paginated results
    positions = query.order_by(Position.id.desc()).offset((page - 1) * per_page).limit(per_page).all()
    
    # Don't close session yet - needed for template rendering
    # session.close()  # REMOVED - let Flask handle cleanup
    
    return render_template("moves.html", 
                         positions=positions,
                         total_positions=total_positions,
                         total_games=total_games,
                         page=page)


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
        name=data['name'],
        color=data['color'],
        starting_position=data.get('starting_position', 'start'),
        moves=data.get('moves', []),
        notes=data.get('notes', '')
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


if __name__ == "__main__":
    app.run(debug=True, port=5555)
