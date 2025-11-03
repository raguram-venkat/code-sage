import json
import datetime
from pathlib import Path
from git import Repo, GitCommandError
from ..utils import find_sage_root
from .subcommand_ABC import Subcommand


class Update(Subcommand):
    """
    sage update <repo-name> / sage update --all
    """
    
    name = "update"
    help = "Update one or all cloned repositories"

    def add_arguments(self):
        self.parser.add_argument("repo", nargs="?", help="Name of the repository to update")
        self.parser.add_argument("--all", action="store_true", help="Update all repositories")

    def run(self, args):
        sage_root = find_sage_root()
        if not sage_root:
            print("No .sage folder found in current or parent directories. Run `sage init` first.")
            return
        log_root = sage_root / "logs"
        meta_file = log_root / "repos.json"
        if not meta_file.exists():
            print("No repos.json found — nothing to update.")
            return

        data = json.load(open(meta_file))
        repos = data.get("repos", {})
        
        if not args.all and args.repo is None:
            print("Please specify a repository name or use --all to update all repositories.")
            return

        targets = [args.repo] if args.repo else repos.keys()
        
        for name in targets:
            info = repos.get(name)
            if not info:
                print(f"Repository {name} not found in registry.")
                continue

            repo_path = Path(info["path"])
            if not repo_path.exists():
                print(f"Path missing for {name}: {repo_path}")
                continue

            try:
                repo = Repo(repo_path)
                origin = repo.remotes.origin
                origin.fetch()
                origin.pull()
                repos[name]["last_commit"] = repo.head.commit.hexsha
                repos[name]["last_updated"] = datetime.datetime.now().isoformat()
            except GitCommandError as e:
                print(f"Update failed for {name}: {e}")

        with open(meta_file, "w") as f:
            json.dump(data, f, indent=4)
