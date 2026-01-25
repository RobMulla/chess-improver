#!/usr/bin/env python3
"""Setup script for Chess Improver."""
import os
import subprocess
import sys
from pathlib import Path


def print_header(text):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")


def check_python_version():
    """Check Python version."""
    if sys.version_info < (3, 9):
        print("❌ Python 3.9+ is required")
        sys.exit(1)
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")


def setup_virtual_environment():
    """Create virtual environment with uv."""
    print_header("Setting up virtual environment")
    
    venv_path = Path("venv")
    
    if venv_path.exists():
        print("⚠️  Virtual environment already exists")
        response = input("Recreate it? (y/N): ")
        if response.lower() != 'y':
            return
        import shutil
        shutil.rmtree(venv_path)
    
    # Check if uv is available
    try:
        subprocess.run(["uv", "--version"], capture_output=True, check=True)
        print("✅ Using uv for virtual environment")
        subprocess.run(["uv", "venv"], check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️  uv not found, using standard venv")
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
    
    print("✅ Virtual environment created")


def install_dependencies():
    """Install Python dependencies."""
    print_header("Installing dependencies")
    
    # Determine pip path
    if os.name == 'nt':  # Windows
        pip = "venv\\Scripts\\pip"
    else:
        pip = "venv/bin/pip"
    
    # Try uv first, fall back to pip
    try:
        subprocess.run(["uv", "--version"], capture_output=True, check=True)
        subprocess.run(["uv", "pip", "install", "-r", "requirements.txt"], check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        subprocess.run([pip, "install", "-r", "requirements.txt"], check=True)
    
    print("✅ Dependencies installed")


def create_env_file():
    """Create .env file from template."""
    print_header("Configuring environment")
    
    if Path(".env").exists():
        print("✅ .env file already exists")
        return
    
    # Copy template
    import shutil
    shutil.copy(".env.example", ".env")
    
    print("📝 Please configure your .env file:")
    print("   1. Set CHESS_COM_USERNAME")
    print("   2. Set LICHESS_USERNAME")
    print("   3. Set STOCKFISH_PATH (download from https://stockfishchess.org)")
    print("   4. (Optional) Set OPENAI_API_KEY for AI analysis")
    
    input("\nPress Enter when ready to continue...")


def check_stockfish():
    """Check if Stockfish is accessible."""
    print_header("Checking Stockfish")
    
    from dotenv import load_dotenv
    load_dotenv()
    
    stockfish_path = os.getenv("STOCKFISH_PATH", "/usr/local/bin/stockfish")
    
    if not Path(stockfish_path).exists():
        print(f"❌ Stockfish not found at: {stockfish_path}")
        print("\nTo install Stockfish:")
        print("1. Visit https://stockfishchess.org/download/")
        print("2. Download for your OS")
        print("3. Update STOCKFISH_PATH in .env")
        return False
    
    print(f"✅ Stockfish found at: {stockfish_path}")
    return True


def initialize_database():
    """Initialize database."""
    print_header("Initializing database")
    
    from src.database.models import init_db
    init_db()


def main():
    """Run setup."""
    print("\n♟️  Chess Improver Setup")
    print("=" * 60)
    
    check_python_version()
    setup_virtual_environment()
    install_dependencies()
    create_env_file()
    
    stockfish_ok = check_stockfish()
    
    initialize_database()
    
    print_header("Setup Complete!")
    
    print("✅ Chess Improver is ready to use!\n")
    print("Next steps:")
    print("1. Activate virtual environment:")
    if os.name == 'nt':
        print("   venv\\Scripts\\activate")
    else:
        print("   source venv/bin/activate")
    
    print("\n2. Download your games:")
    print("   python cli/sync_games.py")
    
    print("\n3. Analyze games:")
    print("   python cli/analyze_games.py")
    
    print("\n4. Generate training plan:")
    print("   python cli/generate_plan.py")
    
    print("\n5. Start web interface:")
    print("   python src/web/app.py")
    print("   Visit http://localhost:5000")
    
    if not stockfish_ok:
        print("\n⚠️  Note: Install Stockfish before analyzing games!")


if __name__ == "__main__":
    main()
