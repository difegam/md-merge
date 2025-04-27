"""
Logging configuration for the md-merge application.

This module sets up the logging configuration for the application, allowing
for different logging levels and formats. It also provides a function to
get a logger instance for use in other modules.

# Example of getting a logger instance in other modules:
# import logging
# logger = logging.getLogger(__name__)
"""

import logging
import sys
from typing import Annotated

LibraryFilterList = Annotated[list[str] | None, "List of libraries to silence"]


def setup_logging(level: int = logging.INFO, silence_libraries: LibraryFilterList = None) -> None:
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    # Use StreamHandler to output to stderr to separate from potential stdout output
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter(log_format, datefmt=date_format))

    # Configure root logger
    root_logger = logging.getLogger()

    # Remove existing handlers to avoid duplicates if called multiple times
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    root_logger.setLevel(level)
    root_logger.addHandler(handler)

    # Optionally silence overly verbose libraries if needed
    if silence_libraries:
        for library in silence_libraries:
            logging.getLogger(library).setLevel(logging.WARNING)

    logger = logging.getLogger(__name__)
    logger.debug(
        f"Logging initialized with level {logging.getLevelName(level)}",
    )
