# Code Cleanup & Coverage Audit

## 📊 Current Coverage: 40%

### Coverage by Module:
```
High Coverage (>80%):
✅ move_classifier.py      96%
✅ win_chance.py           98%
✅ database/models.py      94%
✅ game_analyzer.py        80%

Medium Coverage (40-80%):
⚠️ cache.py               63%
⚠️ engine.py              57%
⚠️ collectors/lichess.py  53%
⚠️ collectors/base.py     42%
⚠️ collectors/chess_com.py 42%

Zero Coverage (0%):
❌ web/app.py              0%  (285 lines)
❌ insights_generator.py   0%  (107 lines)
❌ opening_mistakes.py     0%  (66 lines)
❌ opening_analyzer.py    16%  (67 lines)
❌ plan_generator.py      19%  (96 lines)
❌ workers/analyzer_worker.py 31%
```

---

## 🗑️ Files to DELETE (Obsolete/Redundant)

### scripts/ folder - Analysis:
```
scripts/analyze_5.py          → DELETE (one-off test)
scripts/analyze_losses.py     → DELETE (superseded by web UI)
scripts/analyze_one_loss.py   → DELETE (one-off test)
scripts/extract_openings.py   → KEEP (utility, not yet in UI)
scripts/find_mistakes.py      → DELETE (superseded by web UI)
scripts/reanalyze_games.py    → DELETE (can do via web UI)
scripts/test_cache.py         → DELETE (use proper tests)
scripts/test_one_game.py      → DELETE (one-off test)
```

**Decision:** Delete 7/8 scripts, keep only `extract_openings.py` temporarily

### cli/ folder - Keep for now:
```
cli/sync_games.py        → KEEP (until web UI has import)
cli/analyze_games.py     → KEEP (until web UI has bulk analyze)
cli/generate_plan.py     → KEEP (until web UI has plan gen)
```

**Decision:** Keep CLI tools until Phase 1 of web UI is complete

### src/ modules - Analysis:
```
src/analysis/comprehensive_insights.py  → CHECK (may be duplicate)
src/analysis/insights_generator.py      → KEEP (needed, just untested)
src/analysis/opening_analyzer.py        → KEEP (needed for opening detection)
src/analysis/opening_mistakes.py        → DELETE? (may be redundant)
```

---

## 📝 Actions Plan

### Phase 1: Delete Obsolete Scripts
```bash
rm scripts/analyze_5.py
rm scripts/analyze_losses.py
rm scripts/analyze_one_loss.py
rm scripts/find_mistakes.py
rm scripts/reanalyze_games.py
rm scripts/test_cache.py
rm scripts/test_one_game.py
```

### Phase 2: Add Test Coverage for Untested Modules

**Priority 1 - Web App (0% coverage):**
- [ ] tests/test_web_app.py
  - Test all Flask routes
  - Test API endpoints
  - Mock database calls
  - Target: >80% coverage

**Priority 2 - Background Workers (31% coverage):**
- [ ] tests/test_workers.py
  - Test analyzer_worker
  - Test job queueing
  - Test error handling
  - Target: >80% coverage

**Priority 3 - Collectors (42-53% coverage):**
- [ ] Expand test_collectors.py
  - Test Chess.com API
  - Test Lichess API
  - Mock HTTP requests
  - Test error cases
  - Target: >70% coverage

**Priority 4 - Analysis Modules:**
- [ ] tests/test_opening_analyzer.py (16% → 70%)
- [ ] tests/test_insights_generator.py (0% → 70%)
- [ ] tests/test_plan_generator.py (19% → 70%)

### Phase 3: Add Coverage Enforcement to Pre-commit

Add to `.pre-commit-config.yaml`:
```yaml
  # Test coverage check
  - repo: local
    hooks:
      - id: pytest-coverage
        name: pytest coverage
        entry: bash -c 'pytest tests/ --cov=src --cov-fail-under=50 -q'
        language: system
        pass_filenames: false
        always_run: true
```

This will:
- Run tests on every commit
- Require minimum 50% coverage
- Block commit if coverage drops
- Gradually increase threshold to 80%

---

## 🎯 Coverage Goals

**Current:** 40%
**Phase 1 (Week 1):** 50% (delete scripts, basic web tests)
**Phase 2 (Week 2):** 65% (workers, collectors)
**Phase 3 (Week 3):** 80% (comprehensive coverage)

---

## ⚠️ Findings

**Test Failures:**
- 5 tests currently failing (need to fix)
- Most are integration tests
- May be environmental or session related

**Coverage Gaps:**
- Web app has ZERO tests
- Background workers undertested
- Opening analysis not tested
- Insights generation not tested

**Recommendation:**
1. Fix 5 failing tests first
2. Delete obsolete scripts
3. Add basic web app tests
4. Enable coverage pre-commit hook at 40% (current)
5. Gradually increase threshold as we add tests
