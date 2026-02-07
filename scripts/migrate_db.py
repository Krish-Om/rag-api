#!/usr/bin/env python3
"""
Database migration script for RAG API.
This script creates all database tables and can be run as an init container.
"""

import sys
import os
import time
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database.db import init_db, engine
from sqlalchemy.exc import OperationalError
from sqlmodel import text


def wait_for_db(max_retries=30, delay=2):
    """Wait for PostgreSQL to be ready"""
    print("🔄 Waiting for PostgreSQL to be ready...")

    for attempt in range(max_retries):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print("✅ PostgreSQL is ready!")
            return True
        except OperationalError as e:
            print(
                f"⏳ Attempt {attempt + 1}/{max_retries}: PostgreSQL not ready yet..."
            )
            if attempt == max_retries - 1:
                print(
                    f"❌ Failed to connect to PostgreSQL after {max_retries} attempts"
                )
                print(f"   Error: {e}")
                return False
            time.sleep(delay)

    return False


def run_migrations():
    """Run database migrations"""
    print("🚀 Starting database migrations...")

    # Wait for database to be ready
    if not wait_for_db():
        sys.exit(1)

    try:
        # Initialize database and create tables
        print("🔄 Creating database tables...")
        init_db()
        print("✅ Database tables created successfully!")

        # Verify tables were created
        with engine.connect() as conn:
            # Check if main tables exist
            result = conn.execute(
                text(
                    """
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """
                )
            )

            tables = [row[0] for row in result.fetchall()]

            if tables:
                print(f"✅ Found tables: {', '.join(tables)}")
            else:
                print("⚠️  No tables found - this might indicate an issue")

        print("🎉 Database migration completed successfully!")
        return True

    except Exception as e:
        print(f"❌ Database migration failed: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("🗄️  RAG API Database Migration")
    print("=" * 60)

    success = run_migrations()

    if success:
        print("\n✅ Migration completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Migration failed!")
        sys.exit(1)
