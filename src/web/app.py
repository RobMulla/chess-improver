"""Flask web application for chess improvement system."""
from flask import Flask, render_template, request, jsonify, redirect, url_for
from datetime import datetime, date
from src.database.models import get_session, DailyPlan, Game, Opening, Insight
from src.training.plan_generator import PlanGenerator
from sqlalchemy import func
import json

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


@app.route("/openings")
def openings_list():
    """List opening statistics."""
    session = get_session()
    
    openings = (
        session.query(Opening)
        .filter(Opening.games_played >= 2)
        .order_by(Opening.games_played.desc())
        .all()
    )
    
    session.close()
    
    return render_template("openings.html", openings=openings)


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


if __name__ == "__main__":
    app.run(debug=True, port=5000)
