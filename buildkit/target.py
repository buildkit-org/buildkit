import logging

from . import vt100
from .registry import Registry, Target

_logger = logging.getLogger(__name__)


def load_target(name: str) -> Target:
    t = Registry[name].target

    if t is None:
        Registry.load()
        t = Registry[name].target

    _logger.info(f"Loaded target {t.name}")
    _logger.debug(f"Hash: {t.hash.hexdigest()}")
    _logger.debug(f"Target properties: ")

    for prop in t.props:
        _logger.debug(vt100.indent(f"{prop}: {t.props[prop]}"))

    _logger.debug(f"Target tools: ")

    for tool in t.tools:
        _logger.debug(vt100.indent(f"* {tool.name}"))
        _logger.debug(vt100.indent(f"cmd: {tool.cmd}", indent=8))
        _logger.debug(vt100.indent(f"args: {tool.args}", indent=8))

    return t
