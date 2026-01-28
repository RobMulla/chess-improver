# Chess Improver - Product Requirements Document

**Last Updated:** January 28, 2026
**Status:** Phase 4 Planning (Refinement & UI Overhaul)

## 🎯 Vision

**Chess Improver** is a self-hosted, UI-first web application for serious chess improvement. It empowers users to aggregate their game history from multiple platforms (Chess.com, Lichess), analyze it with professional-grade engines, and systematically eliminate mistakes through targeted, interactive practice.

**Core Philosophy:** "Everything in the UI." No command-line tools required for daily operation.

---

## 🗺️ User Journey & Core Modules

The application flow is designed to guide the user from data ingestion to actionable improvement.

### 1. ⚙️ Settings & Onboarding
*The entry point for new users.*
- **Account Management**: Persistent storage of multiple Chess.com and Lichess usernames.
- **Onboarding Nudge**: If no accounts are configured, a banner prompts the user to set them up immediately.
- **Config Persistence**: All settings (engine depth, threads, themes) are saved to the database.

### 2. 📊 Data Overview (The "Hub")
*A clear, visual summary of the user's data state.*
- **Activity Heatmap**: A "GitHub-style" contribution graph showing games played per day over the last year.
    - **Color Coding**: Differentiate between *missing*, *imported*, and *analyzed* days.
    - **Interactivity**: Clicking a date allows for immediate import/analysis of that range.
- **Sync Status**: clear distinction between "Imported" and "Analyzed" games.
- **Actionable Imports**: "Import New Games" buttons located directly next to linked accounts.
- **Smart Analysis**: Ability to select specific ranges for analysis, with warnings if re-analyzing existing data.

### 3. 📑 Games Overview
*A powerful, spreadsheet-like interface for managing the game library.*
- **Excel-like Experience**: High-density table view that fills the viewport.
    - **Fixed Headers**: Sort and filter columns (Date, Opening, Result, Accuracy) without losing context.
    - **Infinite Scroll/Pagination**: Handle thousands of games smoothly.
- **Keyboard Navigation**: Move through rows with arrow keys.
- **Customizable**: User can select how many rows to view per page.

### 4. ♟️ Single Game Viewer
*Distraction-free deep dive into a single game.*
- **Single-Page Feel**: No scrolling required. The board, move list, and analysis pane fit perfectly within the viewport.
- **Tabbed Sidebar**: "Moves" and "Analysis" are separated to keep the interface clean.
- **Independent Scrolling**: Move list scrolls independently of the board/layout.
- **Evaluation Bar**: Visual representation of the game's swing.

### 5. 💥 "Blunder Buster" (Practice Mode)
*The core training loop. Re-play your mistakes to learn.*
- **Session Setup**:
    - **Selectors**: Choose criteria: Color (White/Black), Phase (Opening/Mid/End), Severity (Blunder/Mistake).
    - **Filters**: Recent games (last week/month) or specific dates.
    - **Goal**: Set number of positions to solve (e.g., 20 moves).
- **The Gameplay Loop**:
    - **Progress Bar**: A row of boxes (Green=Correct, Red=Failed, Grey=Pending) showing session status at a glance.
    - **Orientation**: Board **MUST** always flip to the player's perspective.
    - **Context**: Animate the opponent's last move before passing control.
    - **Retry Logic**:
        - **Incorrect**: Board flashes red. Show the opponent's refutation (best engine response). User must retry until correct (but marked as "Failed").
        - **Correct**: Board flashes green.
        - **Hint**: Show piece to move (marks as failed).
        - **Show Answer**: Draw arrow on board (marks as failed).
    - **Forced Progression**: User explicitly clicks "Next Position" to review the board state before moving on.
- **Session Summary**: After completion, show stats, accuracy, and time spent.

---

## 🏗️ Technical Architecture

### Tech Stack
- **Frontend**: Vanilla JS (ES6+) + Tailwind CSS. *Exploring lightweight frameworks (Alpine.js / Preact) for complex data tables if needed.*
- **Backend**: Python Flask.
- **Database**: SQLite + SQLAlchemy (Data consistency is paramount).
- **Engine**: Stockfish 16+ via Python wrapper.
- **Async Processing**: Redis + RQ for handling long-running analysis jobs without blocking the UI.

### Data Models (Refined)
- **UserConfig**: Stores accounts and preferences.
- **Game**: The central entity. Stores PGN, analysis status, and move-level accuracy metrics.
- **Position**: Individual fen/move snapshots for practice.
- **PracticeSession**: Logs of training runs (score, time, settings) to track improvement over time.

---

## 🧪 Engineering Standards
1.  **Test-Driven**: Logic for move classification, win% extraction, and practice positioning must be tested.
2.  **Linting**: Strict `ruff` and `bandit` compliance.
3.  **UI Verification**: Ensure board orientation and "Excel-like" behavior works across browsers.
