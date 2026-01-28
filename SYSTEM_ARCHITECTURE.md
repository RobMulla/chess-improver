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
