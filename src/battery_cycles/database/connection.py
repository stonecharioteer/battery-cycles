"""Database connection and initialization."""

import logging
from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from battery_cycles.database.models import Base

logger = logging.getLogger(__name__)


class Database:
    """Database connection manager."""

    def __init__(self, db_path: Path):
        """Initialize database connection.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.engine = create_engine(
            f"sqlite:///{db_path}",
            echo=False,  # Set to True for SQL query logging
            connect_args={"check_same_thread": False},  # Allow multi-thread access
        )
        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )

    def init_db(self) -> None:
        """Initialize database schema.

        Creates all tables if they don't exist.
        """
        # Ensure parent directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Create all tables
        Base.metadata.create_all(bind=self.engine)
        logger.info(f"Database initialized at {self.db_path}")

    def get_session(self) -> Generator[Session, None, None]:
        """Get a database session.

        Yields:
            SQLAlchemy Session object
        """
        session = self.SessionLocal()
        try:
            yield session
        finally:
            session.close()

    def get_session_direct(self) -> Session:
        """Get a database session directly (must be closed manually).

        Returns:
            SQLAlchemy Session object
        """
        return self.SessionLocal()


def get_database(db_path: Path) -> Database:
    """Get database instance.

    Args:
        db_path: Path to SQLite database file

    Returns:
        Database instance
    """
    return Database(db_path)
