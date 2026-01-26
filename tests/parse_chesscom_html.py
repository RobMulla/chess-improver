"""Parse Chess.com HTML analysis to extract move-by-move classifications."""
import re
from collections import Counter

html_file = "/Users/robmulla/Repos/chess-improver/tests/chess_dot_com_analysis_example/RobM83 vs. JosePater30 _ Analysis - Chess.com.html"

with open(html_file, 'r', encoding='utf-8') as f:
    html = f.read()

# Find all move classifications in the HTML
# Chess.com uses classes like "move-best", "move-excellent", etc.
pattern = r'move-(best|excellent|good|great|brilliant|inaccuracy|mistake|blunder|book)'
matches = re.findall(pattern, html, re.IGNORECASE)

print("🔍 Chess.com Move-by-Move Classifications\n")
print(f"Total moves found: {len(matches)}")

# Count each type
counter = Counter(m.lower() for m in matches)

print("\nBreakdown:")
for classification, count in sorted(counter.items(), key=lambda x: -x[1]):
    print(f"  {classification}: {count}")

# Filter to just player moves (every other one, since it alternates white/black)
print("\n📊 Assuming you played White (every odd move):")
player_moves = [matches[i].lower() for i in range(0, len(matches), 2)]
player_counter = Counter(player_moves)

for classification, count in sorted(player_counter.items(), key=lambda x: -x[1]):
    print(f"  {classification}: {count}")

print(f"\nTotal player moves: {len(player_moves)}")
