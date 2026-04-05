from pathlib import Path
import sys


_repo_root = Path(__file__).resolve().parents[2]
_repo_root_str = str(_repo_root)
if _repo_root_str not in sys.path:
    sys.path.append(_repo_root_str)
