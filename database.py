import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from urllib.parse import quote_plus
import pymysql

# Load environment variables from .env file relative to this file's location
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

# Get DB credentials from environment variables
DB_USER = os.getenv("MYSQL_USER", "root")
DB_PASSWORD = os.getenv("MYSQL_PASSWORD", "")  # Defaults to empty string, no hardcoded password
DB_HOST = os.getenv("MYSQL_HOST", "localhost")
DB_PORT = os.getenv("MYSQL_PORT", "3306")
DB_NAME = os.getenv("MYSQL_DB", "shopsense_new_db")  # New database name specifically for this project

# Helper to automatically create database if it doesn't exist
def create_database_if_not_exists():
    try:
        # Connect to MySQL server directly
        connection = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            port=int(DB_PORT)
        )
        try:
            with connection.cursor() as cursor:
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
            connection.commit()
            print(f"\nDatabase '{DB_NAME}' created or checked successfully.\n")
        finally:
            connection.close()
    except Exception as e:
        print(f"\nError checking/creating database '{DB_NAME}': {e}\n")

# Run automatic database creator
create_database_if_not_exists()

# URL-encode password to handle special characters (like '@') safely
encoded_password = quote_plus(DB_PASSWORD)

# Connect directly to the new database
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{encoded_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Create SQLAlchemy engine and sessions
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # checks connection liveness before executing queries
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency to get db session in FastAPI routes
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
