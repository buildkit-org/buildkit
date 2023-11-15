import logging
import platform
import sys

from inspect import cleandoc

from . import const
from . import vt100
from .args import Args
from .cmds import cmds

_logger = logging.getLogger(__name__)


def setup_logging(verbose: bool):
    if verbose:
        logging.basicConfig(
            level=logging.DEBUG,
            format=f"{vt100.CYAN}%(asctime)s{vt100.RESET} {vt100.YELLOW}%(levelname)s{vt100.RESET} %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    else:
        logging.basicConfig(
            level=logging.DEBUG,
            filename=const.LOGFILE,
            filemode="w",
            format="%(asctime)s %(levelname)s %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )


def generate_host_target():
    (const.BUILDKIT_DIR / "target").mkdir(parents=True)
    target = cleandoc(
        f"""
    [target]
    name = "host"

    [target.props]
    arch = "{platform.machine()}"
    sys = "{platform.system().lower()}"
    host = true
    freestanding = false
    endian = "{sys.byteorder}"

    [target.tools.cc]
    cmd = "gcc"
    args = ["-Wall", "-Wextra", "-Werror", "-std=c2x"]

    [target.tools.cxx]
    cmd = "g++"
    args = ["-Wall", "-Wextra", "-Werror", "-fno-exceptions", "-fno-rttia", "-std=c++2b"]

    [target.tools.ld]
    cmd = "g++"
    args = []

    [target.tools.ar]
    cmd = "ar"
    args = ["rcs"]

    [target.tools.as]
    cmd = "as"
    args = []\n
    """
    )

    (const.BUILDKIT_DIR / "target" / "host.toml").write_text(target)


def main() -> int:
    if not const.BUILDKIT_DIR.exists():
        generate_host_target()

    cmd = "help" if len(sys.argv) < 2 else sys.argv[1]
    args = Args.parse([] if len(sys.argv) < 3 else sys.argv[2:])
    setup_logging(hasattr(args, "verbose"))

    try:
        args.bind(cmds[cmd].args)
        cmds[cmd](args)
    except Exception as e:
        _logger.debug("Exception", exc_info=True)
        print(f"{vt100.RED}{vt100.BOLD}Error:{vt100.RESET} {e}")

    return 0
