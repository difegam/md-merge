"""Custom exceptions for the md-merge application."""


class MdMergeError(Exception):
    """Base exception for md-merge errors."""


class ValidationError(MdMergeError):
    """Exception raised for validation errors (e.g., invalid CLI args)."""


class FileProcessingError(MdMergeError):
    """Exception raised during file reading or writing."""


class FileNotFoundError(FileProcessingError):
    """Specific exception for files not found."""


class DirectoryNotFoundError(FileProcessingError):
    """Specific exception for directories not found."""


class NotAFileError(FileProcessingError):
    """Exception raised when a path is expected to be a file but isn't."""


class NotMarkdownFileError(FileProcessingError):
    """Exception raised when a file is not a markdown file."""


class NotADirectoryError(FileProcessingError):
    """Exception raised when a path is expected to be a directory but isn't."""
