import os

from pathlib import Path
from typing import Optional


def root() -> Optional[Path]:
    cwd = Path.cwd()

    while str(cwd) != cwd.root:
        if (cwd / "buildkit.toml").exists():
            return cwd
        cwd = cwd.parent

    return None


def chdir():
    r = root()
    if r is None:
        raise FileNotFoundError("No buildkit.toml found in any parent directory")
    os.chdir(r)


def buildkit_dir() -> Path:
    return root() / ".buildkit"


def build_dir() -> Path:
    return buildkit_dir() / "build"


def meta_dir() -> Path:
    return root() / "meta"


def target_dir() -> Path:
    return meta_dir() / "targets"


def src_dir() -> Path:
    return root() / "src"
