"""Custom exceptions for VideoTagger."""


class VideoTaggerError(Exception):
    """Base exception for all VideoTagger errors."""


class RecordNotFoundError(VideoTaggerError):
    """Raised when an Airtable record is not found."""

    def __init__(self, art_id: str) -> None:
        self.art_id = art_id
        super().__init__(f"No record found with Art ID: {art_id}")


class AirtableAPIError(VideoTaggerError):
    """Raised when an Airtable API call fails."""

    def __init__(self, message: str, original_error: Exception | None = None) -> None:
        self.original_error = original_error
        super().__init__(message)


class ArtIdExtractionError(VideoTaggerError):
    """Raised when Art ID cannot be extracted from filename."""

    def __init__(self, filename: str) -> None:
        self.filename = filename
        super().__init__(f"Could not extract Art ID from filename: {filename}")


class VideoProcessingError(VideoTaggerError):
    """Raised when video processing fails."""

    def __init__(self, message: str, video_path: str | None = None) -> None:
        self.video_path = video_path
        super().__init__(message)


class LLMError(VideoTaggerError):
    """Raised when LLM API call or response parsing fails."""

    def __init__(self, message: str, original_error: Exception | None = None) -> None:
        self.original_error = original_error
        super().__init__(message)
