import tomllib

from enum import auto, StrEnum
from dataclasses import dataclass
from typing import Optional
from pathlib import Path
from hashlib import sha1

from . import const
from .project import root, src_dir, target_dir


# === Project =================================================================
@dataclass
class Project:
    name: str
    description: Optional[str] = None

    @classmethod
    def load(cls) -> "Project":
        r = root()

        if r is None:
            raise FileNotFoundError("No buildkit.toml found in any parent directory")

        with (r / "buildkit.toml").open("rb") as f:
            toml = tomllib.load(f)
            return Project(**toml["project"])


# === Target ==================================================================
@dataclass
class Tool:
    name: str
    cmd: str
    args: list[str]


@dataclass
class Target:
    name: str
    hash: bytes
    props: dict[str, str | bool | int]
    tools: list[Tool]


# === Manifest ================================================================
class ManifestType(StrEnum):
    PLUGIN = auto()
    BINARY = auto()
    LIBRARY = auto()


@dataclass
class Dependency:
    name: str
    version: Optional[str]
    git: Optional[str]
    branch: Optional[str]
    path: Optional[str]


@dataclass
class Manifest:
    type: ManifestType
    hash: bytes
    name: str
    path: Path
    description: Optional[str] = None
    enableIf: Optional[dict[str, bool]] = None
    alias: Optional[str] = None
    dependency: Optional[Dependency] = None


# === Common ==================================================================
class ComponentType(StrEnum):
    MANIFEST = auto()
    PROJECT = auto()
    TARGET = auto()


@dataclass
class RegistryInstace:
    manifest: Optional[Manifest] = None
    project: Optional[Project] = None
    target: Optional[Target] = None


class RegistryMeta(type):
    def __new__(cls, name, bases, attrs):
        try:
            project = Project.load()
            attrs["main_project"] = project.name
        except FileNotFoundError:
            project = Project("No project", "No project was found")
            attrs["main_project"] = None
        attrs["__components"] = {
            ComponentType.MANIFEST: {},
            ComponentType.PROJECT: {project.name: project},
            ComponentType.TARGET: {},
        }
        return super().__new__(cls, name, bases, attrs)

    def __getitem__(cls, name) -> dict[ComponentType, Manifest | Project | Target]:
        comp = getattr(cls, "__components")
        return RegistryInstace(
            manifest=comp[ComponentType.MANIFEST].get(name),
            project=comp[ComponentType.PROJECT].get(name),
            target=comp[ComponentType.TARGET].get(name),
        )


class Registry(metaclass=RegistryMeta):
    @classmethod
    @property
    def manifests(cls) -> dict[str, Manifest]:
        comp = getattr(cls, "__components")
        return comp[ComponentType.MANIFEST]

    @classmethod
    @property
    def projects(cls) -> dict[str, Project]:
        comp = getattr(cls, "__components")
        return comp[ComponentType.PROJECT]

    @classmethod
    @property
    def targets(cls) -> dict[str, Target]:
        comp = getattr(cls, "__components")
        return comp[ComponentType.TARGET]

    @classmethod
    def load(cls):
        comp = getattr(cls, "__components")

        for manifest in src_dir().glob("**/manifest.toml"):
            toml = tomllib.load(manifest.open("rb"))
            if "binary" in toml:
                toml = toml["binary"]
                toml["type"] = ManifestType.BINARY
            elif "library" in toml:
                toml = toml["library"]
                toml["type"] = ManifestType.LIBRARY
            elif "plugin" in toml:
                toml = toml["plugin"]
                toml["type"] = ManifestType.PLUGIN

            toml["hash"] = sha1(manifest.open("rb").read())
            toml["path"] = manifest
            comp[ComponentType.MANIFEST][toml["name"]] = Manifest(**toml)

        targets = list(const.GLB_TARGET_DIR.glob("*.toml"))

        if target_dir().exists():
            targets += list(target_dir().glob("*.toml"))

        for target in targets:
            tools = []
            with target.open("rb") as f:
                t = tomllib.load(f)["target"]
                f.seek(0)

                for tool in t["tools"]:
                    t["tools"][tool]["name"] = tool
                    tools.append(Tool(**t["tools"][tool]))

                t["tools"] = tools
                t["hash"] = sha1(f.read())
                comp[ComponentType.TARGET][t["name"]] = Target(**t)
