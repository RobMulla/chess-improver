"""Generate insights from analyzed games."""
from datetime import datetime, timedelta
from typing import Dict, List
from sqlalchemy import func
from src.database.models import get_session, Game, Position, Insight


class InsightsGenerator:
    """Generate chess.com-style insights from analyzed data."""

    def __init__(self):
        self.session = get_session()

    def generate_all_insights(self):
        """Generate all insights."""
        print("📊 Generating insights...")
        
        self.accuracy_trends()
        self.performance_by_time_control()
        self.performance_by_opponent_rating()
        self.common_mistakes()
        
        print("✅ Insights generated!")

    def accuracy_trends(self):
        """Calculate accuracy trends over time."""
        # Get analyzed games with positions
        games = (
            self.session.query(Game)
            .filter_by(analyzed=True)
            .order_by(Game.date)
            .all()
        )
        
        if not games:
            print("⚠️ No analyzed games found")
            return
        
        # Calculate accuracy for each game
        accuracies = []
        for game in games:
            positions = self.session.query(Position).filter_by(game_id=game.id).all()
            eval_drops = [p.eval_drop for p in positions if p.eval_drop > 0]
            
            if eval_drops:
                accuracy = max(0, 100 - sum(eval_drops) / len(eval_drops) / 10)
                accuracies.append({
                    'date': game.date,
                    'accuracy': accuracy
                })
        
        if not accuracies:
            return
        
        # Overall average
        avg_accuracy = sum(a['accuracy'] for a in accuracies) / len(accuracies)
        
        # Recent (last 30 days)
        cutoff = datetime.utcnow() - timedelta(days=30)
        recent = [a for a in accuracies if a['date'] >= cutoff]
        recent_avg = sum(a['accuracy'] for a in recent) / len(recent) if recent else avg_accuracy
        
        # Save insights
        self._save_insight("avg_accuracy", avg_accuracy, "all_time", "accuracy")
        self._save_insight("avg_accuracy", recent_avg, "last_30_days", "accuracy")
        
        print(f"  📈 Average accuracy: {avg_accuracy:.1f}% (last 30d: {recent_avg:.1f}%)")

    def performance_by_time_control(self):
        """Analyze performance by time control."""
        games = self.session.query(Game).filter_by(analyzed=True).all()
        
        time_controls = {}
        for game in games:
            tc = game.time_control or "unknown"
            if tc not in time_controls:
                time_controls[tc] = {'wins': 0, 'draws': 0, 'losses': 0, 'total': 0}
            
            # Parse result
            if game.result == "1-0":
                result = "wins" if game.player_color == "white" else "losses"
            elif game.result == "0-1":
                result = "losses" if game.player_color == "white" else "wins"
            else:
                result = "draws"
            
            time_controls[tc][result] += 1
            time_controls[tc]['total'] += 1
        
        print(f"\n  ⏱️  Performance by time control:")
        for tc, stats in sorted(time_controls.items(), key=lambda x: -x[1]['total']):
            win_rate = (stats['wins'] + 0.5 * stats['draws']) / stats['total'] * 100
            print(f"    {tc}: {stats['total']} games, {win_rate:.1f}% score")

    def performance_by_opponent_rating(self):
        """Analyze performance vs different rating ranges."""
        games = self.session.query(Game).filter_by(analyzed=True).all()
        
        rating_buckets = {
            'lower': {'range': (-999, -200), 'record': [0, 0, 0]},  # Much lower
            'similar': {'range': (-200, 200), 'record': [0, 0, 0]},  # Similar
            'higher': {'range': (200, 999), 'record': [0, 0, 0]},  # Much higher
        }
        
        for game in games:
            if not game.player_rating or not game.opponent_rating:
                continue
            
            rating_diff = game.opponent_rating - game.player_rating
            
            # Determine bucket
            bucket = None
            for key, data in rating_buckets.items():
                if data['range'][0] <= rating_diff <= data['range'][1]:
                    bucket = key
                    break
            
            if not bucket:
                continue
            
            # Record result
            if game.result == "1-0":
                idx = 0 if game.player_color == "white" else 2
            elif game.result == "0-1":
                idx = 2 if game.player_color == "white" else 0
            else:
                idx = 1
            
            rating_buckets[bucket]['record'][idx] += 1
        
        print(f"\n  🎯 Performance vs opponent rating:")
        for name, data in rating_buckets.items():
            w, d, l = data['record']
            total = w + d + l
            if total > 0:
                score = (w + 0.5 * d) / total * 100
                print(f"    {name.capitalize()}: +{w} ={d} -{l} ({score:.1f}%)")

    def common_mistakes(self):
        """Identify common mistake patterns."""
        # Count mistakes by move number ranges
        move_ranges = {
            'opening': (1, 15),
            'middlegame': (16, 30),
            'endgame': (31, 100),
        }
        
        mistakes_by_phase = {}
        for phase in move_ranges:
            mistakes_by_phase[phase] = 0
        
        positions = (
            self.session.query(Position)
            .filter(Position.is_mistake == True)
            .all()
        )
        
        for pos in positions:
            for phase, (min_move, max_move) in move_ranges.items():
                if min_move <= pos.move_number <= max_move:
                    mistakes_by_phase[phase] += 1
                    break
        
        print(f"\n  ⚠️  Mistakes by game phase:")
        total = sum(mistakes_by_phase.values())
        if total > 0:
            for phase, count in mistakes_by_phase.items():
                pct = count / total * 100
                print(f"    {phase.capitalize()}: {count} ({pct:.1f}%)")

    def _save_insight(self, name: str, value: float, period: str, category: str):
        """Save insight to database."""
        insight = Insight(
            metric_name=name,
            metric_value=value,
            time_period=period,
            category=category,
        )
        self.session.add(insight)
        self.session.commit()

    def close(self):
        self.session.close()


if __name__ == "__main__":
    generator = InsightsGenerator()
    generator.generate_all_insights()
    generator.close()
