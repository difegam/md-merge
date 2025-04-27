# Markdown Merger (md-merge)

A command-line tool to merge multiple Markdown files into a single document.

## Installation

```bash
uv pip install md-merge
```
## CLI
You can also install it using the `uv` tool, and run it directly from the command line:
```bash
uv tool install md-merge
md-merge --help
```

## Usage

```bash
# Merge specific files in order
md-merge file1.md another/file.md docs/intro.md --output combined_manual.md

# Merge all *.md files recursively from a directory (alphabetical order)
md-merge --dir path/to/markdown/docs --output full_docs.md

# Specify a different output file
md-merge file.md --output my_merged_file.md

# Enable verbose logging for debugging
mdmerge --dir my_project --verbose

# Get help
md-merge --help
```

## Features
- Merges specified files or all .md files in a directory.
- Inserts a separator between files showing the source path.
- Adds a header to the merged document with timestamp and file count.
- Preserves YAML front matter (from the first file only).
- Configurable output file path (default: merged.md).
- Verbose logging option (--verbose or -v).
- Robust error handling and validation.


## Future Improvements
- Add support for custom separators.
- Implement a GUI for easier file selection.
- Support for other file formats (e.g., .txt, .rst).
- Add unit tests for better coverage.
