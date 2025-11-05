# core/__main__.py
from pathlib import Path
from core.migration.migration_manager import MigrationManager
import sys

def main():
    db_path = Path(".sage/data/sage.db")
    schema_dir = Path("core/schema")
    
    if len(sys.argv) == 1:
        print("Usage:")
        print("  python -m core migrate          # run migrations")
        print("  python -m core new <desc>       # create new migration")
        print("  python -m core list             # list migration status")
        print("  python -m core delete <version> # delete migration")
        print("  python -m core reset            # delete entire database")
        return
    
    command = sys.argv[1].lower() 

    with MigrationManager(db_path, schema_dir) as mgr:
        if command == "migrate":
            mgr.run_migrations()
        elif command == "new":
            desc = " ".join(sys.argv[2:]) or "new migration"
            mgr.create_migration(desc)
        elif command == "list":
            mgr.list_migrations()
        elif command == "delete":
            if len(sys.argv) < 3:
                print("Usage: python -m core delete <version>")
            else:
                mgr.delete_migration(sys.argv[2])
        elif command == "reset":
            mgr.reset_database()
        else:
            print(f"Unknown command: {command}")

if __name__ == "__main__":
    main()
