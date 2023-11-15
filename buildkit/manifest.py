import logging

from .registry import Registry, Manifest

_logger = logging.getLogger(__name__)


def load_manifest(name: str) -> Manifest:
    manifest = Registry[name].manifest

    if manifest is None:
        Registry.load()
        manifest = Registry[name].manifest

    _logger.info(f"Loaded manifest {manifest.name}")
    _logger.debug(f"Hash: {manifest.hash.hexdigest()}")
    _logger.debug(f"type: {manifest.type}")
    _logger.debug(f"path: {manifest.path}")
    _logger.debug(f"description: {manifest.description}")
    _logger.debug(f"enableIf: {manifest.enableIf}")
    _logger.debug(f"alias: {manifest.alias}")
    _logger.debug(f"dependency: {manifest.dependency}")

    return manifest
