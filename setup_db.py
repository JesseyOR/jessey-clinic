#!/usr/bin/env python
"""
Production‑grade database setup with migrations and safe seeding.
Run once to initialize the database.
"""
import sys
import os
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    try:
        from app import app
        from database.db import db
        from database.seed import seed_database
        from flask_migrate import init, migrate, upgrade, stamp

        with app.app_context():
            logger.info("Starting database setup...")

            # Initialize migrations folder if it doesn't exist
            if not os.path.exists('migrations'):
                logger.info("Initializing migrations folder...")
                init()
                stamp()  # Mark current schema as up‑to‑date

            # Generate a new migration (optional: you can skip if no model changes)
            logger.info("Generating migration script...")
            migrate(message="auto_migration")

            # Apply migrations
            logger.info("Applying migrations to database...")
            upgrade()

            # Seed only if database is empty
            logger.info("Checking if seeding is needed...")
            seed_database()

            logger.info("✅ Database setup complete. You can now run 'python app.py'.")

    except Exception as e:
        logger.exception(f"❌ Database setup failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()