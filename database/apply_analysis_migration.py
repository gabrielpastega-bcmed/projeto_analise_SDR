"""
Script para aplicar migration de análises no PostgreSQL.

Usage:
    python database/apply_analysis_migration.py
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Load environment
load_dotenv()


def get_database_url() -> str:
    """Constrói URL de conexão do PostgreSQL a partir do .env."""
    host = os.getenv("AUTH_DATABASE_HOST")
    port = os.getenv("AUTH_DATABASE_PORT", "5432")
    database = os.getenv("AUTH_DATABASE_NAME")
    user = os.getenv("AUTH_DATABASE_USER")
    password = os.getenv("AUTH_DATABASE_PASSWORD")

    if not all([host, database, user, password]):
        raise ValueError(
            "Missing database configuration. Check .env for:\n"
            "AUTH_DATABASE_HOST, AUTH_DATABASE_PORT, AUTH_DATABASE_NAME, "
            "AUTH_DATABASE_USER, AUTH_DATABASE_PASSWORD"
        )

    return f"postgresql://{user}:{password}@{host}:{port}/{database}"


def apply_migration():
    """Aplica a migration de análises."""
    print("\n" + "=" * 60)
    print("APPLYING MIGRATION: octadesk_analysis_results")
    print("=" * 60 + "\n")

    # Read SQL file
    migration_file = (
        Path(__file__).parent / "migrations" / "003_create_analysis_results.sql"
    )

    if not migration_file.exists():
        print(f"[ERROR] Migration file not found: {migration_file}")
        return False

    print(f"[INFO] Reading migration: {migration_file.name}")

    with open(migration_file, "r", encoding="utf-8") as f:
        sql = f.read()

    # Connect and execute using psycopg2 directly (supports multi-statement SQL)
    try:
        import psycopg2

        # Parse connection string
        db_url = get_database_url()
        print("[INFO] Connecting to database...")

        # Extract connection params from URL
        # Format: postgresql://user:password@host:port/database
        import re

        match = re.match(r"postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)", db_url)
        if not match:
            raise ValueError("Invalid database URL format")

        user, password, host, port, database = match.groups()

        # Connect with psycopg2
        conn = psycopg2.connect(
            host=host, port=port, database=database, user=user, password=password
        )
        conn.autocommit = True

        print("[OK] Connected successfully")
        print("[INFO] Executing migration...")

        # Execute entire SQL file (psycopg2 supports multiple statements)
        cursor = conn.cursor()
        cursor.execute(sql)

        print("[OK] Migration executed successfully!")

        # Verify table exists
        cursor.execute(
            """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_name = 'octadesk_analysis_results'
        """
        )

        if cursor.fetchone():
            print("[OK] Table 'octadesk_analysis_results' verified")

            # Count indexes
            cursor.execute(
                """
                SELECT COUNT(*) 
                FROM pg_indexes 
                WHERE tablename = 'octadesk_analysis_results'
            """
            )
            index_count = cursor.fetchone()[0]
            print(f"[OK] {index_count} indexes created")
        else:
            print("[WARN] Table not found after migration")
            cursor.close()
            conn.close()
            return False

        cursor.close()
        conn.close()

        print("\n" + "=" * 60)
        print("MIGRATION COMPLETED SUCCESSFULLY!")
        print("=" * 60 + "\n")
        return True

    except Exception as e:
        print(f"\n[ERROR] Error applying migration: {e}")
        import traceback

        traceback.print_exc()
        return False


def rollback_migration():
    """Remove a tabela (rollback)."""
    print("\n[WARN] ROLLBACK: Dropping octadesk_analysis_results table")

    try:
        db_url = get_database_url()
        engine = create_engine(db_url)

        with engine.connect() as conn:
            conn.execute(text("DROP TABLE IF EXISTS octadesk_analysis_results CASCADE"))
            conn.commit()
            print("[OK] Table dropped successfully")

        return True

    except Exception as e:
        print(f"[ERROR] Error during rollback: {e}")
        return False


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Apply analysis results migration")
    parser.add_argument(
        "--rollback", action="store_true", help="Rollback migration (drop table)"
    )

    args = parser.parse_args()

    if args.rollback:
        if (
            input("[WARN] This will DROP the table. Continue? (yes/no): ").lower()
            == "yes"
        ):
            rollback_migration()
    else:
        apply_migration()
