"""Analyze opening mistake patterns."""
from collections import defaultdict
from typing import List, Dict
from src.database.models import get_session, Game, Position


class OpeningMistakeAnalyzer:
    """Identify common positions where mistakes occur in openings."""
    
    def __init__(self):
        self.session = get_session()
    
    def find_critical_positions(self, min_occurrences: int = 2) -> List[Dict]:
        """
        Find positions in openings where mistakes frequently occur.
        
        Returns list of critical positions with FEN, frequency, and details.
        """
        print("🔍 Analyzing opening mistake patterns...")
        
        # Get all opening phase mistakes (first 15 moves)
        opening_mistakes = (
            self.session.query(Position)
            .filter(Position.move_number <= 15)
            .filter(Position.is_mistake == True)
            .all()
        )
        
        # Group by FEN position
        position_mistakes = defaultdict(lambda: {
            'count': 0,
            'fen': None,
            'move_number': None,
            'games': [],
            'avg_eval_drop': 0,
            'sum_eval_drop': 0,
            'best_moves': [],
            'player_moves': []
        })
        
        for pos in opening_mistakes:
            fen = pos.fen
            position_mistakes[fen]['count'] += 1
            position_mistakes[fen]['fen'] = fen
            position_mistakes[fen]['move_number'] = pos.move_number
            position_mistakes[fen]['sum_eval_drop'] += pos.eval_drop
            position_mistakes[fen]['best_moves'].append(pos.best_move)
            position_mistakes[fen]['player_moves'].append(pos.player_move)
            
            # Get game info
            game = self.session.query(Game).get(pos.game_id)
            if game:
                position_mistakes[fen]['games'].append({
                    'id': game.id,
                    'date': game.date,
                    'opening': game.opening_name,
                    'result': game.result
                })
        
        # Filter and format results
        critical_positions = []
        for fen, data in position_mistakes.items():
            if data['count'] >= min_occurrences:
                data['avg_eval_drop'] = data['sum_eval_drop'] / data['count']
                # Get most common best move
                best_move_counts = defaultdict(int)
                for move in data['best_moves']:
                    if move:
                        best_move_counts[move] += 1
                data['recommended_move'] = max(best_move_counts.items(), key=lambda x: x[1])[0] if best_move_counts else None
                
                critical_positions.append(data)
        
        # Sort by frequency
        critical_positions.sort(key=lambda x: x['count'], reverse=True)
        
        print(f"✅ Found {len(critical_positions)} critical positions")
        self._print_summary(critical_positions[:10])
        
        return critical_positions
    
    def _print_summary(self, positions: List[Dict]):
        """Print summary of critical positions."""
        if not positions:
            print("No critical positions found")
            return
        
        print("\n📍 Top 10 Critical Opening Positions:")
        print("=" * 80)
        print(f"{'Move':<6} {'Times':<7} {'Avg Loss':<10} {'Opening':<30}")
        print("-" * 80)
        
        for pos in positions:
            opening_name = pos['games'][0]['opening'] if pos['games'] else 'Unknown'
            avg_loss = pos['avg_eval_drop']
            
            print(
                f"{pos['move_number']:<6} "
                f"{pos['count']:<7} "
                f"{avg_loss:>6.0f} cp   "
                f"{opening_name[:30]:<30}"
            )
    
    def get_practice_positions(self, limit: int = 5) -> List[Dict]:
        """Get positions to practice, formatted for chess board display."""
        critical = self.find_critical_positions()
        
        practice_positions = []
        for pos in critical[:limit]:
            practice_positions.append({
                'fen': pos['fen'],
                'move_number': pos['move_number'],
                'frequency': pos['count'],
                'recommended_move': pos['recommended_move'],
                'opening': pos['games'][0]['opening'] if pos['games'] else 'Unknown',
                'description': f"Move {pos['move_number']} - {pos['count']}x mistakes, avg {pos['avg_eval_drop']:.0f}cp loss"
            })
        
        return practice_positions
    
    def close(self):
        self.session.close()


if __name__ == "__main__":
    analyzer = OpeningMistakeAnalyzer()
    critical_positions = analyzer.find_critical_positions()
    
    print(f"\n\n📚 Practice these {min(5, len(critical_positions))} positions:")
    practice = analyzer.get_practice_positions(5)
    for i, pos in enumerate(practice, 1):
        print(f"\n{i}. {pos['description']}")
        print(f"   Opening: {pos['opening']}")
        print(f"   FEN: {pos['fen']}")
        print(f"   Try: {pos['recommended_move']}")
    
    analyzer.close()
