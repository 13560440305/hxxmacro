import logging
import os
from logging.handlers import RotatingFileHandler


def setup_logger(name: str, config: dict = None):
    if config is None:
        config = {}

    # Determine log directory relative to this file
    base_dir = os.path.dirname(__file__)
    log_dir = config.get("dir", "../logs")
    log_dir = os.path.normpath(os.path.join(base_dir, log_dir))
    os.makedirs(log_dir, exist_ok=True)

    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    level_name = config.get("level", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    logger.setLevel(level)

    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    # Rotation parameters (configurable)
    rotation = config.get("rotation", {}) if isinstance(config, dict) else {}
    max_bytes = rotation.get("max_bytes", 5 * 1024 * 1024)
    backup_count = rotation.get("backup_count", 5)

    # File handler with rotation
    file_path = os.path.join(log_dir, f"{name}.log")
    fh = RotatingFileHandler(file_path, maxBytes=int(max_bytes), backupCount=int(backup_count), encoding="utf-8")
    fh.setLevel(level)
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    if config.get("console", True):
        ch = logging.StreamHandler()
        ch.setLevel(level)
        ch.setFormatter(fmt)
        logger.addHandler(ch)

    return logger
