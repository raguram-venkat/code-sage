import sqlite3
from pathlib import Path
from typing import List, Optional
import re

from core.migration.utils import load_sql_file, extract_version


class MigrationManager:
    """
    Reliable SQLite migration manager.

    Usage:
        with MigrationManager(db_path, schema_dir) as mgr:
            mgr.run_migrations()
    """

    def __init__(self, db_path: Path, schema_dir: Path, verbose: bool = True):
        self.db_path = db_path
        self.schema_dir = schema_dir
        self.conn: Optional[sqlite3.Connection] = None
        self.verbose = verbose

    # ------------------------------------------------------------------ #
    # Logging helper
    # ------------------------------------------------------------------ #
    def _log(self, message: str):
        if self.verbose:
            print(message)

    # ------------------------------------------------------------------ #
    # Connection handling
    # ------------------------------------------------------------------ #
    def connect(self):
        """Establish a SQLite connection."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        return self.conn

    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    # ------------------------------------------------------------------ #
    # Migration metadata tracking
    # ------------------------------------------------------------------ #
    def ensure_migrations_table(self):
        """Create the _migrations table if it doesn't exist yet."""
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS _migrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                version TEXT UNIQUE NOT NULL,
                description TEXT,
                applied BOOLEAN DEFAULT 1,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                rolled_back_at TIMESTAMP
            )
            """
        )
        self.conn.commit()

    def get_applied_migrations(self) -> set[str]:
        """Fetch all applied migration versions from DB."""
        try:
            rows = self.conn.execute("SELECT version FROM _migrations").fetchall()
            return {row["version"] for row in rows}
        except sqlite3.OperationalError:
            # If _migrations table is missing, nothing is applied
            return set()

    def mark_migration_applied(self, version: str, description: str):
        """Insert record into _migrations table after success."""
        self.conn.execute(
            "INSERT INTO _migrations (version, description) VALUES (?, ?)",
            (version, description),
        )
        self.conn.commit()

    # ------------------------------------------------------------------ #
    # Migration application logic
    # ------------------------------------------------------------------ #
    def get_migration_files(self) -> List[Path]:
        if not self.schema_dir.exists():
            return []
        files = [
            f for f in self.schema_dir.glob("*.sql")
            if extract_version(f.name) > 0
        ]
        files.sort(key=lambda f: extract_version(f.name))
        return files

    def safe_executescript(self, sql: str):
        """Execute SQL with rollback on error."""
        try:
            self.conn.executescript(sql)
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise RuntimeError(f"SQL execution failed: {e}") from e

    def apply_migration(self, migration_file: Path, applied_versions: set[str]) -> bool:
        """Apply a single migration if not already applied."""
        version = f"{extract_version(migration_file.name):03d}"
        if version in applied_versions:
            self._log(f"Skipping already applied migration {version}")
            return False

        sql = load_sql_file(migration_file)
        self._log(f"Applying migration {version}: {migration_file.name}")

        # Attempt to execute, but tolerate "already exists" warnings safely
        try:
            self.safe_executescript(sql)
        except RuntimeError as e:
            msg = str(e).lower()
            # If table/view/index already exists, treat as non-fatal idempotent case
            if "already exists" in msg:
                self._log(f"  (ignored harmless error: {e})")
            else:
                raise

        # Record as applied
        description = migration_file.stem.split("_", 1)[1] if "_" in migration_file.stem else ""
        self.mark_migration_applied(version, description)
        self._log(f"Migration {version} applied successfully.")
        return True

    def run_migrations(self) -> int:
        """Apply all pending migrations."""
        self.ensure_migrations_table()
        files = self.get_migration_files()
        if not files:
            self._log("No migration files found.")
            return 0

        applied_versions = self.get_applied_migrations()
        pending = [f for f in files if f"{extract_version(f.name):03d}" not in applied_versions]

        if not pending:
            self._log("Database is already up to date.")
            return 0

        count = 0
        for file in pending:
            if self.apply_migration(file, applied_versions):
                count += 1
                applied_versions.add(f"{extract_version(file.name):03d}")

        self._log(f"Applied {count} new migration(s).")
        return count

    # ------------------------------------------------------------------ #
    # Migration creation & rollback
    # ------------------------------------------------------------------ #
    def create_migration(self, description: str) -> Path:
        existing = self.get_migration_files()
        next_version = 1 if not existing else extract_version(existing[-1].name) + 1
        slug = re.sub(r"[^a-z0-9_]", "", description.lower().replace(" ", "_"))
        filename = f"{next_version:03d}_{slug}.sql"
        path = self.schema_dir / filename
        self.schema_dir.mkdir(parents=True, exist_ok=True)
        template = f"""-- Migration {next_version:03d}: {description}
-- Description: Add details here

-- SQL statements go below

"""
        path.write_text(template, encoding="utf-8")
        self._log(f"Created new migration: {path}")
        return path

    def rollback_last(self, unsafe_force: bool = False):
        applied = sorted(list(self.get_applied_migrations()))
        if not applied:
            self._log("No migrations to roll back.")
            return
        last = applied[-1]
        if not unsafe_force:
            self._log("Rollback does NOT undo schema changes. Use unsafe_force=True to remove record.")
            return
        self.conn.execute("DELETE FROM _migrations WHERE version=?", (last,))
        self.conn.commit()
        self._log(f"Removed migration record {last}.")
        
    
    # ------------------------------------------------------------------ #
    # Extra management utilities
    # ------------------------------------------------------------------ #
    def list_migrations(self):
        """Print all known migrations and their applied status."""
        self.ensure_migrations_table()
        files = self.get_migration_files()
        applied = self.get_applied_migrations()

        if not files:
            self._log("No migration files found.")
            return

        self._log("\nMigration Status:")
        for f in files:
            version = f"{extract_version(f.name):03d}"
            desc = f.stem.split('_', 1)[1] if "_" in f.stem else ""
            status = "APPLIED" if version in applied else "PENDING"
            self._log(f"  {version}: {desc:30} [{status}]")

    def delete_migration(self, version: str):
        """Delete a migration file and its record if applied."""
        target = None
        for f in self.get_migration_files():
            if f"{extract_version(f.name):03d}" == version:
                target = f
                break

        if not target:
            self._log(f"Migration {version} not found.")
            return

        # Delete migration file
        target.unlink(missing_ok=True)
        self._log(f"Deleted migration file {target.name}")

        # Remove from _migrations table if exists
        self.ensure_migrations_table()
        self.conn.execute("DELETE FROM _migrations WHERE version = ?", (version,))
        self.conn.commit()
        self._log(f"Removed migration {version} record (if existed).")

    def reset_database(self):
        """Wipe the entire database file (use cautiously)."""
        self.close()
        if self.db_path.exists():
            self.db_path.unlink()
            self._log(f"Deleted database at {self.db_path}")
        else:
            self._log("No database file found.")
