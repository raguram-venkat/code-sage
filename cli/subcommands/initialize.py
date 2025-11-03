
from pathlib import Path
import json
from .subcommand_ABC import Subcommand


class Initialize(Subcommand):
    """
    Initialize the .sage folder and all necessary files and sub folders
    
    sage init -p/--path (default: current working directory)
    """
    name = "init"
    help = "Initialize the .sage folder and all necessary files and sub folders"
    
    def add_arguments(self):
        self.parser.add_argument(
            "-p",
            "--path",
            type=str,
            default=".",
            help="Path where the .sage folder will be initialized (default: current working directory)"
        )
    
    def run(self, args):
        # 1. Resolve user path (handles '.' or relative paths automatically)
        print(f"Initializing .sage folder at path: {args.path}")
        project_root = Path(args.path).expanduser().resolve()
        sage_folder = project_root / ".sage"

        # 2. Create folder structure
        sage_folder.mkdir(parents=True, exist_ok=True)
        (sage_folder / "logs").mkdir(exist_ok=True)
        (sage_folder / "repos").mkdir(exist_ok=True)

        # 3. Create config.json
        config = {"root": str(project_root)}
        with open(sage_folder / "config.json", "w") as f:
            json.dump(config, f, indent=4)

        # 4. Create or update global registry
        global_config = Path.home() / ".sage_global.json"
        if global_config.exists():
            registry = json.load(open(global_config))
        else:
            registry = {}

        registry[str(project_root)] = str(sage_folder)
        with open(global_config, "w") as f:
            json.dump(registry, f, indent=4)

        print(f".sage folder initialized at {sage_folder}")