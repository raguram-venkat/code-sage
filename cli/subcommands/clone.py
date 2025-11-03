
from pathlib import Path
from git import Repo
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

    def run(self, args):
        if args.url:
            print(f"Cloning repository from {args.url} with depth {args.depth}")
        else:
            print("Please provide a repository URL to clone.")
            return
        
        sage_root = find_sage_root()
        if not sage_root:
            print("No .sage folder found in current or parent directories. Run `sage init` first.")
            return
        print("Inside run method of Clone subcommand")
        
        repo_name = Path(args.url).stem.replace(".git", "")
        clone_path = sage_root / "repos" / repo_name
        clone_path.parent.mkdir(exist_ok=True, parents=True)
        
        try:
            Repo.clone_from(args.url, clone_path, depth=args.depth)
            
        except Exception as e:
            print("Clone failed:")
            print(e.stderr.decode())

  
        log_path = sage_root / "logs" / "clone.log"
        with open(log_path, "a") as log:
            log.write(f"Cloned {args.url} into {clone_path}\n")
        
        
        
        
    