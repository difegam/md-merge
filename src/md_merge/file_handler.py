"""Handles file and directory path operations."""

import logging
from enum import Enum
from pathlib import Path

from md_merge.exceptions import (
    DirectoryNotFoundError,
    FileNotFoundError,
    FileProcessingError,
    NotADirectoryError,
    NotAFileError,
    NotMarkdownFileError,
)

logger = logging.getLogger(__name__)


class MergeType(Enum):
    """Enum for merge options."""

    FILES = "files"
    DIRECTORY = "directory"

    def __str__(self) -> str:
        return self.value


def find_markdown_files(directory: Path) -> list[Path]:
    logger.debug(f"Searching for markdown files in directory: {directory}")
    if not directory.exists():
        raise DirectoryNotFoundError(f"Directory not found: {directory}")
    if not directory.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {directory}")

    try:
        # Use rglob to find all markdown files in the directory
        md_files = sorted(directory.rglob("*.md"))
        logger.info(f"Found {len(md_files)} markdown files in {directory}.")

        # Debug logging for found files
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Found markdown files: {'\n'.join([f'- {file!s}' for file in md_files])}")

        return md_files

    except Exception as e:
        logger.error(f"Error finding markdown files in {directory}: {e}", exc_info=True)
        raise FileProcessingError(f"Failed to find markdown files in {directory}: {e}") from e


def validate_inputs(files: list[Path], directory: Path) -> None:
    logger.debug("Validating input files and directory.")
    if files and directory:
        raise ValueError("Cannot specify both individual files and a directory.")
    if not files and not directory:
        raise ValueError("Must specify either individual files or a directory.")

    logger.debug("Input validation passed.")


def select_merge_type(files: list[Path], directory: Path) -> MergeType:
    """Determine the merge type based on user input."""
    if files:
        logger.debug("Merge type selected: FILES")
        return MergeType.FILES
    if directory:
        logger.debug("Merge type selected: DIRECTORY")
        return MergeType.DIRECTORY
    raise ValueError("No valid merge type found. Please specify files or a directory.")


def validate_input_directory(directory: Path) -> None:
    logger.debug(f"Validating directory path: {directory}")
    if not directory.exists():
        raise DirectoryNotFoundError(f"Directory not found: {directory}")
    if not directory.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {directory}")
    logger.debug("Directory path is valid.")


def validate_input_files(files: list[Path]) -> None:
    logger.debug(f"Validating {len(files)} input file paths.")
    for file_path in files:
        if not file_path.exists():
            raise FileNotFoundError(f"Input file not found: {file_path}")

        # Check if the path is a file
        if not file_path.is_file():
            raise NotAFileError(f"Input path is not a file: {file_path}")

        # Check if the file has a .md extension
        if file_path.suffix != ".md":
            raise NotMarkdownFileError(f"Input file is not a markdown file: {file_path}")
        logger.debug(f"  - Validated: {file_path}")
    logger.debug("All input file paths are valid.")
