import os
from sqlalchemy import create_engine, Column, String, Integer
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///local_players.db")

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class PlayerModel(Base):
    __tablename__ = "players"

    username = Column(String(50), primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    password_hash = Column(String(256), nullable=False)
    solved_count = Column(Integer, default=0)
    total_score = Column(Integer, default=0)
    current_level = Column(String(50), default="Junior Investigator")

def init_db():
    Base.metadata.create_all(bind=engine)