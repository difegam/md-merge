"""Command Line Interface definition using argparse."""

import argparse
import logging
import sys
from enum import Enum
from pathlib import Path
from uuid import uuid4

from md_merge import file_handler, merger
from md_merge import logger as md_logger
from md_merge.exceptions import (
    DirectoryNotFoundError,
    FileNotFoundError,
    FileProcessingError,
    MdMergeError,
    NotADirectoryError,
    NotAFileError,
    ValidationError,
)

# Get a logger instance for this module
logger = logging.getLogger(__name__)


def set_logging_level(value: bool) -> None:
    """Sets the logging level based on the --verbose flag."""
    if value:
        md_logger.setup_logging(logging.DEBUG)
        logger.info("Verbose logging enabled.")
    else:
        md_logger.setup_logging(logging.INFO)


def generate_dft_output_path() -> Path:
    """Generate a default output path for the merged file."""
    return Path.cwd() / f"md-merge-{uuid4()}.md"


def setup_command_line_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser.

    Returns:
        argparse.ArgumentParser: Configured argument parser
    """
    parser = argparse.ArgumentParser(
        prog="md-merge",
        description="A CLI tool to merge multiple Markdown files into a single document.",
    )

    # Files argument
    parser.add_argument(
        "files",
        nargs="*",
        type=Path,
        help="Paths to individual Markdown files to merge (in order).",
    )

    # Directory option
    parser.add_argument(
        "--dir",
        "-d",
        dest="directory",
        type=Path,
        help="Path to a directory. Recursively finds and merges all '.md' files alphabetically.",
    )

    # Output option
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=generate_dft_output_path(),
        help="Path for the merged output Markdown file.",
    )

    # Verbose option
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose (DEBUG level) logging."
    )

    return parser


class ErrorCode(Enum):
    """Enum for error codes."""

    SUCCESS = 0
    VALIDATION_ERROR = 1
    FILE_DIRECTORY_ERROR = 2
    FILE_PROCESSING_ERROR = 3
    APPLICATION_ERROR = 4
    UNEXPECTED_ERROR = 10


error_messages = {
    ErrorCode.SUCCESS: "Success",
    ErrorCode.VALIDATION_ERROR: "Validation error occurred. {error}",
    ErrorCode.FILE_DIRECTORY_ERROR: "File/directory error occurred. {error}",
    ErrorCode.FILE_PROCESSING_ERROR: "Error processing file. {error}",
    ErrorCode.APPLICATION_ERROR: "Application error occurred. {error}",
    ErrorCode.UNEXPECTED_ERROR: "An unexpected error occurred. {error}",
}


def exit_on_cli_error(error_code: ErrorCode, error: Exception) -> None:
    logger.error(error_messages[error_code].format(error=error), exc_info=False)
    sys.exit(error_code.value)


def main() -> None:
    """Main function to handle command-line arguments and execute the merging process."""
    # Set up the argument parser
    parser = setup_command_line_parser()
    args = parser.parse_args()

    # Set up logging based on verbosity
    set_logging_level(args.verbose)

    input_paths: list[Path] = []

    try:
        # Validate inputs
        file_handler.validate_inputs(args.files, args.directory)

        operation_mode = file_handler.select_merge_type(args.files, args.directory)

        if operation_mode == file_handler.MergeType.FILES:
            logger.info("Mode: Explicit files")
            file_handler.validate_input_files(args.files)
            input_paths = args.files
        elif operation_mode == file_handler.MergeType.DIRECTORY:
            logger.info("Mode: Directory")
            file_handler.validate_input_directory(args.directory)
            input_paths = file_handler.find_markdown_files(args.directory)

        # Check if any files were found
        if not input_paths:
            logger.warning(f"No '.md' files found in directory {args.directory}. Nothing to merge.")
            return

        # Merge files
        merger.merge_files(input_paths, args.output)

    except (ValidationError, ValueError) as e:
        exit_on_cli_error(ErrorCode.VALIDATION_ERROR, e)
    except (FileNotFoundError, NotAFileError, DirectoryNotFoundError, NotADirectoryError) as e:
        exit_on_cli_error(ErrorCode.FILE_DIRECTORY_ERROR, e)
    except FileProcessingError as e:
        exit_on_cli_error(ErrorCode.FILE_PROCESSING_ERROR, e)
    except MdMergeError as e:  # Catch base custom error
        exit_on_cli_error(ErrorCode.APPLICATION_ERROR, e)
    except Exception as e:  # Catch-all for unexpected errors
        exit_on_cli_error(ErrorCode.UNEXPECTED_ERROR, e)

    logger.info("md-merge process completed successfully.")
    logger.info(f"Successfully merged {len(input_paths)} file(s) into {args.output}")


if __name__ == "__main__":
    main()
