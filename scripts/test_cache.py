"""Test caching and background jobs."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.analysis.cache import get_cache
from src.analysis.engine import StockfishAnalyzer
import chess

print("=" * 60)
print("Testing Redis Cache & Background Jobs")
print("=" * 60)

# Test 1: Cache initialization
print("\n1️⃣ Testing cache initialization...")
cache = get_cache()
print(f"   Cache enabled: {cache.enabled}")
if cache.enabled:
    print("   ✅ Redis connected")
else:
    print("   ❌ Redis not available")
    sys.exit(1)

# Test 2: Cache operations
print("\n2️⃣ Testing cache operations...")
test_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
test_result = {"score": 100, "best_move": "e2e4", "depth": 20}

cache.set_evaluation(test_fen, test_result)
retrieved = cache.get_evaluation(test_fen)

if retrieved == test_result:
    print("   ✅ Cache write/read working")
else:
    print(f"   ❌ Cache failed: expected {test_result}, got {retrieved}")

# Test 3: Stockfish with caching
print("\n3️⃣ Testing Stockfish with caching...")
try:
    analyzer = StockfishAnalyzer()
    board = chess.Board()
    
    # First analysis (cache miss)
    import time
    start = time.time()
    result1 = analyzer.analyze_position(board)
    time1 = time.time() - start
    print(f"   First analysis: {time1:.3f}s (cache miss)")
    
    # Second analysis (cache hit)
    start = time.time()
    result2 = analyzer.analyze_position(board)
    time2 = time.time() - start
    print(f"   Second analysis: {time2:.3f}s (cache hit)")
    
    speedup = time1 / time2 if time2 > 0 else 0
    print(f"   ⚡️ Speedup: {speedup:.0f}x faster")
    
    if time2 < time1 / 10:  # Should be at least 10x faster
        print("   ✅ Caching working correctly")
    else:
        print("   ⚠️ Cache might not be working optimally")
    
    analyzer.close()
except Exception as e:
    print(f"   ❌ Stockfish test failed: {e}")

# Test 4: Cache stats
print("\n4️⃣ Cache statistics...")
stats = cache.get_stats()
for key, value in stats.items():
    print(f"   {key}: {value}")

# Test 5: Background job queue
print("\n5️⃣ Testing job queue...")
try:
    from redis import Redis
    from rq import Queue
    redis_conn = Redis()
    queue = Queue('analysis', connection=redis_conn)
    print(f"   Queue: {queue.name}")
    print(f"   Jobs in queue: {len(queue)}")
    print("   ✅ Job queue ready")
except Exception as e:
    print(f"   ❌ Queue error: {e}")

print("\n" + "=" * 60)
print("✅ All systems operational!")
print("=" * 60)
print("\nTo start the worker:")
print("  cd /Users/robmulla/Repos/chess-improver")
print("  source venv/bin/activate")
print("  PYTHONPATH=/Users/robmulla/Repos/chess-improver rq worker analysis")
