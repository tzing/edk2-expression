class Error(Exception):
    """Base class for exceptions in this module."""


class ParseError(Error):
    """Exception raised when expression parsing failed."""


class NotSupported(Error):
    """Exception raised when the operation is not supported."""


class EvaluationError(Error):
    """Exception raised when expression evaluation failed."""
