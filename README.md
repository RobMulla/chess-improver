# Chess Improver

A comprehensive chess improvement system that downloads your games from chess.com and Lichess, analyzes them with Stockfish, uses AI for deep insights, and creates personalized daily training plans.

## Features

Automatic game download from chess.com and Lichess. Engine analysis using Stockfish to identify mistakes and calculate accuracy. AI-powered insights for deep game reviews and pattern recognition. Custom insights dashboard that recreates chess.com insights with more flexibility. Daily training plans personalized to your weaknesses. Opening repertoire analysis to track performance. Learning resources including curated YouTube videos and study materials. Progress tracking with task completion and data export.

## Quick Start

### Prerequisites

Python 3.9 or higher installed. Stockfish Chess Engine downloaded from stockfishchess.org. Active account on chess.com and/or Lichess.

### Installation

Clone the repository and navigate to the project directory. Create a virtual environment using uv or venv. Activate the virtual environment. Install dependencies from requirements.txt. Copy .env.example to .env and configure with your credentials.

```bash
# Create virtual environment
uv venv
source venv/bin/activate

# Install dependencies
uv pip install -r requirements.txt

# Configure environment
cp .env.example .env
```

### Configuration

Edit the .env file with your information:

```bash
CHESS_COM_USERNAME=your_username
LICHESS_USERNAME=your_username
STOCKFISH_PATH=/path/to/stockfish
OPENAI_API_KEY=sk-...
```

### Usage

Download your games using the sync command. Analyze games with Stockfish. Generate today's training plan. Start the web interface and visit localhost:5000.

```bash
python cli/sync_games.py
python cli/analyze_games.py
python cli/generate_plan.py
python src/web/app.py
```

## Project Structure

The source code is organized into collectors for downloading games, database models for storage, analysis modules for Stockfish integration, AI modules for insights, training modules for plan generation, resources for learning materials, and web interface for the dashboard. Command-line tools are in the cli directory. Downloaded games and the database are stored in the data directory.

## How It Works

The system downloads all your games via public APIs. Stockfish analyzes each position to find mistakes and calculate accuracy. AI identifies recurring patterns and weaknesses across games. Custom insights are generated showing accuracy trends and opening statistics. Daily tasks are generated based on your specific needs. Progress tracking shows completion rates and improvement over time.

## Privacy

All data is stored locally on your machine. The only external API calls are to chess.com and Lichess to download your public games, OpenAI if using AI analysis (optional), and YouTube if searching for videos (optional).

## License

Apache 2.0 - See LICENSE file

## Roadmap

Integration with chess.com Game Review API. Local LLM support using Ollama. Mobile app for daily plans. Spaced repetition for opening training. Tournament preparation mode. Opening tree visualization.
