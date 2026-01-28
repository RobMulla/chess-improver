# Chess Improver - Product Requirements Document

**Last Updated:** January 27, 2026
**Status:** Core v1.0 COMPLETE ✅

## 🎯 Vision

**Chess Improver** is a web-based chess training platform that analyzes your games from Chess.com and Lichess, identifies your mistakes, and helps you improve through targeted practice and data-driven insights.

**Mission:** Make chess improvement accessible, personalized, and data-driven by focusing on re-learning from your actual mistakes.

---

## 👥 Target Users

**Primary:** Amateur chess players (800-2000 ELO) who:
- Play regularly on Chess.com or Lichess
- Want to improve systematically by reviewing their own blunders
- Prefer a clean, UI-driven experience over CLI tools
- Have 10-30 minutes daily for targeted practice

---

## 🎨 Core User Experience

### User Journey
1. **Configure** site settings with Chess.com/Lichess usernames and analysis preferences.
2. **Import** games seamlessly via the Web UI (background sync).
3. **Analyze** games with professional-grade Stockfish evaluation and Win% accuracy metrics.
4. **Practice** specific mistakes in the **"Blunder Buster"** interactive trainer.
5. **Track** progress through session history and aggregate accuracy stats.

### Key Differentiators
- **UI-First Experience**: No CLI required; all operations (sync, analyze, practice) are in the browser.
- **Blunder-Focused Training**: Practice only the moves you actually missed in your own games.
- **Persistent Progress**: Every practice attempt and session is stored for long-term tracking.
- **Professional Analytics**: Win% based move classification on par with Lichess/Chess.com standards.

---

## 🏗️ Product Architecture

### Technology Stack
**Frontend:**
- Clean, modern UI using **Tailwind CSS** and **Inter** typography.
- **Vanilla JavaScript** (no heavy frameworks) for fast, responsive interactions.
- Interactive chessboard using **chess.js** and **chessboard.js**.

**Backend:** ✅ COMPLETE
- **Python Flask** for the web server and API.
- **Stockfish** engine for local high-depth analysis.
- **Redis + RQ** for asynchronous game syncing and analysis.
- **SQLAlchemy + SQLite** for persistent storage of games, moves, sessions, and configs.

**Testing:** ✅ 100% Core Pass Rate
- Comprehensive test suite for Win% logic, Move Classification, and Practice Mode.
- Isolated in-memory database testing for API endpoints.

---

## ✨ Feature Specifications

### 1. Unified Dashboard
- **Overview Stats**: Total games, analyzed games, and analysis progress.
- **Top Openings**: Performance breakdown (wins/draws/losses) of your most-played openings.
- **Quick Navigation**: One-click access to Sync, Practice, and Settings.

### 2. Games Library & Viewer
- **Filtered Browser**: Filter games by date, platform, result, and opening.
- **Deep Analysis**: Step through games with move-by-move evaluation and classification (Best, Excellent, Mistake, Blunder).
- **Game Phase Detection**: Smart classification of moves into Opening, Middlegame, and Endgame.

### 3. "Blunder Buster" Practice Mode
- **Smart Filtering**: Launch sessions based on specific criteria:
  - playing as White/Black
  - Mistake vs. Blunder focus
  - specific game phases (Endgames only, etc.)
  - specific date ranges
- **Interactive Gameplay**: Replay the position and find the engine's best move.
- **Immediate Feedback**: Correct/Incorrect validation with the option to "Show Solution."
- **Session History**: Review past training runs, accuracy percentages, and aggregate improvement stats.

### 4. Settings & Data Management
- **Persistent Identity**: Store multiple usernames for Chess.com and Lichess.
- **Sync Control**: Trigger background updates and track import progress directly from the UI.

---

## 🧪 Testing Requirements

**MANDATORY Standards:**
1. **TDD Flow**: Every feature improvement (like Blunder Buster) must include corresponding `pytest` cases.
2. **Pre-commit Compliance**: Code must pass `ruff` formatting, linting, and security audits (`bandit`).
3. **Regression Safety**: Coverage must be maintained on all core analysis and practice logic.

---

## 🐛 Resolved Issues (Phase 2 & 3)
- ✅ **Move Classification**: Fixed 100% accuracy bug; now uses Win% loss distribution.
- ✅ **Opening Detection**: Standardized naming and unified opening labels across the DB.
- ✅ **UI Cleanup**: Removed legacy "Daily Plan" and "Insights" modules in favor of the focused "Blunder Buster" vision.
- ✅ **Session Isolation**: Fixed integration test failures related to database state leakage.

---

## � Roadmap

### Phase 4: Refined Practice (Next)
- [ ] **Openings Practice**: Set "ideal" opening branches and practice your preparation.
- [ ] **SRS Integration**: Implement Spaced Repetition (SRS) to show recurring mistakes more frequently.
- [ ] **Advanced Stats**: Heatmaps of common mistake squares and time management analysis.

### Phase 5: Scale & Social
- [ ] AI-powered position explanations (LLM integration).
- [ ] Mobile-responsive design optimization.
- [ ] User accounts (OAuth integration).

---

**Version:** 1.0 (Post-Phase 3)
**Author:** Antigravity AI
**Status:** Main implementation complete; shifted to refinement and new training modules.
