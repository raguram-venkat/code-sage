import json
from pathlib import Path
import shutil
from ..utils import find_sage_root
from .subcommand_ABC import Subcommand

class Delete(Subcommand):
    """
    sage sunset -r <repo-name> / -p <sage-root-path> / --force
    """
    name = "sunset"
    help = "Delete the .sage folder or specific cloned repositories"
    
    def add_arguments(self):
        self.parser.add_argument(
            "-r", "--repo",
            help="Name of the repository to delete from the current .sage environment"
        )
        self.parser.add_argument(
            "-p", "--path",
            help="Path to delete the sage folder manually from the given path (Finds the root .sage folder in the ancestral tree )"
        )
        self.parser.add_argument(
            "-f", "--force",
            action="store_true",
            help="Force delete without confirmation"
        )

    
    def run(self, args):
        sage_root = find_sage_root()
        global_registry_path = Path.home() / ".sage_global.json"

        # Load global registry safely
        registry = {}
        if global_registry_path.exists():
            try:
                registry = json.loads(global_registry_path.read_text())
            except Exception:
                print("Warning: Could not parse .sage_global.json; continuing with empty registry.")

        # CASE 1: Delete entire .sage folder (default)
        if not args.repo and not args.path:
            if not sage_root:
                print("No .sage folder found in current or parent directories.")
                return

            if not args.force:
                confirm = input(f"Delete entire .sage folder at {sage_root}? [y/N]: ")
                if confirm.lower() != "y":
                    print("Aborted.")
                    return

            shutil.rmtree(sage_root, ignore_errors=True)
            registry = {k: v for k, v in registry.items() if Path(v).resolve() != sage_root.resolve()}
            print(f"Deleted .sage folder at {sage_root}")

        # CASE 2: Delete specific repo
        elif args.repo:
            if not sage_root:
                print("Run inside or under a .sage folder to delete a repo.")
                return

            repo_path = sage_root / "repos" / args.repo
            if not repo_path.exists():
                print(f"Repository '{args.repo}' not found in {sage_root / 'repos'}.")
                return

            if not args.force:
                confirm = input(f"Delete repository '{args.repo}' at {repo_path}? [y/N]: ")
                if confirm.lower() != "y":
                    print("Aborted.")
                    return

            shutil.rmtree(repo_path, ignore_errors=True)
            print(f"Deleted repository '{args.repo}'")
            registry.pop(args.repo, None)

        # CASE 3: Delete arbitrary path
        elif args.path:
            target_path = Path(args.path).expanduser().resolve()
            if not target_path.exists():
                print(f"Path '{target_path}' does not exist.")
                return
            
            temp_sage_root = find_sage_root(target_path)
            if not temp_sage_root:
                print(f"No .sage folder found in the ancestral tree of {target_path}.")
                return
            
            if not args.force:
                confirm = input(f"Delete folder at '{temp_sage_root}'? [y/N]: ")
                if confirm.lower() != "y":
                    print("Aborted.")
                    return

            shutil.rmtree(temp_sage_root, ignore_errors=True)
            print(f"Deleted folder at '{temp_sage_root}'")

            registry = {k: v for k, v in registry.items() if Path(v).resolve() != temp_sage_root}

        # Write updated registry
        global_registry_path.write_text(json.dumps(registry, indent=2))
