"""Custom exception hierarchy for the chiller intelligence pipeline.

All pipeline-specific errors inherit from ChillerPipelineError
to enable targeted exception handling at each boundary.
"""


class ChillerPipelineError(Exception):
    """Base exception for all chiller pipeline errors."""


class SchemaValidationError(ChillerPipelineError):
    """Raised when the input CSV does not match the expected schema."""


class DataQualityError(ChillerPipelineError):
    """Raised when data quality checks fail (duplicates, corrupt values)."""


class PreprocessingError(ChillerPipelineError):
    """Raised when preprocessing encounters an unrecoverable issue."""


class TrainingError(ChillerPipelineError):
    """Raised when model training fails."""


class PredictionError(ChillerPipelineError):
    """Raised when inference/prediction encounters an error."""
