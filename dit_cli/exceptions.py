"""All Exceptions used by dit_cli"""


class DitError(Exception):
    """Base Class for all dit exceptions"""

    def __init__(self, prepend, message):
        super().__init__(prepend + ': ' + message)


class FormatError(DitError):
    """Raised when the file has an illegal style or structure"""

    def __init__(self, message):
        super().__init__('FormatError', message)


class ValidationError(DitError):
    """Raised when anything goes wrong during validation of a dit"""

    def __init__(self, message, name):
        super().__init__(f'ValidationError<{name}>', message)


class ParseError(DitError):
    """Raised when there anything goes wrong during paring the file"""

    def __init__(self, message):
        super().__init__('ParseError', message)


class TreeError(DitError):
    """Raised when anything goes wrong with tree functions"""

    def __init__(self, message):
        super().__init__('TreeError', message)
