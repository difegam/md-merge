"""Common test fixtures for md_merge tests."""

import logging
from collections.abc import Callable, Generator
from pathlib import Path
from typing import TypeAlias, TypedDict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from _pytest.logging import LogCaptureFixture
from freezegun import freeze_time

from md_merge.exceptions import (
    DirectoryNotFoundError,
    FileNotFoundError,
    NotADirectoryError,
    NotAFileError,
    NotMarkdownFileError,
)

# Type aliases for improved readability
MockDict: TypeAlias = dict[str, MagicMock | AsyncMock]
LoggerCallable: TypeAlias = Callable[[str, int], bool]


class MockFileSystem(TypedDict):
    """Type for mocked filesystem objects."""

    read_text: MagicMock | AsyncMock
    write_text: MagicMock | AsyncMock
    mkdir: MagicMock | AsyncMock


@pytest.fixture
def freezer():
    """Provide a fixture for freezegun time freezing.

    Returns:
        freezegun.api.freeze_time: A freezegun time freezer
    """
    with freeze_time() as freezer:
        yield freezer


@pytest.fixture
def mock_logger() -> Generator[MagicMock, None, None]:
    """Mock the logger to avoid actual logging during tests.

    Returns:
        MagicMock: The mocked logger instance
    """
    with (
        patch("md_merge.file_handler.logger") as mock_handler_logger,
        patch("md_merge.merger.logger") as mock_merger_logger,
    ):
        # Configure the mock to work with standard logging methods
        for logger in [mock_handler_logger, mock_merger_logger]:
            logger.isEnabledFor.return_value = True

        # Return the file handler logger for now as it's most commonly used
        yield mock_handler_logger


@pytest.fixture
def mock_file_system() -> Generator[MockFileSystem, None, None]:
    """Mock file system operations for tests.

    Returns:
        MockFileSystem: Dictionary of mocked file system operations
    """
    with (
        patch("pathlib.Path.read_text") as mock_read_text,
        patch("pathlib.Path.write_text") as mock_write_text,
        patch("pathlib.Path.mkdir") as mock_mkdir,
    ):
        yield {"read_text": mock_read_text, "write_text": mock_write_text, "mkdir": mock_mkdir}


@pytest.fixture
def sample_markdown_files() -> list[Path]:
    """Create a list of sample markdown file paths.

    Returns:
        List[Path]: A list containing sample markdown file paths
    """
    return [Path("file1.md"), Path("file2.md"), Path("subfolder/file3.md")]


@pytest.fixture
def sample_non_markdown_files() -> list[Path]:
    """Create a list of sample non-markdown file paths.

    Returns:
        List[Path]: A list containing sample non-markdown file paths
    """
    return [Path("file1.txt"), Path("file2.py"), Path("image.png")]


@pytest.fixture
def sample_directory() -> Path:
    """Return a sample directory path.

    Returns:
        Path: A sample directory path
    """
    return Path("/some/directory")


@pytest.fixture
def tmp_md_files(tmp_path) -> list[Path]:
    """Create temporary markdown files for testing.

    Args:
        tmp_path: Pytest's built-in tmp_path fixture

    Returns:
        List[Path]: A list of real temporary markdown files
    """
    md_files = []

    # Create markdown files in the temp directory
    for i in range(3):
        md_file = tmp_path / f"test{i}.md"
        md_file.write_text(f"# Test file {i}\n\nThis is test content for file {i}.")
        md_files.append(md_file)

    # Create a subfolder with markdown files
    subdir = tmp_path / "subdir"
    subdir.mkdir()
    for i in range(2):
        md_file = subdir / f"subtest{i}.md"
        md_file.write_text(f"# Subdir test file {i}\n\nThis is test content in subdirectory.")
        md_files.append(md_file)

    return md_files


@pytest.fixture
def mock_path_validation() -> Generator[None, None, None]:
    """Mock all path validation functions to avoid filesystem operations.

    This fixture patches the common path validation methods in the Path class.
    """
    with (
        patch("pathlib.Path.exists") as mock_exists,
        patch("pathlib.Path.is_file") as mock_is_file,
        patch("pathlib.Path.is_dir") as mock_is_dir,
    ):
        mock_exists.return_value = True
        mock_is_file.return_value = True
        mock_is_dir.return_value = True
        yield


@pytest.fixture
def file_processing_exceptions() -> dict:
    """Return a dictionary of file processing exceptions for easier testing.

    Returns:
        dict: A dictionary mapping exception names to exception classes
    """
    return {
        "file_not_found": FileNotFoundError,
        "dir_not_found": DirectoryNotFoundError,
        "not_a_file": NotAFileError,
        "not_a_dir": NotADirectoryError,
        "not_markdown": NotMarkdownFileError,
    }


@pytest.fixture
def assert_log_message(caplog: LogCaptureFixture) -> LoggerCallable:
    """Return a helper function to assert log messages.

    Args:
        caplog: Pytest's built-in caplog fixture

    Returns:
        callable: A function to assert log messages
    """

    def _assert_log(message: str, level: int = logging.DEBUG) -> bool:
        """Assert if a specific message was logged at the given level.

        Args:
            message: The message to check for
            level: The logging level to check (default: DEBUG)

        Returns:
            bool: True if the message was found, False otherwise
        """
        return any(
            record.levelno == level and message in record.getMessage() for record in caplog.records
        )

    return _assert_log
