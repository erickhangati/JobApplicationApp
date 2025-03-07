import os
from typing import Annotated

from fastapi import Depends
from sqlalchemy import create_engine
from dotenv import load_dotenv
from sqlalchemy.orm import sessionmaker, declarative_base, Session

# Load environment variables from the .env file
load_dotenv()

# Retrieve the database connection URL from environment variables
DB_URL = os.getenv("DB_URL")

# Ensure the database URL is provided
if not DB_URL:
    raise ValueError("Database URL (DB_URL) is not set in environment variables.")

# Create the SQLAlchemy database engine
engine = create_engine(DB_URL, echo=True)  # Set echo=True for debugging SQL queries

# Configure a session factory with automatic session management
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for SQLAlchemy ORM models
Base = declarative_base()


def get_db():
    """
    Dependency function that provides a new database session.
    Automatically closes the session after use.
    """
    db = SessionLocal()
    try:
        yield db  # Provide the database session
    finally:
        db.close()  # Ensure the session is closed after use


# Dependency injection for FastAPI routes
db_dependency = Annotated[Session, Depends(get_db)]
