# System Architecture

## Overview
Chess Improver is a locally hosted application designed for chess analysis and training. It employs a decoupled architecture where a Flask-based web server manages user interaction, while background workers handle resource-intensive asynchronous tasks such as data ingestion and engine analysis.

## Directory Structure

```
src/
├── analysis/           # Core analysis logic
│   ├── engine.py       # Stockfish wrapper (StockfishAnalyzer)
│   └── game_analyzer.py# Game analysis orchestration (GameAnalyzer)
├── database/           # Data persistence layer
│   ├── models.py       # SQLAlchemy models (Game, Position, etc.)
│   └── seed_openings.py# Utility for population of opening book data
├── web/                # Presentation layer
│   ├── static/         # Usage assets (CSS, JS, Images)
│   ├── templates/      # Jinja2 HTML templates
│   └── app.py          # Application entry point and API definition
└── workers/            # Asynchronous Task Runners
    ├── analyzer_worker.py # Task runner for game analysis
    └── import_worker.py   # Task runner for data ingestion
```

## Data Architecture

### Database
The application utilizes a single SQLite database (`chess_improver.db`) managed via the SQLAlchemy ORM.

**Core Entities:**
- **`Game`**: Stores raw PGN data, player metadata, and analysis results (accuracy metrics, move classifications).
- **`Position`**: Represents specific game states identified as tactical opportunities or errors. These form the basis of the training module.
- **`PracticeSession`**: Records telemetry from user training sessions to track improvement over time.
- **`UserConfig`**: Key-value storage for application configuration and user preferences.

### Async Processing
To ensure interface responsiveness, CPU-intensive operations are offloaded using Redis and RQ (Redis Queue).
1.  **Ingestion**: `import_worker.py` interfaces with external APIs to retrieve game data.
2.  **Analysis**: `analyzer_worker.py` executes the Stockfish engine to process games and update the database with analytical insights.

## Analysis Engine

**`StockfishAnalyzer` (`src/analysis/engine.py`)**
- Encapsulates the Stockfish binary interaction.
- Provides a standardized interface for position evaluation (centipawn/mate scores) and best-move determination.
- Manages UCI (Universal Chess Interface) communication protocols.

**`GameAnalyzer` (`src/analysis/game_analyzer.py`)**
- Orchestrates the sequential analysis of game moves.
- Calculates Win Probability using centipawn loss logic similar to platforms like Lichess.
- Classifies moves (e.g., Brilliant, Mistake, Blunder) based on significant shifts in win probability.
- Generates `Position` records for detected errors to populate the training database.

## Frontend Architecture

**Technology Stack**: Server-Side Rendered (SSR) HTML via Jinja2, utilizing Vanilla JavaScript and Tailwind CSS for client-side interactivity and styling.

**Key Interfaces:**
- **Dashboard**: High-level statistical reconfiguration and status monitoring.
- **Game Viewer**:
    - Integrates `chessboard.js` for board visualization.
    - Utilizes `chess.js` for client-side move validation.
    - Implements a tabbed interface for move history and analytical data.
- **Practice Mode**:
    - Interactive training interface dependent on AJAX for state management.
    - Client-side validation compares user input against stored engine solutions.
    - Enforces correct board orientation based on the user's playing color.

## Development Setup

- **Language**: Python 3.11+
- **Dependency Management**: `uv` or `pip`
- **Database**: SQLite (auto-provisioned)
- **Message Broker**: Redis
- **Environment**: `FLASK_APP=src/web/app.py`, `FLASK_DEBUG=1`

---

## Engineering Standards

The project maintains strict quality controls to ensure codebase robustness and maintainability.

### Code Quality & Formatting
*Enforced via `ruff` and `pre-commit`*

- **Linting**: `ruff` handles Python linting.
- **Formatting**: `ruff-format` ensures consistent code style.
- **Security**: `bandit` performs static analysis for common security vulnerabilities.

### Pre-commit Hooks
The repository employs pre-commit hooks to validate code integrity prior to ingestion.
**Configuration**: `.pre-commit-config.yaml`
**Active Checks:**
1.  **File Integrity**: Trailing whitespace and end-of-file validation.
2.  **Size Constraints**: Prevention of large binary commits (>1MB).
3.  **Static Analysis**: Execution of Ruff linting and formatting.
4.  **HTML Linting**: djLint validation (auto-formatting disabled to preserve Jinja2 syntax).
5.  **Template Syntax**: Jinja2 template validation to catch syntax errors before commit.
6.  **Security Audit**: Execution of Bandit security checks.
7.  **Test Coverage**: (Push Only) Verifies test coverage meets minimum thresholds.

### Testing Strategy

Tests are maintained in the `tests/` directory and executed via `pytest`.

**Key Suites:**
- **`tests/test_integration.py`**: End-to-end workflow validation (Sync -> Analyze -> Result).
- **`tests/test_practice_mode.py`**: Verification of puzzle generation and orientation logic.
- **`tests/test_move_classifier.py`**: Validation of core move classification algorithms.
- **`tests/test_templates.py`**: Jinja2 template syntax validation across all HTML files.
- **`tests/test_golden_chesscom.py`**: Benchmarking against reference datasets to ensure analytical accuracy.

**Execution:**
```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=src
```

## Developer Onboarding

### 1. Environment Setup
```bash
# 1. Clone Repository
git clone <repo_url>
cd chess-improver

# 2. Create Virtual Environment
python -m venv venv
source venv/bin/activate

# 3. Install Dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 4. Install Pre-commit Hooks
pre-commit install
```

### 2. Application Execution
The application requires Redis for background task processing.

```bash
# Terminal 1: Message Broker
redis-server

# Terminal 2: Analysis Worker
export PYTHONPATH=$PYTHONPATH:$(pwd)
python src/workers/analyzer_worker.py

# Terminal 3: Web Server
export FLASK_APP=src/web/app.py
export FLASK_DEBUG=1
flask run --port 5001
```
