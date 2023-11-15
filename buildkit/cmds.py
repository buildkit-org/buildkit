import inspect
import shutil

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Optional, Iterator, Callable

from . import builder
from . import const
from . import manifest
from . import project
from . import vt100
from .args import Args
from .target import load_target
from .registry import Registry, ManifestType


@dataclass
class Arg:
    name: str
    shortName: str
    description: str
    type: type
    default: Optional[Any] = None
    optional: Optional[bool] = False


@dataclass
class Cmd:
    shortName: str
    longName: str
    description: str
    isPlugin: bool
    callback: Callable[[Args], None]
    args: Optional[list[Arg]] = None

    def __call__(self, args):
        self.callback(args)


class Cmds(Mapping):
    def __init__(self: "Cmds"):
        self.__vals: list[Cmd] = []

    def lookup(self, callback: Callable[[Args], None]) -> Optional[Cmd]:
        return next(filter(lambda c: c.callback == callback, self.__vals), None)

    def append(
        self: "Cmds",
        shortName: str,
        longName: str,
        description: str,
        isPlugin: bool,
        cls: type,
    ):
        self.__vals.append(Cmd(shortName, longName, description, isPlugin, cls))

    def __getitem__(self: "Cmds", __key: str) -> type:
        f = filter(lambda c: c.shortName == __key or c.longName == __key, self.__vals)

        try:
            return next(f)
        except StopIteration:
            raise KeyError(__key) from None

    def __len__(self: "Cmds") -> int:
        return len(self.__vals)

    def __iter__(self: "Cmds") -> Iterator:
        return iter(self.__vals)

    def __repr__(self: "Cmds") -> str:
        ret = "{"

        for cmd in self.__vals:
            ret += f"{cmd.shortName, cmd.longName}: {repr(cmd.cls)}, "
        ret = f"{ret[:-2]}}}"

        return ret


cmds = Cmds()


# === Cli decorators ==========================================================
def arg(
    name: str,
    shortName: str,
    description: str,
    type: type,
    default: Optional[Any] = None,
    optional: Optional[bool] = False,
):
    def wrap(fn: Callable[[Args], None]):
        cmd = cmds.lookup(fn)

        if cmd is None:
            raise ValueError("Command not found, did you forget to add @cmd?")
        if cmd.args is None:
            cmd.args = []

        cmd.args.append(Arg(name, shortName, description, type, default, optional))

        return fn

    return wrap


def cmd(shortName: str, longName: str, description: str):
    curframe = inspect.currentframe()
    calframe = inspect.getouterframes(curframe, 2)

    def wrap(fn: Callable[[Args], None]):
        cmds.append(
            shortName, longName, description, calframe[1].filename != __file__, fn
        )
        return fn

    return wrap


# === Builtin commands ========================================================
@arg("target", "t", "Target to build for", type=str, default="host")
@arg("component", "c", "Component to build", type=str)
@cmd("b", "build", "Build a component")
def buildCmd(args: Args):
    if args.component is None:
        raise ValueError("No component specified, use buildkit list to list components")

    target = load_target(args.target)
    man = manifest.load_manifest(args.component)

    if not project.build_dir().exists():
        project.build_dir().mkdir(parents=True)

    builder.ninja_gen(target, man)


@cmd("l", "list", "List all components")
def listCmd(_: Args):
    Registry.load()
    components = list(Registry.manifests.values())

    binaries = list(
        map(
            lambda c: c.name,
            filter(lambda c: c.type == ManifestType.BINARY, components),
        )
    )
    libraries = list(
        map(
            lambda c: c.name,
            filter(lambda c: c.type == ManifestType.LIBRARY, components),
        )
    )

    vt100.title(f"{vt100.CYAN}Binaries{vt100.RESET}")
    if len(binaries) == 0:
        print(vt100.indent("No binaries found"))
    else:
        print(vt100.indent(vt100.wordwrap(", ".join(binaries))))

    print()
    vt100.title(f"{vt100.CYAN}Libraries{vt100.RESET}")
    if len(libraries) == 0:
        print(vt100.indent("No libraries found"))
    else:
        print(vt100.indent(vt100.wordwrap(", ".join(libraries))))


@cmd("c", "clean", "Clean the build directory")
def cleanCmd(_: Args):
    if not project.build_dir().exists():
        raise FileNotFoundError("No build directory found")
    shutil.rmtree(project.build_dir())


@cmd("n", "nuke", "Clean the buildkit directory")
def nukeCmd(_: Args):
    if not project.buildkit_dir().exists():
        raise FileNotFoundError("No buildkit directory found")
    shutil.rmtree(project.buildkit_dir())


@cmd("v", "version", "Print the version")
def versionCmd(_: Args):
    print(f"buildkit {const.VERSION}")


@arg("command", "c", "Command you want to get help for", type=str, optional=True)
@cmd("h", "help", "Print this help message")
def helpCmd(args: Args):
    if args.command is not None:
        cmd = cmds[args.command]
        print(f"Usage: buildkit {cmd.longName} ", end="")
        for arg in cmd.args:
            type_display = "" if arg.type is bool else f" {arg.type.__name__}"
            if arg.optional:
                print(
                    f"[--{arg.name} | -{arg.shortName}{type_display}]",
                    end=" ",
                )
            else:
                print(
                    f"<--{arg.name} | -{arg.shortName}{type_display}>",
                    end=" ",
                )

        print()
        print()

        vt100.title("Description")
        print(
            vt100.indent(
                f"{cmd.description} {'This is a plugin command' if cmd.isPlugin else ''}"
            )
        )

        print()
        vt100.title("Arguments")
        for arg in cmd.args:
            opt = f"{vt100.CYAN}(optional){vt100.RESET}" if arg.optional else ""
            print(
                vt100.indent(
                    f"{vt100.GREEN}-{arg.shortName or ' '}{vt100.RESET}  --{vt100.CYAN}{arg.name:20}{vt100.RESET} {arg.description} {opt}"
                )
            )

        return

    print("Usage: buildkit <command> [args...]\n")
    vt100.title("Description")

    print(
        vt100.indent(
            "A build system and package manager for low-level software development\n"
        )
    )

    vt100.title("Commands")

    for cmd in cmds:
        plg = f"{vt100.CYAN}(plugin){vt100.RESET}" if cmd.isPlugin else ""
        print(
            vt100.indent(
                f" {vt100.GREEN}{cmd.shortName or ' '}{vt100.RESET}  {cmd.longName:20} {cmd.description} {plg}"
            )
        )

    print()
    vt100.title("Logging")
    print(vt100.indent("Logs are stored in:"))
    print(vt100.indent(f" - {const.LOGFILE}"))
