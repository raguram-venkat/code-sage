
from pathlib import Path
import re

def extract_version(filename: Path) -> int:
    file_name = filename.name if isinstance(filename, Path) else filename
    match = re.match(r"^(\d+)_", file_name)
    return int(match.group(1)) if match else 0

def load_sql_file(path: Path) -> str:
    return path.read_text(encoding="utf-8")
