from pathlib import Path
from unittest.mock import MagicMock

import pytest

from md_merge.file_handler import MergeType, select_merge_type


def test_select_merge_type_files(mock_logger: MagicMock) -> None:
    """Test select_merge_type returns FILES when files are provided."""
    # Arrange
    files = [Path("file1.md"), Path("file2.md")]
    directory = None

    # Act
    result = select_merge_type(files, directory)

    # Assert
    assert result == MergeType.FILES
    mock_logger.debug.assert_called_once_with("Merge type selected: FILES")


def test_select_merge_type_directory(mock_logger):
    """Test select_merge_type returns DIRECTORY when directory is provided."""
    # Arrange
    files = []
    directory = Path("/some/directory")

    # Act
    result = select_merge_type(files, directory)

    # Assert
    assert result == MergeType.DIRECTORY
    mock_logger.debug.assert_called_once_with("Merge type selected: DIRECTORY")


def test_select_merge_type_no_inputs(mock_logger):
    """Test select_merge_type raises ValueError when neither files nor directory is provided."""
    # Arrange
    files = []
    directory = None

    # Act & Assert
    with pytest.raises(ValueError) as exc_info:
        select_merge_type(files, directory)

    assert str(exc_info.value) == "No valid merge type found. Please specify files or a directory."
    mock_logger.debug.assert_not_called()


def test_select_merge_type_both_inputs():
    """Test select_merge_type prioritizes files when both inputs are provided."""
    # Arrange
    files = [Path("file.md")]
    directory = Path("/some/directory")

    # Act
    result = select_merge_type(files, directory)

    # Assert
    assert result == MergeType.FILES


def test_select_merge_type_files_empty_list():
    """Test select_merge_type treats empty list as falsy."""
    # Arrange
    files = []
    directory = Path("/some/directory")

    # Act
    result = select_merge_type(files, directory)

    # Assert
    assert result == MergeType.DIRECTORY


@pytest.mark.parametrize(
    "files,directory,expected",
    [
        ([Path("file.md")], None, MergeType.FILES),
        ([Path("file1.md"), Path("file2.md")], None, MergeType.FILES),
        ([], Path("/some/dir"), MergeType.DIRECTORY),
        (None, Path("/some/dir"), MergeType.DIRECTORY),
    ],
)
def test_select_merge_type_parametrized(
    files: list[Path] | None, directory: None | Path, expected: MergeType | MergeType
) -> None:
    """Test select_merge_type with various input combinations."""
    # Act
    result = select_merge_type(files, directory)

    # Assert
    assert result == expected


def test_select_merge_type_string_representation():
    """Test string representation of MergeType enums from select_merge_type."""
    # Arrange
    files = [Path("file.md")]
    directory = Path("/some/directory")

    # Act
    files_result = select_merge_type(files, None)
    directory_result = select_merge_type([], directory)

    # Assert
    assert str(files_result) == "files"
    assert str(directory_result) == "directory"


def test_select_merge_type_enum_values():
    """Test that the MergeType enum values match expected string values."""
    # Act & Assert
    assert MergeType.FILES.value == "files"
    assert MergeType.DIRECTORY.value == "directory"


def test_select_merge_type_none_vs_empty_list():
    """Test that None and empty list are treated equivalently for files argument."""
    # Arrange & Act
    result_empty_list = select_merge_type([], Path("/some/dir"))
    result_none = select_merge_type(None, Path("/some/dir"))

    # Assert
    assert result_empty_list == result_none == MergeType.DIRECTORY


def test_select_merge_type_debug_logging_level(mock_logger):
    """Test that debug messages are logged at debug level."""
    # Arrange
    mock_logger.isEnabledFor.return_value = True
    files = [Path("file.md")]

    # Act
    select_merge_type(files, None)

    # Assert
    mock_logger.debug.assert_called_once()
    mock_logger.info.assert_not_called()
    mock_logger.warning.assert_not_called()
    mock_logger.error.assert_not_called()
