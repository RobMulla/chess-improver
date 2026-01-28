# Product Requirements Document

**Last Updated:** January 28, 2026
**Status:** Implementation Phase 4

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

- **Data Grid View**: A sortable, filterable table display maximizing information density.
- **Navigation**: Keyboard-centric navigation support for rapid browsing.
- **Performance**: Optimized rendering for datasets exceeding thousands of records.
- **Customization**: User-configurable pagination and row density settings.

### 4. Game Analysis View
A focused interface for in-depth examination of individual games.

- **Viewport Optimization**: Single-page layout eliminating the need for vertical scrolling during review.
- **Information Architecture**: Tabbed separate of move lists and analytical data to reduce visual clutter.
- **Evaluation Visualization**: Graphical representation of game advantage swings.

### 5. Practice Mode ("Blunder Buster")
The core training engine utilizing spaced repetition and mistake re-enforcement.

- **Session Configuration**:
    - **Criteria Selection**: Filtering by color, game phase (Opening/Middlegame/Endgame), and error severity.
    - **Temporal Filters**: Scoping practice to recent games or specific date ranges.
    - **Volume Control**: User-defined session length (e.g., 20 positions).
- **Interaction Model**:
    - **Perspective Enforcement**: Board orientation automatically aligns to the user's playing color.
    - **Contextual Animation**: Replay of the opponent's final move prior to the tactical position.
    - **Feedback Loop**: Visual indicators for correct/incorrect solutions with enforced retry logic.
- **Progression**: Manual advancement controls to ensure user reflection on solved positions.

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
