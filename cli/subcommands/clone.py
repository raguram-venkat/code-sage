
from pathlib import Path
from git import Repo, GitCommandError
import subprocess
import json
import datetime
from .subcommand_ABC import Subcommand
from ..utils.path_utils import find_sage_root


class Clone(Subcommand):
    """
    sage clone <remote-repo-url> -d/--depth (default 1)
    """
    
    name = "clone"
    help = "To clone and get the repo in your local"
    
    def add_arguments(self):
        self.parser.add_argument("url")
        self.parser.add_argument("-d", "--depth", type=int, default=1, help="Depth of cloning the repo")

    def run(self,args):
        if not args.url:
            print("Please provide a repository URL to clone.")
            return

        sage_root = find_sage_root()
        if not sage_root:
            print("No .sage folder found in current or parent directories. Run `sage init` first.")
            return

        repo_name = Path(args.url).stem.replace(".git", "")
        clone_path = sage_root / "repos" / repo_name
        clone_path.parent.mkdir(parents=True, exist_ok=True)

        # Clone repo (GitPython preferred)
        try:
            repo = Repo.clone_from(args.url, clone_path, depth=args.depth)
        except GitCommandError:
            subprocess.check_call(["git", "clone", "--depth", str(args.depth), args.url, str(clone_path)])
            repo = Repo(clone_path)

        # Detect and handle LFS if needed
        gitattributes = clone_path / ".gitattributes"
        if gitattributes.exists() and "filter=lfs" in gitattributes.read_text():
            subprocess.run(["git", "lfs", "install"], cwd=clone_path, check=True)
            subprocess.run(["git", "lfs", "fetch", "--all"], cwd=clone_path, check=True)
            subprocess.run(["git", "lfs", "checkout"], cwd=clone_path, check=True)

        # Update or create repos.json
        log_root = sage_root / "logs"
        meta_file = log_root / "repos.json"
        data = json.load(open(meta_file)) if meta_file.exists() else {"repos": {}}
        data["repos"][repo_name] = {
            "url": args.url,
            "path": str(clone_path),
            "last_commit": repo.head.commit.hexsha,
            "last_updated": datetime.datetime.now().isoformat()
        }

        with open(meta_file, "w") as f:
            json.dump(data, f, indent=4)
                 