from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from dotenv import load_dotenv
import os
load_dotenv()
# engine = connection to db
DATABASE_URL = os.getenv("DATABASE_URL")

# SQLite needs check_same_thread=False; PostgreSQL does not
if DATABASE_URL and DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}  # required for SQLite + FastAPI
    )
else:
    engine = create_engine(DATABASE_URL)

# session = conversation with db
SessionLocal = sessionmaker(bind=engine)

# base = parent for all your db models
class Base(DeclarativeBase):
    pass

# Dependency — FastAPI will call this to get a DB session per request
def get_db():
    db = SessionLocal()
    try:
        yield db       # give the session to the route
    finally:
        db.close()     # always close after request is done

from sqlalchemy import text
def add_columns_if_missing():
    db = SessionLocal()
    try:
        result = db.execute(text("PRAGMA table_info(users)"))
        columns = [row[1] for row in result.fetchall()]
        if "total_tokens_consumed" not in columns:
            db.execute(text("ALTER TABLE users ADD COLUMN total_tokens_consumed INTEGER DEFAULT 0"))
            db.commit()
            print("Successfully added total_tokens_consumed column to users table.")
    except Exception as e:
        print(f"Error checking/adding column: {e}")
    finally:
        db.close()