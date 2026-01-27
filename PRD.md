# Chess Improver - Product Requirements Document

## 🎯 Vision

**Chess Improver** is a web-based chess training platform that analyzes your games from Chess.com and Lichess, identifies your mistakes, and helps you improve through targeted practice and data-driven insights.

**Mission:** Make chess improvement accessible, personalized, and data-driven for players of all levels.

---

## 👥 Target Users

**Primary:** Amateur chess players (800-2000 ELO) who:
- Play regularly on Chess.com or Lichess
- Want to improve systematically
- Prefer visual, interactive learning over reading
- Have 10-30 minutes daily for training

**Secondary:** Chess coaches who want to:
- Track student progress
- Generate practice material from student games
- Identify patterns in student play

---

## 🎨 Core User Experience

### User Journey
1. **Import** games from Chess.com/Lichess automatically
2. **Analyze** games in background with Stockfish
3. **Review** personalized dashboard with accuracy trends
4. **Practice** past mistakes in interactive trainer
5. **Improve** based on data-driven insights

### Key Differentiators
- **Automatic game import** - No manual PGN uploads
- **Background analysis** - Never blocks the UI
- **Mistake-focused training** - Practice your actual errors
- **Beautiful visualizations** - Make data engaging
- **Zero setup** - Web-based, no installation

---

## 🏗️ Product Architecture

### Technology Stack
**Frontend:**
- HTML/CSS/JavaScript (vanilla - no framework bloat)
- Interactive chessboard (chess.js + chessboard.js)
- Chart.js for visualizations

**Backend:**
- Python Flask (lightweight, proven)
- Stockfish chess engine (analysis)
- Redis (caching + job queue)
- SQLite (database - simple, reliable)

**Testing:**
- pytest (Python unit/integration tests)
- Test coverage target: >80%
- All tests must pass before merging

**Infrastructure:**
- Local dev server (port 5555)
- Background worker (RQ)
- Future: Docker deployment

---

## 🧪 Testing Requirements (MANDATORY)

**Test-Driven Development Philosophy:**
> Every feature, bug fix, and code change MUST have corresponding tests that pass before the code is considered complete.

### Rules
1. **No Code Without Tests** - Every new function/feature needs test coverage
2. **Tests Must Pass** - All tests in `tests/` must pass before moving to next task
3. **Test Before Fix** - For bugs, write failing test first, then fix
4. **Regression Prevention** - Add test for every bug found

### Test Structure
```
tests/
├── test_chess_improver.py      # Core functionality
├── test_phase1_features.py     # Phase-specific features  
├── test_win_chance.py          # Win% algorithm
├── test_integration.py         # End-to-end tests
└── test_golden_chesscom.py     # Chess.com validation
```

### Running Tests
```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_win_chance.py -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

### Test Coverage Goals
- **Core algorithms:** 100% (move_classifier, win_chance, engine)
- **API endpoints:** 90%
- **UI helpers:** 70%
- **Overall project:** >80%

---

## ✨ Feature Specifications

### 1. Dashboard (Landing Page)

**Purpose:** High-level overview of chess improvement journey

**Components:**
- **Stats Cards**
  - Total games imported
  - Games analyzed
  - Average accuracy (last 30 days)
  - Improvement trend (+X% vs last month)

- **Recent Activity**
  - Last 5 analyzed games with quick stats
  - Quick-action buttons (Analyze More, Practice)

- **Today's Training Plan**
  - Recommended practice positions (3-5 per day)
  - Based on recent mistake patterns
  - One-click to start practice

**Success Metrics:**
- Time on dashboard < 30s (quick scan)
- Click-through to practice > 40%

---

### 2. Games Library

**Purpose:** Browse and filter all imported games

**Features:**
- **Table View**
  - Columns: Date, Platform, Opening, Result, Accuracy, Mistakes
  - Sortable by any column
  - Pagination (50 games per page)

- **Filters**
  - Date range picker
  - Platform (Chess.com / Lichess)
  - Result (Win / Draw / Loss)
  - Accuracy range (slider)
  - Game phase (Opening / Middlegame / Endgame errors)

- **Quick Actions**
  - Click game → Full game review
  - "Re-analyze" button for old games
  - Export to PGN

**Nice to Have:**
- Bulk operations (analyze selected games)
- Save filter presets

---

### 3. Game Review (Deep Dive)

**Purpose:** Detailed analysis of single game

**Layout:**
- **Left:** Interactive chessboard
- **Right:** Move list with annotations

**Features:**
- Color-coded moves (best/good/inaccuracy/mistake/blunder)
- Click move → Show position + engine evaluation
- Mistake highlights with:
  - What you played
  - Best move (engine recommendation)
  - Evaluation drop (centipawns + win%)
  - Why it's a mistake (position explanation - future AI)

- **Navigation**
  - Previous/Next buttons
  - Jump to first mistake
  - Keyboard shortcuts (←/→)

---

### 4. Practice Mistakes

**Purpose:** Interactive trainer for past mistakes

**Setup Screen:**
- **Filters:**
  - Color (White / Black / Both)
  - Mistake type (All / Blunders / Mistakes / Inaccuracies)
  - Game phase (All / Opening / Middlegame / Endgame)
  - Date range (Last week / month / all time)

- **Settings:**
  - Time limit per position (30s / 60s / unlimited)
  - Difficulty (show hints / no hints)
  - Number of positions (5 / 10 / 20)

**Practice Mode:**
- Show position where mistake was made
- User makes move
- Immediate feedback:
  - ✅ Correct → Show why it's best
  - ❌ Wrong → Highlight mistake, show correct move
  - Option to try again or continue

- **Progress Tracking:**
  - Accuracy rate during session
  - Time per move
  - Session stats at end

**Gamification:**
- Streak counter (consecutive correct moves)
- Daily practice goal (e.g., "Practice 10 positions")
- Achievement badges (future)

---

### 5. Insights & Analytics

**Purpose:** Data-driven understanding of chess patterns

**Sections:**

**A. Accuracy Trends**
- Line chart: Accuracy over time (last 30/90/365 days)
- Breakdown by color (White vs Black)
- Breakdown by time control (Blitz / Rapid / Classical)

**B. Mistake Patterns**
- Pie chart: Mistake distribution (Blunders / Mistakes / Inaccuracies)
- Bar chart: Mistakes by game phase
- Heatmap: Common mistake square patterns (future)

**C. Opening Performance**
- Table: Your top 10 openings
  - Win rate
  - Average accuracy
  - Games played
- Identify weak openings (low win rate or accuracy)

**D. Time Management**
- Scatter plot: Move time vs accuracy
- Insight: "You blunder when moving in < 5 seconds"
- Recommend optimal thinking time

**E. Improvement Areas**
- Top 3 recommendation cards:
  - "Practice endgames - 40% of your mistakes"
  - "Study the Italian Game - only 65% accuracy"
  - "Slow down in middlegame - rushed moves = blunders"

---

### 6. Settings & Configuration

**Game Import:**
- Chess.com username (auto-import latest games)
- Lichess username (auto-import latest games)
- Import frequency (Daily / Weekly / Manual)
- Date range to import

**Analysis Settings:**
- Stockfish depth (15 / 20 / 25 ply)
- Auto-analyze new games (On / Off)
- Cache settings (Clear cache button)

**UI Preferences:**
- Board theme (blue / green / brown)
- Piece set (classic / modern / etc.)
- Dark mode toggle

---

## 🔧 Technical Requirements

### Performance
- **Page load:** < 2 seconds
- **Game analysis:** < 30 seconds (background, non-blocking)
- **Practice mode:** < 100ms move response
- **Cache hit rate:** > 80% for re-analysis

### Scalability
- Support 100K+ games per user
- Handle 10+ concurrent analyses
- Database queries < 100ms

### Reliability
- Graceful degradation if Redis down (no caching)
- Error handling on all API endpoints
- Auto-retry failed analysis jobs

### Security
- No authentication (local-only for now)
- Future: OAuth for Chess.com/Lichess import
- Sanitize all user inputs

---

## 📊 Success Metrics

### Engagement
- Daily active users (target: 70% of registered)
- Average session time (target: 15 minutes)
- Practice sessions per week (target: 3+)

### Core Metrics
- Games analyzed per user (target: 50+)
- Practice completion rate (target: 60%+)
- Insights viewed per session (target: 1+)

### Quality
- Analysis accuracy (match Chess.com ±10%)
- Bug reports per week (target: < 5)
- UI response time < 100ms (target: 95% requests)

---

## 🚀 Roadmap

### Phase 1: MVP (Current) ✅
- [x] Game import from Chess.com/Lichess
- [x] Background analysis with Stockfish
- [x] Basic dashboard
- [x] Games library
- [x] Practice setup screen
- [ ] **FIX: Accurate move classification**
- [ ] **FIX: Opening name detection**

### Phase 2: Core Training (Next)
- [ ] Working practice mode with feedback
- [ ] Game review page with annotations
- [ ] Basic insights (accuracy trends only)

### Phase 3: Advanced Analytics
- [ ] Full insights dashboard
- [ ] Time analysis
- [ ] Opening repertoire tracking
- [ ] Pattern recognition

### Phase 4: Enhancement
- [ ] AI-powered explanations (GPT-4 integration)
- [ ] Spaced repetition algorithm
- [ ] Mobile-responsive design
- [ ] Shareable game reviews

### Phase 5: Social & Scale
- [ ] User accounts & auth
- [ ] Cloud deployment
- [ ] Coach dashboard
- [ ] Community features

---

## 🐛 Known Issues (Critical to Fix)

### 1. Move Classification (HIGHEST PRIORITY)
**Problem:** All games showing 100% accuracy
**Impact:** Blocks practice system and insights
**Solution:** Debug Win% algorithm integration
**ETA:** 2-4 hours

### 2. Opening Names
**Problem:** Most openings showing "Unknown"
**Impact:** Poor user experience, can't filter by opening
**Solution:** Integrate chess-openings library or API
**ETA:** 1 hour

### 3. Empty Insights
**Problem:** "No insights available"
**Impact:** Missing key value proposition
**Solution:** Requires fix #1 (mistake data) + basic charts
**ETA:** 3 hours (after fix #1)

---

## 💡 Future Ideas (Backlog)

- **Puzzle Rush Mode:** Solve positions under time pressure
- **Opponent Analysis:** Track performance vs specific opponents
- **Streamer Mode:** Analyze Twitch streamers' games
- **Study Plans:** Pre-built training curricula
- **Chess Mentor:** AI coach that explains concepts
- **Mobile App:** Native iOS/Android
- **Browser Extension:** Analyze games directly on Chess.com
- **Opening Trainer:** Spaced-repetition for openings
- **Tactics Finder:** Extract tactical motifs from your games

---

## 📝 Design Principles

1. **Clarity over Cleverness** - Simple, obvious UI
2. **Data-Driven** - Every recommendation backed by analysis
3. **Fast Feedback** - Immediate response to user actions
4. **Progressive Disclosure** - Start simple, reveal complexity
5. **Beautiful by Default** - Design matters, even for chess nerds

---

**Document Version:** 1.0  
**Last Updated:** January 27, 2026  
**Status:** Active Development - MVP Phase
