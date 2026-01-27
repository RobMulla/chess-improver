# Chess Improver 🚀

**AI-powered chess training platform** that analyzes your games, identifies mistakes, and helps you improve through targeted practice.

[![Tests](https://img.shields.io/badge/tests-70%20passing-success)]() [![Coverage](https://img.shields.io/badge/coverage-40%25-yellow)]() [![Python](https://img.shields.io/badge/python-3.14-blue)]()

## 🎯 Features

- **Automatic Game Import** from Chess.com and Lichess
- **Stockfish Analysis** with Win% algorithm (Lichess method)
- **Smart Move Classification** (Best → Blunder based on Win% loss)
- **Interactive Practice Mode** for your actual mistakes
- **Performance Insights** and trends
- **Background Analysis** with Redis job queue

## 🚀 Quick Start

```bash
# 1. Clone and setup
git clone <repo-url>
cd chess-improver
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Install Stockfish
brew install stockfish  # Mac
# or download from https://stockfishchess.org/

# 4. Start Redis (for background jobs)
redis-server &

# 5. Run the web app
python -m src.web.app

# 6. Open browser
open http://localhost:5555
```

## 📚 Documentation

- **[PRD.md](PRD.md)** - Product requirements and architecture
- **[docs/WEB_UI_PLAN.md](docs/WEB_UI_PLAN.md)** - Web UI implementation roadmap
- **[docs/CLEANUP_AUDIT.md](docs/CLEANUP_AUDIT.md)** - Code coverage analysis

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# View coverage report
open htmlcov/index.html
```

## 📊 Current Status

**Backend:** ✅ Complete
- Game import, analysis, caching, background jobs

**Web UI:** ⚠️ 70% Complete
- Dashboard, games list, game viewer, practice mode
- Missing: Import UI, bulk analysis, opening detection

**Test Coverage:** 40%
- Core algorithms: 96-98%
- Need: Web app tests, worker tests

## 🛠️ Tech Stack

- **Backend:** Python, Flask, Stockfish, Redis, SQLite
- **Frontend:** HTML/CSS/JavaScript (vanilla)
- **Testing:** pytest, pre-commit hooks (Ruff)
- **Deployment:** Local dev (Docker coming soon)

## 🎓 How It Works

1. **Import** your games from Chess.com/Lichess
2. **Analyze** with Stockfish (background jobs)
3. **Classify** moves using Win% algorithm
4. **Practice** your mistakes interactively
5. **Improve** based on data-driven insights!

## 📈 Roadmap

See [docs/WEB_UI_PLAN.md](docs/WEB_UI_PLAN.md) for detailed roadmap.

**Phase 1 (Week 1):** Browser-only workflow (import, analyze, export via UI)
**Phase 2 (Week 2):** Opening detection + insights visualization
**Phase 3 (Week 3):** Practice enhancements + gamification

## 🤝 Contributing

1. Tests must pass: `pytest tests/`
2. Coverage must not drop below 40%
3. Pre-commit hooks will auto-format code (Ruff)

## 📝 License

MIT

---

**Built with ❤️ for chess improvement**
