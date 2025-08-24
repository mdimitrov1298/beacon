#!/usr/bin/env python3

import argparse
import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.database import init_db, health_check
from app.config import LOG_LEVEL

log_file = "logs/manage_db.log"
Path("logs").mkdir(exist_ok=True)
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)


def init_database():
    try:
        logging.info("Initializing database...")
        init_db()
        logging.info("Database initialization completed successfully")
        return True
    except Exception as e:
        logging.error(f"Database initialization failed: {e}")
        return False


def check_health():
    try:
        logging.info("Checking database health...")
        is_healthy = health_check()
        if is_healthy:
            logging.info("Database is healthy")
            return True
        else:
            logging.error("Database health check failed")
            return False
    except Exception as e:
        logging.error(f"Health check error: {e}")
        return False


def run_migrations():
    try:
        logging.info("Running database migrations...")
        
        try:
            import alembic
        except ImportError:
            logging.error("Alembic is not installed. Please install it with: pip install alembic")
            return False
        
        import subprocess
        
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent
        )
        
        if result.returncode == 0:
            logging.info("Migrations completed successfully")
            return True
        else:
            logging.error(f"Migration failed: {result.stderr}")
            return False
            
    except Exception as e:
        logging.error(f"Error running migrations: {e}")
        return False


def create_migration(message):
    try:
        logging.info(f"Creating migration: {message}")
        
        try:
            import alembic
        except ImportError:
            logging.error("Alembic is not installed. Please install it with: pip install alembic")
            return False
        
        import subprocess
        
        result = subprocess.run(
            ["alembic", "revision", "--autogenerate", "-m", message],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent
        )
        
        if result.returncode == 0:
            logging.info("Migration file created successfully")
            return True
        else:
            logging.error(f"Failed to create migration: {result.stderr}")
            return False
            
    except Exception as e:
        logging.error(f"Error creating migration: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Beacon Database Management")
    parser.add_argument(
        "action",
        choices=["init", "health", "migrate", "create-migration"],
        help="Action to perform"
    )
    parser.add_argument(
        "--message", "-m",
        help="Migration message (required for create-migration)"
    )
    
    args = parser.parse_args()
    
    if args.action == "init":
        success = init_database()
        sys.exit(0 if success else 1)
        
    elif args.action == "health":
        success = check_health()
        sys.exit(0 if success else 1)
        
    elif args.action == "migrate":
        success = run_migrations()
        sys.exit(0 if success else 1)
        
    elif args.action == "create-migration":
        if not args.message:
            logging.error("Migration message is required for create-migration action")
            sys.exit(1)
        success = create_migration(args.message)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
