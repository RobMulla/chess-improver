"""Comprehensive insights generator - mimics chess.com insights."""
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy import and_
from src.database.models import get_session, Game, Position


class ComprehensiveInsights:
    """Generate detailed insights similar to chess.com."""
    
    def __init__(self, days: Optional[int] = None, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None):
        self.session = get_session()
        self.days = days
        self.start_date = start_date
        self.end_date = end_date
    
    def _get_games_query(self):
        """Get filtered games query based on date range."""
        query = self.session.query(Game).filter(Game.analyzed == True)
        
        if self.days:
            cutoff = datetime.utcnow() - timedelta(days=self.days)
            query = query.filter(Game.date >= cutoff)
        elif self.start_date and self.end_date:
            query = query.filter(and_(Game.date >= self.start_date, Game.date <= self.end_date))
        
        return query
    
    def get_overview(self) -> Dict:
        """Get overview stats."""
        games = self._get_games_query().all()
        
        total = len(games)
        won = sum(1 for g in games if (g.result == "1-0" and g.player_color == "white") or (g.result == "0-1" and g.player_color == "black"))
        drawn = sum(1 for g in games if g.result == "1/2-1/2")
        lost = total - won - drawn
        
        return {
            'total_games': total,
            'won': won,
            'drawn': drawn,
            'lost': lost,
            'win_rate': (won / total * 100) if total > 0 else 0,
            'draw_rate': (drawn / total * 100) if total > 0 else 0,
            'loss_rate': (lost / total * 100) if total > 0 else 0,
        }
    
    def get_accuracy_stats(self) -> Dict:
        """Get accuracy statistics."""
        games = self._get_games_query().all()
        
        if not games:
            return {}
        
        # Calculate average accuracy per game
        accuracies = []
        win_accuracies = []
        draw_accuracies = []
        loss_accuracies = []
        
        for game in games:
            positions = self.session.query(Position).filter_by(game_id=game.id).all()
            if positions:
                eval_drops = [p.eval_drop for p in positions if p.eval_drop is not None and p.eval_drop > 0]
                if eval_drops:
                    acc = max(0, 100 - sum(eval_drops) / len(eval_drops) / 10)
                    accuracies.append(acc)
                    
                    # Categorize by result
                    is_win = (game.result == "1-0" and game.player_color == "white") or (game.result == "0-1" and game.player_color == "black")
                    is_draw = game.result == "1/2-1/2"
                    
                    if is_win:
                        win_accuracies.append(acc)
                    elif is_draw:
                        draw_accuracies.append(acc)
                    else:
                        loss_accuracies.append(acc)
        
        return {
            'overall': sum(accuracies) / len(accuracies) if accuracies else 0,
            'when_win': sum(win_accuracies) / len(win_accuracies) if win_accuracies else 0,
            'when_draw': sum(draw_accuracies) / len(draw_accuracies) if draw_accuracies else 0,
            'when_loss': sum(loss_accuracies) / len(loss_accuracies) if loss_accuracies else 0,
        }
    
   def get_game_phase_stats(self) -> Dict:
        """Get stats by game phase (opening/middlegame/endgame)."""
        games = self._get_games_query().all()
        
        phase_stats = {
            'opening': {'count': 0, 'won': 0, 'drawn': 0, 'lost': 0, 'mistakes': 0},
            'middlegame': {'count': 0, 'won': 0, 'drawn': 0, 'lost': 0, 'mistakes': 0},
            'endgame': {'count': 0, 'won': 0, 'drawn': 0, 'lost': 0, 'mistakes': 0},
        }
        
        for game in games:
            positions = self.session.query(Position).filter_by(game_id=game.id).all()
            if not positions:
                continue
            
            # Determine which phase the game ended in
            last_move = max(p.move_number for p in positions) if positions else 0
            
            if last_move <= 15:
                phase = 'opening'
            elif last_move <= 40:
                phase = 'middlegame'
            else:
                phase = 'endgame'
            
            phase_stats[phase]['count'] += 1
            
            # Count result
            is_win = (game.result == "1-0" and game.player_color == "white") or (game.result == "0-1" and game.player_color == "black")
            is_draw = game.result == "1/2-1/2"
            
            if is_win:
                phase_stats[phase]['won'] += 1
            elif is_draw:
                phase_stats[phase]['drawn'] += 1
            else:
                phase_stats[phase]['lost'] += 1
            
            # Count mistakes by phase
            for pos in positions:
                if pos.is_mistake:
                    if pos.move_number <= 15:
                        phase_stats['opening']['mistakes'] += 1
                    elif pos.move_number <= 40:
                        phase_stats['middlegame']['mistakes'] += 1
                    else:
                        phase_stats['endgame']['mistakes'] += 1
        
        return phase_stats
    
    def get_tactical_stats(self) -> Dict:
        """Get tactical pattern statistics (simplified for now)."""
        games = self._get_games_query().all()
        
        total_mistakes = 0
        total_blunders = 0
        total_inaccuracies = 0
        
        for game in games:
            positions = self.session.query(Position).filter_by(game_id=game.id).all()
            for pos in positions:
                if pos.is_blunder:
                    total_blunders += 1
                elif pos.is_mistake:
                    total_mistakes += 1
                elif pos.eval_drop and pos.eval_drop > 30:  # Inaccuracy threshold
                    total_inaccuracies += 1
        
        return {
            'mistakes': total_mistakes,
            'blunders': total_blunders,
            'inaccuracies': total_inaccuracies,
        }
    
    def get_opening_performance(self, limit: int = 10) -> List[Dict]:
        """Get performance in top openings."""
        games = self._get_games_query().all()
        
        opening_stats = defaultdict(lambda: {'total': 0, 'won': 0, 'drawn': 0, 'lost': 0, 'name': ''})
        
        for game in games:
            if not game.opening_name:
                continue
            
            opening = game.opening_name
            opening_stats[opening]['name'] = opening
            opening_stats[opening]['total'] += 1
            
            is_win = (game.result == "1-0" and game.player_color == "white") or (game.result == "0-1" and game.player_color == "black")
            is_draw = game.result == "1/2-1/2"
            
            if is_win:
                opening_stats[opening]['won'] += 1
            elif is_draw:
                opening_stats[opening]['drawn'] += 1
            else:
                opening_stats[opening]['lost'] += 1
        
        # Sort by total games
        sorted_openings = sorted(opening_stats.values(), key=lambda x: x['total'], reverse=True)[:limit]
        
        # Calculate percentages
        for opening in sorted_openings:
            total = opening['total']
            opening['win_pct'] = (opening['won'] / total * 100) if total > 0 else 0
            opening['draw_pct'] = (opening['drawn'] / total * 100) if total > 0 else 0
            opening['loss_pct'] = (opening['lost'] / total * 100) if total > 0 else 0
        
        return sorted_openings
    
    def close(self):
        self.session.close()


if __name__ == "__main__":
    insights = ComprehensiveInsights(days=365)  # Last year
    
    print("📊 Overview:")
    overview = insights.get_overview()
    print(f"  Total games: {overview['total_games']}")
    print(f"  Win rate: {overview['win_rate']:.1f}%")
    
    print("\n🎯 Accuracy:")
    accuracy = insights.get_accuracy_stats()
    print(f"  Overall: {accuracy['overall']:.1f}%")
    print(f"  When winning: {accuracy['when_win']:.1f}%")
    print(f"  When losing: {accuracy['when_loss']:.1f}%")
    
    print("\n♟️  Game Phases:")
    phases = insights.get_game_phase_stats()
    for phase, stats in phases.items():
        print(f"  {phase.capitalize()}: {stats['count']} games, {stats['mistakes']} mistakes")
    
    print("\n📖 Top Openings:")
    openings = insights.get_opening_performance(5)
    for opening in openings:
        print(f"  {opening['name']}: {opening['total']} games ({opening['win_pct']:.1f}% win)")
    
    insights.close()
