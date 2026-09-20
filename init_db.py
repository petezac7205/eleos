#!/usr/bin/env python3
"""
=============================================================================
Eleos Database Initializer & Schema Migrator
=============================================================================
Usage:
    python init_db.py [OPTIONS]

Options:
    --seed          Seed benchmark and initial demo dataset (default: True)
    --no-seed       Skip inserting seed dataset
    --reset         Drop existing tables before recreating schema
    --url URL       PostgreSQL connection URL (e.g. postgresql://user:pass@localhost:5432/eleos)
    --host HOST     PostgreSQL host (default: localhost or env POSTGRES_HOST)
    --port PORT     PostgreSQL port (default: 5432 or env POSTGRES_PORT)
    --user USER     PostgreSQL user (default: postgres or env POSTGRES_USER)
    --password PWD  PostgreSQL password (default: postgres or env POSTGRES_PASSWORD)
    --dbname DB     Database name (default: eleos or env POSTGRES_DB)
    --help          Show help message and exit
=============================================================================
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from typing import Optional, Tuple
from urllib.parse import urlparse

# Load dotenv if available
try:
    from dotenv import load_dotenv
    env_file = Path(__file__).resolve().parent / ".env"
    load_dotenv(dotenv_path=env_file)
except ImportError:
    pass

# Try importing psycopg2 or sqlalchemy
try:
    import psycopg2
    from psycopg2 import sql
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
    HAS_PSYCOPG2 = True
except ImportError:
    HAS_PSYCOPG2 = False

try:
    from sqlalchemy import create_engine, text, inspect
    HAS_SQLALCHEMY = True
except ImportError:
    HAS_SQLALCHEMY = False

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("eleos_init_db")

ROOT_DIR = Path(__file__).resolve().parent
SCHEMA_FILE = ROOT_DIR / "database" / "schema.sql"
SEED_FILE = ROOT_DIR / "database" / "seed_data.sql"

TABLES_ORDER = [
    "users",
    "ngo_profiles",
    "documents",
    "campaigns",
    "budget_items",
    "milestones",
    "donations",
    "trustability_scores",
    "feasibility_scores",
    "cost_benchmarks",
    "volunteer_opportunities",
    "volunteer_applications",
    "volunteer_credentials",
    "review_queue",
]


from urllib.parse import urlparse, unquote

def parse_db_params(args: argparse.Namespace) -> dict:
    """Parse connection configuration from CLI, environment, or default values."""
    db_url = args.url or os.getenv("DATABASE_URL")

    if db_url:
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)
        parsed = urlparse(db_url)
        return {
            "url": db_url,
            "host": parsed.hostname or "localhost",
            "port": parsed.port or 5432,
            "user": unquote(parsed.username) if parsed.username else "postgres",
            "password": unquote(parsed.password) if parsed.password else "postgres",
            "dbname": (parsed.path or "/postgres").lstrip("/"),
        }

    user = args.user or os.getenv("POSTGRES_USER", "postgres")
    password = args.password or os.getenv("POSTGRES_PASSWORD", "postgres")
    host = args.host or os.getenv("POSTGRES_HOST", "localhost")
    port = int(args.port or os.getenv("POSTGRES_PORT", 5432))
    dbname = args.dbname or os.getenv("POSTGRES_DB", "postgres")

    constructed_url = f"postgresql://{user}:{password}@{host}:{port}/{dbname}"
    return {
        "url": constructed_url,
        "host": host,
        "port": port,
        "user": user,
        "password": password,
        "dbname": dbname,
    }


def ensure_database_exists(params: dict):
    """Ensure the target database exists on PostgreSQL, creating it if necessary."""
    dbname = params["dbname"]
    if dbname == "postgres":
        logger.info(f"Target database is default 'postgres'. Skipping CREATE DATABASE.")
        return

    logger.info(f"Checking if database '{dbname}' exists on {params['host']}:{params['port']}...")

    if HAS_PSYCOPG2:
        try:
            conn = psycopg2.connect(
                dbname="postgres",
                user=params["user"],
                password=params["password"],
                host=params["host"],
                port=params["port"],
                connect_timeout=10
            )
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cur = conn.cursor()

            cur.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s;", (dbname,))
            exists = cur.fetchone()

            if not exists:
                logger.info(f"Database '{dbname}' does not exist. Creating database '{dbname}'...")
                cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(dbname)))
                logger.info(f"Database '{dbname}' created successfully.")
            else:
                logger.info(f"Database '{dbname}' already exists.")

            cur.close()
            conn.close()
        except Exception as e:
            logger.warning(f"Note on checking maintenance DB: {e}. Will attempt direct connection to '{dbname}'.")


def run_psycopg2_init(params: dict, reset: bool, seed: bool):
    """Initialize database using psycopg2."""
    logger.info(f"Connecting to database '{params['dbname']}' via psycopg2...")
    try:
        conn = psycopg2.connect(params["url"], connect_timeout=15)
    except Exception:
        conn = psycopg2.connect(
            dbname=params["dbname"],
            user=params["user"],
            password=params["password"],
            host=params["host"],
            port=params["port"],
            connect_timeout=15
        )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()

    if reset:
        logger.warning("Reset flag provided. Dropping existing tables...")
        for table in reversed(TABLES_ORDER):
            cur.execute(f"DROP TABLE IF EXISTS {table} CASCADE;")
        logger.info("All existing tables dropped.")

    # Read and apply schema.sql
    if not SCHEMA_FILE.exists():
        raise FileNotFoundError(f"Schema file not found at {SCHEMA_FILE}")

    logger.info(f"Applying schema from {SCHEMA_FILE}...")
    with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    cur.execute(schema_sql)
    logger.info("Schema DDL applied successfully.")

    # Apply seed data if requested
    if seed:
        if SEED_FILE.exists():
            logger.info(f"Inserting seed benchmark data from {SEED_FILE}...")
            with open(SEED_FILE, "r", encoding="utf-8") as f:
                seed_sql = f.read()
            cur.execute(seed_sql)
            logger.info("Seed data applied successfully.")
        else:
            logger.warning(f"Seed file not found at {SEED_FILE}, skipping seed insertion.")

    # Verify tables
    logger.info("Verifying created tables and row counts:")
    for table in TABLES_ORDER:
        try:
            cur.execute(f"SELECT COUNT(*) FROM {table};")
            count = cur.fetchone()[0]
            logger.info(f"  [OK] Table '{table:<25}' -> {count} rows")
        except Exception as err:
            logger.error(f"  [FAIL] Table '{table}': {err}")

    cur.close()
    conn.close()


def run_sqlalchemy_init(params: dict, reset: bool, seed: bool):
    """Initialize database using SQLAlchemy."""
    logger.info(f"Connecting to database via SQLAlchemy engine: {params['url']}...")
    engine = create_engine(params["url"])

    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        if reset:
            logger.warning("Reset flag provided. Dropping existing tables...")
            for table in reversed(TABLES_ORDER):
                conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE;"))
            logger.info("All existing tables dropped.")

        # Read and execute schema
        if not SCHEMA_FILE.exists():
            raise FileNotFoundError(f"Schema file not found at {SCHEMA_FILE}")

        logger.info(f"Applying schema from {SCHEMA_FILE}...")
        with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
            schema_sql = f.read()

        conn.execute(text(schema_sql))
        logger.info("Schema DDL applied successfully.")

        if seed:
            if SEED_FILE.exists():
                logger.info(f"Inserting seed benchmark data from {SEED_FILE}...")
                with open(SEED_FILE, "r", encoding="utf-8") as f:
                    seed_sql = f.read()
                conn.execute(text(seed_sql))
                logger.info("Seed data applied successfully.")
            else:
                logger.warning(f"Seed file not found at {SEED_FILE}, skipping seed insertion.")

        # Verify
        logger.info("Verifying created tables and row counts:")
        for table in TABLES_ORDER:
            try:
                res = conn.execute(text(f"SELECT COUNT(*) FROM {table};"))
                count = res.scalar()
                logger.info(f"  [OK] Table '{table:<25}' -> {count} rows")
            except Exception as err:
                logger.error(f"  [FAIL] Table '{table}': {err}")




def main():
    parser = argparse.ArgumentParser(
        description="Initialize Eleos PostgreSQL schema, tables, and seed benchmarks."
    )
    parser.add_argument("--seed", action="store_true", default=True, help="Insert benchmark and demo seed dataset (default: True)")
    parser.add_argument("--no-seed", action="store_false", dest="seed", help="Skip inserting seed dataset")
    parser.add_argument("--reset", action="store_true", default=False, help="Drop all existing tables before creating schema")
    parser.add_argument("--url", type=str, default=None, help="PostgreSQL connection URL")
    parser.add_argument("--host", type=str, default=None, help="PostgreSQL host")
    parser.add_argument("--port", type=int, default=None, help="PostgreSQL port")
    parser.add_argument("--user", type=str, default=None, help="PostgreSQL username")
    parser.add_argument("--password", type=str, default=None, help="PostgreSQL password")
    parser.add_argument("--dbname", type=str, default=None, help="Database name")

    args = parser.parse_args()

    params = parse_db_params(args)
    logger.info(f"Target Database: {params['user']}@{params['host']}:{params['port']}/{params['dbname']}")

    if not HAS_PSYCOPG2 and not HAS_SQLALCHEMY:
        logger.error("Neither psycopg2 nor sqlalchemy is installed. Please run: pip install psycopg2-binary sqlalchemy")
        sys.exit(1)

    try:
        ensure_database_exists(params)

        if HAS_PSYCOPG2:
            run_psycopg2_init(params, reset=args.reset, seed=args.seed)
        else:
            run_sqlalchemy_init(params, reset=args.reset, seed=args.seed)

        print("\n" + "=" * 68)
        print("  SUCCESS: Eleos database and tables initialized successfully!")
        print("=" * 68 + "\n")

    except Exception as e:
        logger.error(f"\nFailed to initialize database: {e}")
        logger.info("\nTroubleshooting tips:")
        logger.info("  1. Verify PostgreSQL server is running (e.g. check Windows Services or pg_ctl status).")
        logger.info("  2. Check credentials in your .env file (POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB).")
        logger.info("  3. Pass explicit connection args: python init_db.py --host localhost --user postgres --password your_password --dbname eleos\n")
        sys.exit(1)


if __name__ == "__main__":
    main()

