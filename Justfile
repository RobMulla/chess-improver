# Justfile for Chess Improver

# Run the full development stack (Redis + Worker + Web App)
dev:
    @echo "🚀 Starting Chess Improver Development Stack..."
    @if ! pgrep redis-server > /dev/null; then \
        echo "📦 Starting Redis..."; \
        redis-server & \
    else \
        echo "✅ Redis already running"; \
    fi
    @# Kill background jobs on exit
    @trap 'kill $(jobs -p)' EXIT; \
    source venv/bin/activate && \
    export PYTHONPATH=$PYTHONPATH:. && \
    echo "👷 Starting Worker..." && \
    rq worker & \
    echo "🌐 Starting Web App..." && \
    python -m src.web.app

# Install dependencies
install:
    pip install -r requirements.txt

# Run tests
test:
    pytest tests/ -v

# Run tests with coverage
coverage:
    pytest tests/ --cov=src --cov-report=html
    open htmlcov/index.html

# Clean up pycache
clean:
    find . -type d -name "__pycache__" -exec rm -rf {} +
    find . -type f -name "*.pyc" -delete
