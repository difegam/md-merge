"""Core logic for merging Markdown files."""

import datetime
import logging
from pathlib import Path
from string import Template

from md_merge import logger as md_logger
from md_merge.exceptions import FileProcessingError

logger = logging.getLogger(__name__)
md_logger.setup_logging(logging.INFO)

SEPARATOR_TEMPLATE = Template(
    """
\n
---
**Source file name**: ${source_path}
---
\n
"""
)
HEADER_TEMPLATE = """# {final_document_title}

<details>
<summary>Metadata</summary>

- *Merged from*: {final_document_title}
- *Generated at*: {timestamp}
- *Source files*: {file_count}

</details>

"""


def merge_files(
    input_paths: list[Path], output_path: Path, final_document_title: str = "Merged Markdown File"
) -> None:
    total_files = len(input_paths)
    logger.info(
        f"Starting merge process. Creating '{final_document_title.title()}' \
            from {total_files} files."
    )

    merged_content_parts = []

    for file_index, source_path in enumerate(input_paths):
        logger.info(f"Processing file ({file_index + 1}/{total_files}): {source_path.name}")
        try:
            file_content = source_path.read_text(encoding="utf-8")
            logger.debug(f"Read {len(file_content)} characters from {source_path}")

            # Add separator before files except the first one
            if file_index > 0:
                separator = SEPARATOR_TEMPLATE.safe_substitute(source_path=source_path.name)
                merged_content_parts.append(separator)

            merged_content_parts.append(file_content)

        except FileNotFoundError:
            logger.warning(f"Skipping file {source_path}: Not found.")
        except OSError as e:
            logger.error(f"Skipping file {source_path} due to read error: {e}", exc_info=False)
        except Exception as e:
            logger.error(f"Skipping file {source_path} due to unexpected error: {e}", exc_info=True)
            raise FileProcessingError(f"Unexpected error reading file {source_path}: {e}") from e

    # Construct the final document
    timestamp = datetime.datetime.now(tz=datetime.UTC).strftime("%Y-%m-%d %H:%M:%S %Z")
    header = HEADER_TEMPLATE.format(
        final_document_title=final_document_title,
        timestamp=timestamp,
        file_count=total_files,
    )

    final_content = header
    final_content += "".join(merged_content_parts)

    write_merged_output(output_path, final_content)


def write_merged_output(output_path: Path, content: str) -> None:
    logger.debug(f"Writing merged content to {output_path}")
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")
        logger.info(f"Successfully merged content into {output_path}")
    except OSError as e:
        logger.critical(f"Failed to write merged output to {output_path}: {e}", exc_info=True)
        raise FileProcessingError(f"Error writing output file {output_path}: {e}") from e
    except Exception as e:
        logger.critical(
            f"Failed to write merged output to {output_path} due to unexpected error: {e}",
            exc_info=True,
        )
        raise FileProcessingError(f"Unexpected error writing output file {output_path}: {e}") from e
    logger.info("Merge process completed.")
