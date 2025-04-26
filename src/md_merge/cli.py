"""Command Line Interface definition using argparse."""

import argparse
import logging
import sys
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


def create_parser() -> argparse.ArgumentParser:
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


def main() -> int:
    """Execute the main CLI logic.

    Returns:
        int: Exit code
    """
    parser = create_parser()
    args = parser.parse_args()

    # Set up logging based on verbosity
    set_logging_level(args.verbose)

    input_paths: list[Path] = []

    try:
        # --- Input Validation ---
        file_handler.validate_inputs(args.files, args.directory)

        # --- Determine Mode and Get Input Paths ---
        if args.files:
            logger.info("Mode: Explicit files")
            file_handler.validate_input_files(args.files)
            input_paths = args.files
        elif args.directory:
            logger.info("Mode: Directory")
            input_paths = file_handler.find_markdown_files(args.directory)
            if not input_paths:
                logger.warning(
                    f"No '.md' files found in directory {args.directory}. Nothing to merge."
                )
                return 0

        # --- Perform Merge Operation ---
        merger.merge_files(input_paths, args.output)

    except (ValidationError, ValueError) as e:
        logger.error(f"Validation Error: {e}", exc_info=False)
        return 1
    except (FileNotFoundError, NotAFileError, DirectoryNotFoundError, NotADirectoryError) as e:
        logger.error(f"File/Directory Error: {e}", exc_info=False)
        return 2
    except FileProcessingError as e:
        logger.error(f"File Processing Error: {e}", exc_info=True)
        return 3
    except MdMergeError as e:  # Catch base custom error
        logger.error(f"Application Error: {e}", exc_info=True)
        return 4
    except Exception as e:  # Catch-all for unexpected errors
        logger.critical(f"An unexpected error occurred: {e}", exc_info=True)
        return 10

    logger.info("md-merge process completed successfully.")
    print(f"Successfully merged {len(input_paths)} file(s) into {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
