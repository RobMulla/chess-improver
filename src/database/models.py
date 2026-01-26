"""Database models for chess improvement system."""
from datetime import datetime
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Float,
    Boolean,
    DateTime,
    Text,
    ForeignKey,
    JSON,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

Base = declarative_base()


class Game(Base):
    """Chess game record."""

    __tablename__ = "games"

    id = Column(Integer, primary_key=True)
    platform = Column(String(20), nullable=False)  # 'chess.com' or 'lichess'
    game_id = Column(String(100), unique=True, nullable=False)
    pgn = Column(Text, nullable=False)
    date = Column(DateTime, nullable=False)
    time_control = Column(String(50))
    result = Column(String(10))  # '1-0', '0-1', '1/2-1/2'
    player_color = Column(String(5))  # 'white' or 'black'
    player_rating = Column(Integer)
    opponent_rating = Column(Integer)
    opponent_name = Column(String(100))
    opening_name = Column(String(200))
    opening_eco = Column(String)
    
    # Analysis flags
    analyzed = Column(Boolean, default=False)
    starred = Column(Boolean, default=False)  # Allow users to favorite games
    analysis_date = Column(DateTime)
    
    # Game statistics
    total_moves = Column(Integer)
    player_accuracy = Column(Float)
    opening_accuracy = Column(Float)
    middlegame_accuracy = Column(Float)
    endgame_accuracy = Column(Float)
    
    # Book analysis
    book_moves = Column(Integer)
    player_out_of_book_move = Column(Integer)  # Move number when player left book
    opponent_out_of_book_move = Column(Integer)
    first_mistake_move = Column(Integer)
    
    # Move classification counts
    brilliant_moves = Column(Integer, default=0)
    great_moves = Column(Integer, default=0)
    best_moves = Column(Integer, default=0)
    excellent_moves = Column(Integer, default=0)
    good_moves = Column(Integer, default=0)
    inaccuracy_moves = Column(Integer, default=0)
    mistake_moves = Column(Integer, default=0)
    miss_moves = Column(Integer, default=0)
    blunder_moves = Column(Integer, default=0)
    
    # Relationships
    positions = relationship("Position", back_populates="game", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Game {self.platform}:{self.game_id} {self.date}>"


class Position(Base):
    """Individual position from a game."""

    __tablename__ = "positions"

    id = Column(Integer, primary_key=True)
    game_id = Column(Integer, ForeignKey("games.id"), nullable=False)
    move_number = Column(Integer, nullable=False)
    fen = Column(String(100), nullable=False)
    
    # Engine analysis
    evaluation = Column(Float)  # In centipawns (white perspective)
    best_move = Column(String(10))
    player_move = Column(String(10))
    
    # Mistake classification
    is_mistake = Column(Boolean, default=False)
    is_blunder = Column(Boolean, default=False)
    eval_drop = Column(Float)  # Centipawn loss
    move_classification = Column(String(20))  # brilliant, great, best, excellent, good, book, inaccuracy, mistake, miss, blunder
    game_phase = Column(String(20))  # opening, middlegame, endgame
    
    # Relationship
    game = relationship("Game", back_populates="positions")

    def __repr__(self):
        return f"<Position game={self.game_id} move={self.move_number}>"


class Opening(Base):
    """Opening statistics."""

    __tablename__ = "openings"

    id = Column(Integer, primary_key=True)
    name = Column(String(200), unique=True, nullable=False)
    eco_code = Column(String(10))
    
    # Statistics
    games_played = Column(Integer, default=0)
    wins = Column(Integer, default=0)
    draws = Column(Integer, default=0)
    losses = Column(Integer, default=0)
    avg_accuracy = Column(Float)
    
    # Learning resources
    youtube_links = Column(JSON)  # List of video URLs
    study_links = Column(JSON)  # List of study URLs

    @property
    def win_rate(self):
        if self.games_played == 0:
            return 0
        return (self.wins + 0.5 * self.draws) / self.games_played

    def __repr__(self):
        return f"<Opening {self.eco_code} {self.name}>"


class DailyPlan(Base):
    """Daily training plan."""

    __tablename__ = "daily_plans"

    id = Column(Integer, primary_key=True)
    date = Column(DateTime, unique=True, nullable=False)
    tasks = Column(JSON, nullable=False)  # List of task objects
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<DailyPlan {self.date.date()}>"


class Insight(Base):
    """Generated insights and analytics."""

    __tablename__ = "insights"

    id = Column(Integer, primary_key=True)
    metric_name = Column(String(100), nullable=False)
    metric_value = Column(Float)
    metric_data = Column(JSON)  # For complex data
    time_period = Column(String(50))  # 'last_week', 'last_month', 'all_time'
    category = Column(String(50))  # 'accuracy', 'openings', 'time_control', etc.
    generated_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Insight {self.metric_name} ({self.time_period})>"


class GameReview(Base):
    """AI-generated game reviews."""

    __tablename__ = "game_reviews"

    id = Column(Integer, primary_key=True)
    game_id = Column(Integer, ForeignKey("games.id"), nullable=False, unique=True)
    review_text = Column(Text, nullable=False)
    key_mistakes = Column(JSON)  # List of critical mistakes
    improvements = Column(JSON)  # List of improvement suggestions
    generated_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<GameReview for game {self.game_id}>"


# Database setup functions
def get_engine():
    """Get database engine."""
    db_url = os.getenv("DATABASE_URL", "sqlite:///chess_improver.db")
    return create_engine(db_url, echo=False)


def get_session():
    """Get database session."""
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    return Session()


def init_db():
    """Initialize database tables."""
    engine = get_engine()
    Base.metadata.create_all(engine)
    print("✅ Database initialized successfully")


if __name__ == "__main__":
    init_db()
