"""Centralized logging setup for the project."""

import logging


def get_logger(module_name: str) -> logging.Logger:
    """Get a configured logger for a given module name.

    Args:
        module_name (str): Name of the module or logger.

    Returns:
        logging.Logger: Configured logger instance.
    """
    logger = logging.getLogger(module_name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter("[%(asctime)s] %(levelname)s in %(name)s: %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger
