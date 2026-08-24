class DatabaseLoadError(Exception):
    """Raised when the database load step fails."""


class QualityValidationError(Exception):
    """Raised when a data quality validation check fails."""
