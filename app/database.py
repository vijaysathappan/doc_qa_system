from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from dotenv import load_dotenv
import os
load_dotenv()
# engine = connection to db
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./docqa.db")

# Convert legacy postgres:// to postgresql:// for SQLAlchemy compatibility
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# SQLite needs check_same_thread=False; PostgreSQL does not
if DATABASE_URL.startswith("sqlite"):
    # Ensure directory is writeable, otherwise fall back to temp directory (for serverless environments)
    db_file_path = DATABASE_URL.replace("sqlite:///", "")
    db_dir = os.path.dirname(db_file_path) or "."
    if not os.access(db_dir, os.W_OK):
        import tempfile
        DATABASE_URL = f"sqlite:///{os.path.join(tempfile.gettempdir(), 'docqa.db')}"

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

def get_table_columns(db, table_name):
    """Retrieve column names for a table in a database-agnostic way."""
    if DATABASE_URL and DATABASE_URL.startswith("sqlite"):
        result = db.execute(text(f"PRAGMA table_info({table_name})"))
        return [row[1] for row in result.fetchall()]
    else:
        result = db.execute(text(
            f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table_name}'"
        ))
        return [row[0] for row in result.fetchall()]

def add_columns_if_missing():
    db = SessionLocal()
    try:
        columns = get_table_columns(db, "users")
        if "total_tokens_consumed" not in columns:
            db.execute(text("ALTER TABLE users ADD COLUMN total_tokens_consumed INTEGER DEFAULT 0"))
            db.commit()
            print("Successfully added total_tokens_consumed column to users table.")
    except Exception as e:
        print(f"Error checking/adding total_tokens_consumed column: {e}")

    try:
        columns = get_table_columns(db, "document_chunks")
        if "embedding" not in columns:
            if DATABASE_URL and DATABASE_URL.startswith("sqlite"):
                db.execute(text("ALTER TABLE document_chunks ADD COLUMN embedding TEXT"))
            else:
                db.execute(text("ALTER TABLE document_chunks ADD COLUMN embedding JSON"))
            db.commit()
            print("Successfully added embedding column to document_chunks table.")
    except Exception as e:
        print(f"Error checking/adding embedding column: {e}")
    finally:
        db.close()