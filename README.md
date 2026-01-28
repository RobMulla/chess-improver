# Chess Improver

**A self-hosted, analytical platform for systematic chess improvement.**

Chess Improver aggregates game history from external platforms, processes it through professional-grade analysis engines, and generates targeted, spaced-repetition practice sessions to address specific performance gaps.



## Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <repo-url>
cd chess-improver

# Initialize environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Infrastructure Setup

Ensure Redis and Stockfish are installed and available in your path.

```bash
# MacOS
brew install stockfish redis

# Linux (Debian/Ubuntu)
sudo apt-get install stockfish redis-server
```

### 3. Execution

Launch the required services:

```bash
# Start the Message Broker
redis-server &

# Start the Web Application
python -m src.web.app
```

Access the dashboard at `http://localhost:5555`.

## Documentation

- **[Product Requirements (PRD)](PRD.md)**: Detailed feature specifications and product vision.
- **[System Architecture](SYSTEM_ARCHITECTURE.md)**: Engineering design, data models, and component overview.

## Testing

The project maintains a comprehensive test suite. Validation can be executed via `pytest`.

```bash
# Execute test suite
pytest tests/ -v
```

## Technology Stack

- **Backend Framework**: Python Flask
- **Analysis Engine**: Stockfish
- **Data Persistence**: SQLite (Application Data), Redis (Task Queue)
- **Frontend**: Vanilla JavaScript, Tailwind CSS

## Feature Matrix

| Feature | Description | Support Level |
| :--- | :--- | :--- |
| **Multi-Platform Import** | Aggregation of history from Chess.com and Lichess. | Full Support |
| **Engine Analysis** | Server-side analysis using Stockfish 16+. | Full Support |
| **Move Classification** | Algorithmic detection of Brilliances, Mistakes, and Blunders. | Full Support |
| **Practice Mode** | Interactive replay of tactical errors from your own games. | Full Support |
| **Data Visualization** | Heatmaps and trend analysis for long-term improvement tracking. | Partial |
| **Bulk Processing** | Asynchronous queuing for heavy analysis workloads. | Full Support |

## License

Licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE) for more information.
