"""Daily training plan generator."""
import json
from datetime import datetime, date
from typing import List, Dict, Optional
from src.database.models import get_session, DailyPlan, Game, Position
from src.analysis.opening_analyzer import OpeningAnalyzer


class PlanGenerator:
    """Generate personalized daily training plans."""

    def __init__(self):
        self.session = get_session()

    def generate_plan(self, plan_date: Optional[date] = None) -> DailyPlan:
        """Generate training plan for a specific date."""
        if not plan_date:
            plan_date = datetime.utcnow().date()
        
        print(f"📅 Generating training plan for {plan_date}...")
        
        # Check if plan already exists
        existing = (
            self.session.query(DailyPlan)
            .filter(func.date(DailyPlan.date) == plan_date)
            .first()
        )
        
        if existing:
            print(f"✅ Plan already exists for {plan_date}")
            return existing
        
        tasks = []
        task_id = 1
        
        # 1. Opening study task
        opening_task = self._create_opening_task(task_id)
        if opening_task:
            tasks.append(opening_task)
            task_id += 1
        
        # 2. Tactics training
        tactics_task = self._create_tactics_task(task_id)
        tasks.append(tactics_task)
        task_id += 1
        
        # 3. Game review
        game_review_task = self._create_game_review_task(task_id)
        if game_review_task:
            tasks.append(game_review_task)
            task_id += 1
        
        # 4. Study mistake pattern
        mistake_task = self._create_mistake_pattern_task(task_id)
        if mistake_task:
            tasks.append(mistake_task)
            task_id += 1
        
        # 5. Endgame practice
        endgame_task = {
            "id": task_id,
            "type": "endgame",
            "title": "Practice key endgame positions",
            "duration": "10 min",
            "resources": ["https://lichess.org/practice"],
            "completed": False,
        }
        tasks.append(endgame_task)
        
        # Create plan
        plan = DailyPlan(
            date=datetime.combine(plan_date, datetime.min.time()),
            tasks=tasks,
        )
        
        self.session.add(plan)
        self.session.commit()
        
        print(f"✅ Created plan with {len(tasks)} tasks")
        self._print_plan(plan)
        
        return plan

    def _create_opening_task(self, task_id: int) -> Optional[Dict]:
        """Create opening study task based on weakest opening."""
        analyzer = OpeningAnalyzer()
        weak_openings = analyzer.get_weak_openings(min_games=3)
        analyzer.close()
        
        if not weak_openings:
            return None
        
        opening = weak_openings[0]
        
        return {
            "id": task_id,
            "type": "opening_study",
            "title": f"Study {opening.name}",
            "duration": "15 min",
            "description": f"Win rate: {opening.win_rate*100:.1f}% ({opening.games_played} games)",
            "resources": [
                f"https://lichess.org/opening/{opening.eco_code}" if opening.eco_code else "https://lichess.org/opening",
                f"https://www.youtube.com/results?search_query=chess+{opening.name.replace(' ', '+')}"
            ],
            "completed": False,
        }

    def _create_tactics_task(self, task_id: int) -> Dict:
        """Create tactics training task based on common mistakes."""
        # Find most common tactical theme in mistakes
        positions = (
            self.session.query(Position)
            .filter(Position.is_blunder == True)
            .order_by(Position.id.desc())
            .limit(20)
            .all()
        )
        
        theme = "pin"  # Default theme
        # TODO: Classify tactical themes from positions
        
        return {
            "id": task_id,
            "type": "tactics",
            "title": f"Solve 10 {theme} tactics",
            "duration": "10 min",
            "resources": [
                f"https://lichess.org/training/themes/{theme}",
                "https://www.chess.com/puzzles"
            ],
            "completed": False,
        }

    def _create_game_review_task(self, task_id: int) -> Optional[Dict]:
        """Create task to review a recent game with mistakes."""
        # Find recent game with blunders
        game = (
            self.session.query(Game)
            .join(Position)
            .filter(Position.is_blunder == True)
            .filter(Game.analyzed == True)
            .order_by(Game.date.desc())
            .first()
        )
        
        if not game:
            return None
        
        # Count mistakes in this game
        mistakes = (
            self.session.query(Position)
            .filter_by(game_id=game.id, is_mistake=True)
            .count()
        )
        
        blunders = (
            self.session.query(Position)
            .filter_by(game_id=game.id, is_blunder=True)
            .count()
        )
        
        return {
            "id": task_id,
            "type": "game_review",
            "title": f"Review game from {game.date.strftime('%Y-%m-%d')}",
            "duration": "10 min",
            "description": f"{mistakes} mistakes, {blunders} blunders - {game.opening_name}",
            "game_id": game.id,
            "resources": [],
            "completed": False,
        }

    def _create_mistake_pattern_task(self, task_id: int) -> Optional[Dict]:
        """Create task to study common mistake pattern."""
        # Analyze recent mistakes
        recent_mistakes = (
            self.session.query(Position)
            .join(Game)
            .filter(Position.is_mistake == True)
            .order_by(Game.date.desc())
            .limit(50)
            .all()
        )
        
        if not recent_mistakes:
            return None
        
        # Categorize by game phase
        opening_mistakes = sum(1 for m in recent_mistakes if m.move_number <= 15)
        middlegame_mistakes = sum(1 for m in recent_mistakes if 16 <= m.move_number <= 30)
        endgame_mistakes = sum(1 for m in recent_mistakes if m.move_number > 30)
        
        # Find most common phase
        if opening_mistakes >= middlegame_mistakes and opening_mistakes >= endgame_mistakes:
            phase = "opening"
        elif middlegame_mistakes >= endgame_mistakes:
            phase = "middlegame"
        else:
            phase = "endgame"
        
        return {
            "id": task_id,
            "type": "study",
            "title": f"Study {phase} principles",
            "duration": "10 min",
            "description": f"You make {len([m for m in recent_mistakes if self._in_phase(m.move_number, phase)])} mistakes in the {phase}",
            "resources": [
                f"https://www.youtube.com/results?search_query=chess+{phase}+principles"
            ],
            "completed": False,
        }

    def _in_phase(self, move_number: int, phase: str) -> bool:
        """Check if move is in given phase."""
        if phase == "opening":
            return move_number <= 15
        elif phase == "middlegame":
            return 16 <= move_number <= 30
        else:
            return move_number > 30

    def _print_plan(self, plan: DailyPlan):
        """Print plan in readable format."""
        print(f"\n📋 Daily Plan for {plan.date.date()}")
        print("=" * 60)
        
        for task in plan.tasks:
            print(f"\n{task['id']}. {task['title']} ({task['duration']})")
            if task.get('description'):
                print(f"   {task['description']}")
            if task.get('resources'):
                print(f"   Resources: {', '.join(task['resources'][:1])}")

    def close(self):
        self.session.close()


if __name__ == "__main__":
    from sqlalchemy import func
    
    generator = PlanGenerator()
    generator.generate_plan()
    generator.close()
