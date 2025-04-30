import datetime
from collections.abc import Generator
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, call, patch

import pytest

from md_merge.merger import HEADER_TEMPLATE, SEPARATOR_TEMPLATE, merge_files

"""Unit tests for merger module."""


@pytest.fixture
def mock_file_system() -> Generator[dict[str, MagicMock | AsyncMock], Any, None]:
    """Fixture to mock file system operations."""
    with (
        patch("pathlib.Path.read_text") as mock_read_text,
        patch("pathlib.Path.write_text") as mock_write_text,
        patch("pathlib.Path.mkdir") as mock_mkdir,
    ):
        yield {"read_text": mock_read_text, "write_text": mock_write_text, "mkdir": mock_mkdir}


@pytest.fixture
def mock_logger() -> Generator[MagicMock | AsyncMock, Any, None]:
    """Fixture to mock logger."""
    with patch("md_merge.merger.logger") as mock_logger:
        yield mock_logger


def test_merge_files_happy_path(
    mock_file_system: dict[str, MagicMock | AsyncMock],
    mock_logger: MagicMock | AsyncMock,
    freezer,
) -> None:
    """Test successful merging of multiple files."""
    # Arrange
    freezer.move_to("2023-01-01 12:00:00")
    input_paths = [Path("file1.md"), Path("file2.md"), Path("file3.md")]
    output_path = Path("output.md")
    title = "Test Merged Document"

    mock_file_system["read_text"].side_effect = ["Content 1", "Content 2", "Content 3"]

    # Act
    merge_files(input_paths, output_path, title)

    # Assert
    mock_file_system["read_text"].assert_has_calls([
        call(encoding="utf-8"),
        call(encoding="utf-8"),
        call(encoding="utf-8"),
    ])

    # Check that mkdir was called with parents=True
    mock_file_system["mkdir"].assert_called_once_with(parents=True, exist_ok=True)

    # Verify the content of the merged file
    expected_timestamp = datetime.datetime(2023, 1, 1, 12, 0, 0, tzinfo=datetime.UTC).strftime(
        "%Y-%m-%d %H:%M:%S %Z"
    )
    expected_header = HEADER_TEMPLATE.format(
        final_document_title=title, timestamp=expected_timestamp, file_count=3
    )

    separator1 = SEPARATOR_TEMPLATE.safe_substitute(source_path="file2.md")
    separator2 = SEPARATOR_TEMPLATE.safe_substitute(source_path="file3.md")
    expected_content = f"{expected_header}Content 1{separator1}Content 2{separator2}Content 3"

    mock_file_system["write_text"].assert_called_once_with(expected_content, encoding="utf-8")
    mock_logger.info.assert_any_call(f"Successfully merged content into {output_path}")
    mock_logger.info.assert_any_call("Merge process completed.")


def test_merge_files_empty_input(
    mock_file_system: dict[str, MagicMock | AsyncMock], mock_logger: MagicMock | AsyncMock, freezer
) -> None:
    """Test merging with empty input list."""
    # Arrange
    freezer.move_to("2023-01-01 12:00:00")
    input_paths = []
    output_path = Path("output.md")
    title = "Empty Document"

    # Act
    merge_files(input_paths, output_path, title)

    # Assert
    mock_file_system["read_text"].assert_not_called()

    # Verify the content of the merged file
    expected_timestamp = datetime.datetime(2023, 1, 1, 12, 0, 0, tzinfo=datetime.UTC).strftime(
        "%Y-%m-%d %H:%M:%S %Z"
    )
    expected_header = HEADER_TEMPLATE.format(
        final_document_title=title, timestamp=expected_timestamp, file_count=0
    )

    mock_file_system["write_text"].assert_called_once_with(expected_header, encoding="utf-8")


def test_merge_files_single_file(
    mock_file_system: dict[str, MagicMock | AsyncMock], mock_logger: MagicMock | AsyncMock
) -> None:
    """Test merging a single file."""
    # Arrange
    input_paths = [Path("single_file.md")]
    output_path = Path("output.md")

    mock_file_system["read_text"].return_value = "Single file content"

    # Act
    merge_files(input_paths, output_path)

    # Assert
    mock_file_system["read_text"].assert_called_once_with(encoding="utf-8")

    # Check that the separator was not added (since it's only added before files except the first one)
    written_content = mock_file_system["write_text"].call_args[0][0]
    assert "Single file content" in written_content
    assert "**Source file name**" not in written_content


def test_merge_files_file_not_found(
    mock_file_system: dict[str, MagicMock | AsyncMock], mock_logger: MagicMock | AsyncMock
) -> None:
    """Test handling of FileNotFoundError."""
    # Arrange
    input_paths = [Path("existing.md"), Path("missing.md"), Path("another_existing.md")]
    output_path = Path("output.md")

    mock_file_system["read_text"].side_effect = [
        "Content 1",
        FileNotFoundError("File not found"),
        "Content 3",
    ]

    # Act
    merge_files(input_paths, output_path)

    # Assert
    mock_file_system["read_text"].assert_has_calls([
        call(encoding="utf-8"),
        call(encoding="utf-8"),
        call(encoding="utf-8"),
    ])

    # Check that the warning was logged
    mock_logger.warning.assert_called_once_with("Skipping file missing.md: Not found.")

    # Verify content still contains the existing files
    written_content = mock_file_system["write_text"].call_args[0][0]
    assert "Content 1" in written_content
    assert "Content 3" in written_content


def test_merge_files_os_error(
    mock_file_system: dict[str, MagicMock | AsyncMock], mock_logger: MagicMock | AsyncMock
) -> None:
    """Test handling of OSError."""
    # Arrange
    input_paths = [Path("file1.md"), Path("problematic.md")]
    output_path = Path("output.md")

    mock_file_system["read_text"].side_effect = ["Content 1", OSError("Permission denied")]

    # Act
    merge_files(input_paths, output_path)

    # Assert
    mock_file_system["read_text"].assert_has_calls([call(encoding="utf-8"), call(encoding="utf-8")])

    # Check that the error was logged
    mock_logger.error.assert_called_once()
    assert "due to read error" in mock_logger.error.call_args[0][0]

    # Verify content still contains the first file
    written_content = mock_file_system["write_text"].call_args[0][0]
    assert "Content 1" in written_content


@pytest.mark.xfail(raises=Exception)
def test_merge_files_unexpected_exception(
    mock_file_system: dict[str, MagicMock | AsyncMock],
) -> None:
    """Test that unexpected exceptions are propagated."""
    # Arrange
    input_paths = [Path("file.md")]
    output_path = Path("output.md")

    # Simulate an unexpected exception
    mock_file_system["read_text"].side_effect = ValueError("Unexpected error")

    # Act & Assert - should raise
    merge_files(input_paths, output_path)
