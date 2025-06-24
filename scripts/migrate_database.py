#!/usr/bin/env python3
"""Database migration script to add project_relevance_comment column.

This script can be run in any environment to migrate the database schema.
Usage: uv run python scripts/migrate_database.py
"""

import sqlite3
import sys
from pathlib import Path
from loguru import logger

def find_database_file():
    """Find the database file in common locations."""
    possible_paths = [
        Path("./arxiv_papers.db"),  # Current directory
        Path.home() / ".arxiv_notifier" / "arxiv_notifier.db",  # User home
        Path("data/arxiv_papers.db"),  # Data directory
    ]
    
    for path in possible_paths:
        if path.exists():
            return path
    
    return None

def migrate_database():
    """Add project_relevance_comment column to existing database."""
    db_path = find_database_file()
    
    if not db_path:
        logger.warning("No database file found. The database will be created with the correct schema on first run.")
        return True
    
    logger.info(f"Found database at: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if processed_papers table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='processed_papers'
        """)
        
        if not cursor.fetchone():
            logger.info("processed_papers table does not exist. No migration needed.")
            conn.close()
            return True
        
        # Check if column already exists
        cursor.execute("PRAGMA table_info(processed_papers)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if "project_relevance_comment" not in columns:
            logger.info("Adding project_relevance_comment column...")
            cursor.execute("""
                ALTER TABLE processed_papers 
                ADD COLUMN project_relevance_comment TEXT
            """)
            conn.commit()
            logger.success("Migration completed successfully!")
        else:
            logger.info("Column already exists. No migration needed.")
        
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return False

if __name__ == "__main__":
    logger.info("Starting database migration...")
    success = migrate_database()
    
    if success:
        logger.success("Database migration completed successfully!")
        sys.exit(0)
    else:
        logger.error("Database migration failed!")
        sys.exit(1)