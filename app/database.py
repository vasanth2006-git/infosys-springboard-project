import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("shopsense.db")

# Default MySQL connection string (Can be overridden via MYSQL_URL env variable)
# Format: mysql+pymysql://username:password@host:port/database_name
MYSQL_URL = os.getenv("MYSQL_URL", "mysql+pymysql://root:root@localhost:3306/shopsense")
SQLITE_URL = "sqlite:///./shopsense.db"

Engine = None

try:
    # Attempt MySQL connection with a short timeout to check availability
    logger.info(f"Attempting connection to MySQL database: {MYSQL_URL}")
    test_engine = create_engine(
        MYSQL_URL,
        connect_args={"connect_timeout": 3},
        pool_pre_ping=True
    )
    # Test connection
    with test_engine.connect() as conn:
        logger.info("Successfully connected to MySQL database!")
    Engine = test_engine
except Exception as e:
    logger.warning(f"MySQL connection failed ({e}). Falling back to SQLite database at {SQLITE_URL}")
    Engine = create_engine(
        SQLITE_URL,
        connect_args={"check_same_thread": False}
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=Engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
