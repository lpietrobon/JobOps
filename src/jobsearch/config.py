from pathlib import Path
from typing import Any
try:
    import yaml
except ModuleNotFoundError:
    yaml = None

DEFAULT_CONFIG_PATH = Path("config.yaml")
DEFAULT_DB_PATH = Path("data/jobs.sqlite")

def load_config(path: str | Path = DEFAULT_CONFIG_PATH) -> dict[str, Any]:
    p = Path(path)
    if not p.exists():
        example = Path("config.example.yaml")
        if example.exists():
            return _load_yaml(example)
        return {}
    return _load_yaml(p)

def _load_yaml(path: Path) -> dict[str, Any]:
    if yaml is None:
        # Minimal fallback for environments that run tests before installing deps.
        return {"profile": {}, "runtime": {"request_timeout_seconds": 30}, "sources": {}}
    return yaml.safe_load(path.read_text()) or {}
