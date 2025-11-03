from pathlib import Path

def find_sage_root(start: Path | str = ".") -> Path | None:
    path = Path(start).expanduser().resolve()
    for parent in [path] + list(path.parents):
        if (parent / ".sage" / "config.json").exists():
            return parent / ".sage"
    return None
