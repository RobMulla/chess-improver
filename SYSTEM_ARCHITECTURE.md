# System Architecture

## Overview
Chess Improver is a locally hosted Flask application designed to analyze chess games and provide targeted training. It uses a decoupling strategy where the web server handles UI/API requests and background workers handle resource-intensive tasks (importing, analysis).

## 📂 Directory Structure

```
src/
├── analysis/           # core analysis logic
│   ├── engine.py       # Stockfish wrapper (StockfishAnalyzer)
│   └── game_analyzer.py# Orchestrates game analysis (GameAnalyzer)
├── database/           # Data layer
│   ├── models.py       # SQLAlchemy models (Game, Position, etc.)
│   └── seed_openings.py# Utility to populate opening book
├── web/                # Flask Web App
│   ├── static/         # CSS, JS, Images
│   ├── templates/      # Jinja2 HTML templates
│   └── app.py          # Main application entry point & API routes
└── workers/            # Background Tasks
    ├── analyzer_worker.py # Task runner for game analysis
    └── import_worker.py   # Task runner for fetching games
```

## 🔄 Data Architecture

### Database (SQLite)
The application uses a single SQLite database (`chess_improver.db`) managed via SQLAlchemy.

**Key Models:**
- **`Game`**: Stores raw PGN, metadata (players, result), and analysis results (accuracy, move classifications).
- **`Position`**: Represents a specific moment in a game (FEN) identified as a mistake or blunder. Used for practice.
- **`PracticeSession`**: Logs user practice runs, scores, and settings.
- **`UserConfig`**: Key-value store for settings (usernames, engine depth).

### Background Processing (Redis + RQ)
Analysis is CPU-intensive. We use Redis and RQ (Redis Queue) to offload these tasks.
1.  **Import**: `import_worker.py` fetches games from APIs and saves to DB.
2.  **Analysis**: `app.py` queues jobs; `analyzer_worker.py` picks them up, spins up Stockfish, and updates the `Game` and `Position` tables.

## 🧠 Core Analysis Engine

**`StockfishAnalyzer` (`src/analysis/engine.py`)**
- Wraps the Stockfish binary.
- Provides `analyze_position()` returning score (cp/mate) and best move.
- Handles UCI communication.

**`GameAnalyzer` (`src/analysis/game_analyzer.py`)**
- Iterates through moves of a game.
- Calculates Win% chances based on centipawn loss (Lichess-style logic).
- Classifies moves (Brilliant, Best, Good, Mistake, Blunder) based on Win% swing.
- Populates the `Position` table with puzzles generated from mistakes.

## 🎨 Frontend Architecture

**Tech Stack**: Server-Side Rendered (SSR) HTML via Jinja2 + Vanilla JavaScript + Tailwind CSS.

**Key Pages:**
- **Dashboard (`dashboard.html`)**: High-level stats.
- **Game Viewer (`game_viewer.html`)**:
    - Uses `chessboard.js` for the board.
    - `chess.js` for move validation and logic.
    - Tabbed Sidebar for Moves vs. Analysis.
- **Practice Mode (`practice.html`)**:
    - AJAX-heavy page for interactive training.
    - Client-side logic handles move validation against the stored solution.
    - **Board Orientation**: Explicitly handled to ensure user perspective (flipped for Black).

## 🚀 Execution Flow

1.  **User Visits Site**: Flask serves `dashboard.html`.
2.  **Import Trigger**: User requests sync -> API enqueues job -> Worker fetches PGNs -> DB updated.
3.  **Analysis Trigger**: User clicks "Analyze" -> API enqueues job -> Worker runs Stockfish -> DB updated with accuracy/mistakes.
4.  **Practice**: User starts session -> API queries loose `Position` records -> Frontend guides user through puzzles.

## 🛠️ Development Setup

- **Language**: Python 3.11+
- **Dependency Manager**: `uv` or `pip`.
- **Database**: SQLite (auto-created).
- **Redis**: Must be running for background tasks.
- **Env Vars**: `FLASK_APP=src/web/app.py`, `FLASK_DEBUG=1`.

---

## 🛡️ Engineering Standards

We adhere to strict quality controls to ensure robustness and maintainability.

### Code Quality & Formatting
*Tools used via `ruff` and `pre-commit`*

- **Linter**: `ruff` (configured in `pyproject.toml`) handles Python linting (replacing flake8/isort).
- **Formatter**: `ruff-format` ensures consistent style (replacing Black).
- **Security**: `bandit` scans for common security vulnerabilities (e.g., hardcoded passwords, unsafe exec).

### Pre-commit Hooks
The repo uses pre-commit hooks to enforce standards before code enters the repo.
**Config**: `.pre-commit-config.yaml`
**Hooks Run:**
1.  **Trailing Whitespace / End of File**: Basic cleanup.
2.  **Large File Check**: Prevents committing binaries > 1MB.
3.  **Ruff**: Lints and formats code.
4.  **Bandit**: Security audit.
5.  **Pytest Coverage**: **(Push Only)** prevents pushing code if coverage drops below 40%.

### 🧪 Testing Strategy

Tests are located in `tests/` and run via `pytest`.

**Key Test Suites:**
- **`tests/test_integration.py`**: End-to-end flows (sync -> analyze -> result).
- **`tests/test_practice_mode.py`**: Verifies puzzle generation and board orientation logic.
- **`tests/test_win_chance.py`**: Core algorithm verification for move classification.
- **`tests/test_golden_chesscom.py`**: Verification against "golden" reference games to ensure analytical accuracy.

**Run Tests:**
```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=src

# Watch mode (recommended during dev)
ptw
```

## 👩‍💻 Developer Onboarding

### 1. Environment Setup
```bash
# 1. Clone & Enter
git clone <repo_url>
cd chess-improver

# 2. Create Virtual Env (Recommended with uv or python)
python -m venv venv
source venv/bin/activate

# 3. Install Dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 4. Install Pre-commit Hooks
pre-commit install
```

### 2. Running the App
The app requires Redis for background workers.

```bash
# Terminal 1: Redis
redis-server

# Terminal 2: Worker (Process Analysis)
export PYTHONPATH=$PYTHONPATH:$(pwd)
python src/workers/analyzer_worker.py

# Terminal 3: Web Server
export FLASK_APP=src/web/app.py
export FLASK_DEBUG=1
flask run --port 5001
```

### 3. Making Changes
1.  Create a branch for your feature.
2.  Write tests in `tests/` confirming the desired behavior.
3.  Implement changes.
4.  Run `pytest` to ensure no regressions.
5.  Commit (Pre-commit hooks will auto-fix formatting).
