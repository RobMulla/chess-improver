# Product Requirements Document

**Last Updated:** January 28, 2026
**Status:** Production-Ready (Core Features Complete)

## Vision

Chess Improver is a self-hosted, web-based platform designed to facilitate systematic chess improvement. It aggregates game history from external platforms (Chess.com, Lichess), analyzes gameplay using professional-grade engines, and generates targeted practice sessions based on identifiable performance gaps.

The platform prioritizes a unified user interface, ensuring all workflows—from data ingestion to advanced analysis—are accessible without command-line intervention.

---

## User Journey & Core Modules

The application architecture supports a linear flow from data acquisition to actionable improvement feedback.

### 1. Settings & Account Management
This module serves as the primary configuration hub for the application.

- **Account Aggregation**: Support for multiple account linkages across Chess.com and Lichess.
- **Configuration Persistence**: Database-backed storage for user preferences, including engine parameters (depth, threads) and UI themes.
- **Onboarding Workflow**: Automated prompts for initial account setup upon fresh installation.

### 2. Data Hub
The Data Hub provides a comprehensive visualization of user activity and system state.

- **Activity Visualization**: A calendar-based heatmap displaying game frequency and analysis coverage over the trailing 12 months.
- **Status Indicators**: Visual differentiation between imported raw data and fully analyzed games.
- **Data Ingestion Controls**: Context-aware triggers for importing new game data from linked accounts.
- **Analysis Management**: Controls for batch analysis of data ranges, with logic to prevent redundant processing.

### 3. Game Library
A high-density, tabular interface designed for efficient management of large datasets.

- **Data Grid View**: A high-density, "Excel-like" table interface.
- **Features**:
    - Sortable columns (click headers).
    - Client-side filtering per column.
    - Adjustable rows per page selector.
    - Horizontal scrolling for extended metrics.
- **Navigation**: Pagination controls at the top and bottom.

### 4. Game Analysis View
A focused interface for in-depth examination of individual games.

- **Viewport Optimization**: Single-page layout eliminating the need for vertical scrolling during review.
- **Information Architecture**: Tabbed separate of move lists and analytical data to reduce visual clutter.
- **Evaluation Visualization**: Graphical representation of game advantage swings.

### 5. Practice Mode ("Blunder Buster")
The core training engine utilizing spaced repetition and mistake re-enforcement.

- **Session Configuration**:
    - **Criteria Selection**: Filtering by color, game phase (Opening/Middlegame/Endgame), and error severity.
    - **Temporal Filters**: Scoping practice to recent games (last week/month) or specific date ranges.
    - **Volume Control**: User-defined session length (e.g., 20 positions).
- **Interaction Model (Game Environment)**:
    - **Progress Tracking**: "Boxes" visualization at the top representing each puzzle in the session (Grey=Pending, Green=Correct, Red=Incorrect).
    - **Perspective Enforcement**: Board automatically flips to player's perspective.
    - **Context**: Animation of opponent's last move upon load.
    - **Navigation**: Ability to step backward through the game history (clamped to the puzzle start).
    - **Feedback Loop**:
        - **Incorrect**: Board flashes red, allows retry (marked as failed after first attempt).
        - **Show Opponent Response**: If incorrect again, show the engine's refutation.
        - **Hint**: option to highlight the piece to move.
        - **Show Answer**: Arrow indication of the correct move.
    - **Completion**: Explicit "Next Position" action required to proceed, regardless of result.
    - **Session Timing**: Display session duration and time per puzzle.

---

## Technical Architecture

### Technology Stack
- **Frontend**: Vanilla JavaScript (ES6+) with Tailwind CSS.
- **Backend**: Python Flask framework.
- **Database**: SQLite with SQLAlchemy ORM.
- **Analysis Engine**: Stockfish (v16+) via Python integration.
- **Task Queue**: Redis and RQ for asynchronous processing.

### Data Models
- **UserConfig**: Application-wide settings and credentials.
- **Game**: Primary entity containing PGN data, analysis metrics, and move classifications.
- **Position**: Derived tactical snapshots for practice mode.
- **PracticeSession**: Telemetry data for tracking training performance over time.

---

## Engineering Standards

1.  **Testing**: Comprehensive test coverage for all core logic, including move classification and win-probability algorithms.
2.  **Code Quality**: Strict adherence to `ruff` linting and `bandit` security scanning standards.
3.  **Cross-Browser Compatibility**: Verification of key UI components (Board orientation, Data Grids) across major browser engines.
