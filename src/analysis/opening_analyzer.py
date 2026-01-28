"""Opening repertoire analyzer."""
from collections import defaultdict

from src.database.models import Game, Opening, Position, get_session


class OpeningAnalyzer:
    """Analyze opening performance."""

    def __init__(self):
        self.session = get_session()

    def analyze_openings(self):
        """Analyze all openings and update database."""
        print("📚 Analyzing opening repertoire...")

        # Get all games grouped by opening
        games = self.session.query(Game).filter(Game.opening_name.isnot(None)).all()

        opening_stats = defaultdict(
            lambda: {"games": 0, "wins": 0, "draws": 0, "losses": 0, "eco": None, "accuracies": []}
        )

        for game in games:
            opening_name = game.opening_name

            # Get result
            if game.result == "1-0":
                result = "win" if game.player_color == "white" else "loss"
            elif game.result == "0-1":
                result = "loss" if game.player_color == "white" else "win"
            else:
                result = "draw"

            # Calculate game accuracy
            positions = self.session.query(Position).filter_by(game_id=game.id).all()
            if positions:
                eval_drops = [p.eval_drop for p in positions if p.eval_drop > 0]
                if eval_drops:
                    accuracy = max(0, 100 - sum(eval_drops) / len(eval_drops) / 10)
                    opening_stats[opening_name]["accuracies"].append(accuracy)

            # Update stats
            opening_stats[opening_name]["games"] += 1
            if result == "win":
                opening_stats[opening_name]["wins"] += 1
            elif result == "draw":
                opening_stats[opening_name]["draws"] += 1
            elif result == "loss":
                opening_stats[opening_name]["losses"] += 1
            opening_stats[opening_name]["eco"] = game.opening_eco

        # Update database
        for opening_name, stats in opening_stats.items():
            avg_accuracy = (
                sum(stats["accuracies"]) / len(stats["accuracies"]) if stats["accuracies"] else None
            )

            # Get or create opening
            opening = self.session.query(Opening).filter_by(name=opening_name).first()
            if not opening:
                opening = Opening(name=opening_name)
                self.session.add(opening)

            # Update stats
            opening.eco_code = stats["eco"]
            opening.games_played = stats["games"]
            opening.wins = stats["wins"]
            opening.draws = stats["draws"]
            opening.losses = stats["losses"]
            opening.avg_accuracy = avg_accuracy

        self.session.commit()

        print(f"✅ Analyzed {len(opening_stats)} openings")

        # Print summary
        self._print_summary()

    def _print_summary(self):
        """Print opening performance summary."""
        openings = (
            self.session.query(Opening)
            .filter(Opening.games_played >= 3)  # At least 3 games
            .order_by(Opening.games_played.desc())
            .limit(10)
            .all()
        )

        print("\n📊 Top 10 Openings by Games Played:")
        print("=" * 80)
        print(f"{'Opening':<40} {'Games':>6} {'W/D/L':>10} {'Win%':>7} {'Acc%':>7}")
        print("-" * 80)

        for opening in openings:
            win_pct = opening.win_rate * 100
            acc_str = f"{opening.avg_accuracy:.1f}%" if opening.avg_accuracy else "N/A"

            print(
                f"{opening.name[:40]:<40} "
                f"{opening.games_played:>6} "
                f"{opening.wins:>3}/{opening.draws:>2}/{opening.losses:>2} "
                f"{win_pct:>6.1f}% "
                f"{acc_str:>7}"
            )

    def get_weak_openings(self, min_games: int = 5) -> list[Opening]:
        """Get openings with poor performance."""
        openings = self.session.query(Opening).filter(Opening.games_played >= min_games).all()

        # Sort by win rate
        weak_openings = sorted(openings, key=lambda o: o.win_rate)[:5]

        return weak_openings

    def close(self):
        self.session.close()


if __name__ == "__main__":
    analyzer = OpeningAnalyzer()
    analyzer.analyze_openings()
    analyzer.close()
