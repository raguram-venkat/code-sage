from pathlib import Path
from core.migration.migration_manager import MigrationManager
from core.database import get_connection, execute, fetch_all


def reset_database(db_path: Path):
    """Delete existing DB file to start clean."""
    if db_path.exists():
        db_path.unlink()
        print(f"Deleted existing DB at {db_path}")


def run_migrations():
    db_path = Path(".sage/data/sage.db")
    schema_dir = Path("core/schema")

    with MigrationManager(db_path, schema_dir) as mgr:
        mgr.run_migrations()


def insert_sample_records():
    print("Inserting sample repo and file records...")
    execute(
        "INSERT INTO repos (name, path, url) VALUES (?, ?, ?)",
        ("test_repo", "/tmp/test_repo", "https://example.com/repo.git")
    )

    repo = fetch_all("SELECT id FROM repos WHERE name=?", ("test_repo",))[0]
    repo_id = repo["id"]

    execute(
        "INSERT INTO files (repo_id, relative_path, file_hash, size_bytes) "
        "VALUES (?, ?, ?, ?)",
        (repo_id, "core/database.py", "abc123", 1024)
    )

    files = fetch_all("SELECT * FROM files")
    print(f"Inserted {len(files)} file(s):")
    for f in files:
        print(dict(f))


def delete_sample_records():
    print("Deleting all repo and file records...")
    execute("DELETE FROM files")
    execute("DELETE FROM repos")
    print("Records deleted.")


def show_tables():
    conn = get_connection()
    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()
    conn.close()
    print("\nDatabase tables:")
    for t in tables:
        print(f" - {t['name']}")


def main():
    db_path = Path(".sage/data/sage.db")
    reset_database(db_path)
    run_migrations()
    show_tables()
    insert_sample_records()
    delete_sample_records()


if __name__ == "__main__":
    main()
