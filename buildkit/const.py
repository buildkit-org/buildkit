from pathlib import Path

BUILDKIT_DIR = Path.home() / ".buildkit"
GLB_TARGET_DIR = BUILDKIT_DIR / "target"
DEFAULT_TARGET = "host"
LOGFILE = BUILDKIT_DIR / "buildkit.log"
VERSION = "0.1.0"
