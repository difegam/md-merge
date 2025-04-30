import logging
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

from md_merge.cli import (
    ErrorCode,
    exit_on_cli_error,
    generate_dft_output_path,
    main,
    set_logging_level,
    setup_command_line_parser,
)
from md_merge.exceptions import (
    DirectoryNotFoundError,
    FileNotFoundError,
    FileProcessingError,
    MdMergeError,
    NotADirectoryError,
    NotAFileError,
    ValidationError,
)
from md_merge.file_handler import MergeType


@pytest.fixture
def mock_file_handler() -> MagicMock:
    """Mock the file_handler module."""
    with patch("md_merge.cli.file_handler") as mock:
        mock.MergeType = MergeType  # Keep the real enum
        yield mock


@pytest.fixture
def mock_merger() -> MagicMock:
    """Mock the merger module."""
    with patch("md_merge.cli.merger") as mock:
        yield mock


@pytest.fixture
def mock_logger() -> MagicMock:
    """Mock the logger."""
    with patch("md_merge.cli.logger") as mock:
        yield mock


@pytest.fixture
def mock_md_logger() -> MagicMock:
    """Mock the md_logger module."""
    with patch("md_merge.cli.md_logger") as mock:
        yield mock


@pytest.fixture
def mock_sys_exit() -> MagicMock:
    """Mock sys.exit to prevent test exit."""
    with patch("sys.exit") as mock:
        yield mock


@pytest.fixture
def mock_uuid() -> MagicMock:
    """Mock uuid4 for predictable output paths."""
    with patch("md_merge.cli.uuid4") as mock:
        mock.return_value = "test-uuid"
        yield mock


def test_setup_command_line_parser() -> None:
    """Test the argument parser setup."""
    parser = setup_command_line_parser()

    assert parser.prog == "md-merge"

    # Get all argument names
    arg_actions = {action.dest for action in parser._actions if action.dest != "help"}
    expected_args = {"files", "directory", "output", "verbose"}

    assert arg_actions == expected_args


def test_set_logging_level_verbose(mock_md_logger: MagicMock, mock_logger: MagicMock) -> None:
    """Test setting verbose logging level."""

    set_logging_level(True)

    mock_md_logger.setup_logging.assert_called_once_with(logging.DEBUG)
    mock_logger.info.assert_called_once_with("Verbose logging enabled.")


def test_set_logging_level_normal(mock_md_logger: MagicMock, mock_logger: MagicMock) -> None:
    """Test setting normal logging level."""

    set_logging_level(False)

    mock_md_logger.setup_logging.assert_called_once_with(logging.INFO)
    mock_logger.info.assert_not_called()


def test_generate_dft_output_path(mock_uuid: MagicMock) -> None:
    """Test default output path generation."""
    path = generate_dft_output_path()

    assert path == Path.cwd() / "md-merge-test-uuid.md"


def test_exit_on_cli_error(mock_logger: MagicMock, mock_sys_exit: MagicMock) -> None:
    """Test error exit handling."""
    error = ValueError("Test error")
    exit_on_cli_error(ErrorCode.VALIDATION_ERROR, error)

    mock_logger.error.assert_called_once_with(
        "Validation error occurred. Test error", exc_info=False
    )
    mock_sys_exit.assert_called_once_with(1)


@patch("md_merge.cli.setup_command_line_parser")
def test_main_files_mode_success(
    mock_parser: MagicMock,
    mock_file_handler: MagicMock,
    mock_merger: MagicMock,
    mock_logger: MagicMock,
    mock_sys_exit: MagicMock,
) -> None:
    """Test successful execution with files mode."""
    # Set up mocks
    mock_args = MagicMock()
    mock_args.files = [Path("file1.md"), Path("file2.md")]
    mock_args.directory = None
    mock_args.output = Path("output.md")
    mock_args.verbose = False

    mock_parser.return_value.parse_args.return_value = mock_args

    mock_file_handler.select_merge_type.return_value = MergeType.FILES

    # Execute
    main()

    # Verify
    mock_file_handler.validate_inputs.assert_called_once_with(mock_args.files, mock_args.directory)
    mock_file_handler.validate_input_files.assert_called_once_with(mock_args.files)
    mock_merger.merge_files.assert_called_once_with(mock_args.files, mock_args.output)

    mock_logger.info.assert_has_calls([
        call("Mode: Explicit files"),
        call("md-merge process completed successfully."),
        call(f"Successfully merged {len(mock_args.files)} file(s) into {mock_args.output}"),
    ])
    mock_sys_exit.assert_not_called()


@patch("md_merge.cli.setup_command_line_parser")
def test_main_directory_mode_success(
    mock_parser: MagicMock,
    mock_file_handler: MagicMock,
    mock_merger: MagicMock,
    mock_logger: MagicMock,
) -> None:
    """Test successful execution with directory mode."""
    # Set up mocks
    mock_args = MagicMock()
    mock_args.files = []
    mock_args.directory = Path("test_dir")
    mock_args.output = Path("output.md")
    mock_args.verbose = False

    mock_parser.return_value.parse_args.return_value = mock_args

    mock_file_handler.select_merge_type.return_value = MergeType.DIRECTORY
    found_files = [Path("test_dir/file1.md"), Path("test_dir/file2.md")]
    mock_file_handler.find_markdown_files.return_value = found_files

    # Execute
    main()

    # Verify
    mock_file_handler.validate_inputs.assert_called_once_with(mock_args.files, mock_args.directory)
    mock_file_handler.validate_input_directory.assert_called_once_with(mock_args.directory)
    mock_file_handler.find_markdown_files.assert_called_once_with(mock_args.directory)
    mock_merger.merge_files.assert_called_once_with(found_files, mock_args.output)

    mock_logger.info.assert_has_calls([
        call("Mode: Directory"),
        call("md-merge process completed successfully."),
        call(f"Successfully merged {len(found_files)} file(s) into {mock_args.output}"),
    ])


@patch("md_merge.cli.setup_command_line_parser")
def test_main_directory_no_files_found(
    mock_parser: MagicMock,
    mock_file_handler: MagicMock,
    mock_merger: MagicMock,
    mock_logger: MagicMock,
) -> None:
    """Test directory mode with no files found."""
    # Set up mocks
    mock_args = MagicMock()
    mock_args.files = []
    mock_args.directory = Path("empty_dir")
    mock_args.output = Path("output.md")
    mock_args.verbose = False

    mock_parser.return_value.parse_args.return_value = mock_args

    mock_file_handler.select_merge_type.return_value = MergeType.DIRECTORY
    mock_file_handler.find_markdown_files.return_value = []

    # Execute
    main()

    # Verify
    mock_file_handler.validate_inputs.assert_called_once_with(mock_args.files, mock_args.directory)
    mock_file_handler.validate_input_directory.assert_called_once_with(mock_args.directory)
    mock_merger.merge_files.assert_not_called()

    mock_logger.warning.assert_called_once_with(
        f"No '.md' files found in directory {mock_args.directory}. Nothing to merge."
    )


@pytest.mark.parametrize(
    "exception,error_code,exit_code",
    [
        (ValidationError("Bad input"), ErrorCode.VALIDATION_ERROR, 1),
        (ValueError("Invalid value"), ErrorCode.VALIDATION_ERROR, 1),
        (FileNotFoundError("Missing file"), ErrorCode.FILE_DIRECTORY_ERROR, 2),
        (NotAFileError("Not a file"), ErrorCode.FILE_DIRECTORY_ERROR, 2),
        (DirectoryNotFoundError("Missing dir"), ErrorCode.FILE_DIRECTORY_ERROR, 2),
        (NotADirectoryError("Not a dir"), ErrorCode.FILE_DIRECTORY_ERROR, 2),
        (FileProcessingError("Process error"), ErrorCode.FILE_PROCESSING_ERROR, 3),
        (MdMergeError("App error"), ErrorCode.APPLICATION_ERROR, 4),
        (Exception("Unexpected error"), ErrorCode.UNEXPECTED_ERROR, 10),
    ],
)
@patch("md_merge.cli.setup_command_line_parser")
def test_main_error_handling(
    mock_parser: MagicMock,
    exception: Exception,
    error_code: ErrorCode,
    exit_code: int,
    mock_file_handler: MagicMock,
    mock_logger: MagicMock,
    mock_sys_exit: MagicMock,
) -> None:
    """Test error handling for various exceptions."""
    # Set up mocks
    mock_args = MagicMock()
    mock_args.files = [Path("file1.md")]
    mock_args.directory = None
    mock_args.output = Path("output.md")
    mock_args.verbose = False

    mock_parser.return_value.parse_args.return_value = mock_args

    # Configure mock to raise the exception
    mock_file_handler.validate_inputs.side_effect = exception

    # Execute
    main()

    # Verify
    mock_logger.error.assert_called_once()
    mock_sys_exit.assert_called_once_with(exit_code)


@patch("md_merge.cli.setup_command_line_parser")
def test_main_with_custom_title(
    mock_parser: MagicMock,
    mock_file_handler: MagicMock,
    mock_merger: MagicMock,
) -> None:
    """Test passing custom title to merger."""
    # Set up mocks
    mock_args = MagicMock()
    mock_args.files = [Path("file1.md")]
    mock_args.directory = None
    mock_args.output = Path("output.md")
    mock_args.verbose = False

    mock_parser.return_value.parse_args.return_value = mock_args

    mock_file_handler.select_merge_type.return_value = MergeType.FILES

    # Execute
    main()

    # Verify merger was called with default title (None)
    mock_merger.merge_files.assert_called_once_with(mock_args.files, mock_args.output)


@patch("md_merge.cli.argparse.ArgumentParser.parse_args")
def test_main_integration_with_args(
    mock_parse_args: MagicMock,
    mock_file_handler: MagicMock,
    mock_merger: MagicMock,
) -> None:
    """Test main function with simulated command line arguments."""
    # Set up mock
    mock_args = MagicMock()
    mock_args.files = [Path("file1.md"), Path("file2.md")]
    mock_args.directory = None
    mock_args.output = Path("output.md")
    mock_args.verbose = True

    mock_parse_args.return_value = mock_args

    mock_file_handler.select_merge_type.return_value = MergeType.FILES

    # Execute
    with patch("md_merge.cli.md_logger.setup_logging") as mock_setup_logging:
        main()

        # Verify
        mock_setup_logging.assert_called_once_with(logging.DEBUG)
        mock_file_handler.validate_input_files.assert_called_once_with(mock_args.files)
        mock_merger.merge_files.assert_called_once_with(mock_args.files, mock_args.output)
