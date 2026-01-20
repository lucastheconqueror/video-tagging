"""Tests for Airtable integration."""

from unittest.mock import MagicMock

import pytest

from videotagger.airtable import extract_art_id, find_by_art_id, update_tags
from videotagger.exceptions import ArtIdExtractionError, RecordNotFoundError


class TestExtractArtId:
    """Tests for Art ID extraction from filenames."""

    def test_extracts_art_id_from_valid_filename(self) -> None:
        """Test extraction from standard filename format."""
        result = extract_art_id("V - some video a1433.mp4")
        assert result == "a1433"

    def test_extracts_long_art_id(self) -> None:
        """Test extraction of longer Art ID."""
        result = extract_art_id("V - another video a13332.mp4")
        assert result == "a13332"

    def test_handles_uppercase_extension(self) -> None:
        """Test extraction with uppercase MP4 extension."""
        result = extract_art_id("V - video a999.MP4")
        assert result == "a999"

    def test_returns_lowercase_art_id(self) -> None:
        """Test that Art ID is normalized to lowercase."""
        result = extract_art_id("V - video A1234.mp4")
        assert result == "a1234"

    def test_raises_error_for_invalid_filename(self) -> None:
        """Test that invalid filename raises ArtIdExtractionError."""
        with pytest.raises(ArtIdExtractionError) as exc_info:
            extract_art_id("invalid_filename.mp4")
        assert "invalid_filename.mp4" in str(exc_info.value)

    def test_raises_error_for_missing_art_id(self) -> None:
        """Test filename without Art ID pattern."""
        with pytest.raises(ArtIdExtractionError):
            extract_art_id("V - video without id.mp4")


class TestFindByArtId:
    """Tests for finding records by Art ID."""

    def test_returns_record_when_found(self) -> None:
        """Test successful record lookup."""
        mock_table = MagicMock()
        mock_record = {
            "id": "rec123",
            "fields": {"Art ID": "a1433", "TagsKG": ""},
            "createdTime": "2024-01-01T00:00:00.000Z",
        }
        mock_table.first.return_value = mock_record

        result = find_by_art_id("a1433", table=mock_table)

        assert result == mock_record
        mock_table.first.assert_called_once_with(formula="{Art ID} = 'a1433'")

    def test_raises_error_when_not_found(self) -> None:
        """Test RecordNotFoundError when no record matches."""
        mock_table = MagicMock()
        mock_table.first.return_value = None

        with pytest.raises(RecordNotFoundError) as exc_info:
            find_by_art_id("a9999", table=mock_table)

        assert exc_info.value.art_id == "a9999"


class TestUpdateTags:
    """Tests for updating TagsKG column."""

    def test_updates_tags_successfully(self) -> None:
        """Test successful tag update."""
        mock_table = MagicMock()
        mock_record = {"id": "rec123", "fields": {"Art ID": "a1433"}}
        mock_updated = {"id": "rec123", "fields": {"Art ID": "a1433", "TagsKG": "{}"}}

        mock_table.first.return_value = mock_record
        mock_table.update.return_value = mock_updated

        tags = {"location": "Gym", "mood": "Energetic"}
        result = update_tags("a1433", tags, table=mock_table)

        assert result == mock_updated
        mock_table.update.assert_called_once()
        # Verify the TagsKG field contains JSON
        call_args = mock_table.update.call_args
        assert call_args[0][0] == "rec123"
        assert "TagsKG" in call_args[0][1]

    def test_raises_error_when_record_not_found(self) -> None:
        """Test that update fails gracefully when record doesn't exist."""
        mock_table = MagicMock()
        mock_table.first.return_value = None

        with pytest.raises(RecordNotFoundError):
            update_tags("a9999", {"test": "data"}, table=mock_table)
