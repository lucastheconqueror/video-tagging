"""Airtable integration for VideoTagger.

Provides functions to find records by Art ID and update TagsKG column.
"""

import json
import re
from functools import lru_cache
from typing import Any

from pyairtable import Api, Table
from pyairtable.api.types import RecordDict

from videotagger.config import AirtableConfig, get_settings
from videotagger.exceptions import (
    AirtableAPIError,
    ArtIdExtractionError,
    RecordNotFoundError,
)

# Regex pattern to extract Art ID from filename
# Matches 'a' followed by digits at end of filename before extension
ART_ID_PATTERN = re.compile(r"(a\d+)\.mp4$", re.IGNORECASE)


def extract_art_id(filename: str) -> str:
    """Extract Art ID from video filename.

    Args:
        filename: Video filename like "V - something a1433.mp4"

    Returns:
        Art ID string like "a1433"

    Raises:
        ArtIdExtractionError: If Art ID cannot be found in filename.
    """
    match = ART_ID_PATTERN.search(filename)
    if not match:
        raise ArtIdExtractionError(filename)
    return match.group(1).lower()


def get_airtable_table(config: AirtableConfig | None = None) -> Table:
    """Get configured Airtable Table instance.

    Args:
        config: Optional AirtableConfig. If None, loads from Settings.

    Returns:
        Configured pyairtable Table instance.
    """
    if config is None:
        config = get_settings().airtable

    api = Api(config.api_key)
    return api.table(config.base_id, config.table_id)


@lru_cache
def get_airtable_client() -> Table:
    """Get cached Airtable Table instance.

    Returns:
        Configured pyairtable Table instance.
    """
    return get_airtable_table()


def find_by_art_id(art_id: str, table: Table | None = None) -> RecordDict:
    """Find an Airtable record by Art ID.

    Args:
        art_id: The Art ID to search for (e.g., "a1433")
        table: Optional Table instance. If None, uses default client.

    Returns:
        Record dict with 'id', 'fields', and 'createdTime'.

    Raises:
        RecordNotFoundError: If no record found with the given Art ID.
        AirtableAPIError: If the API call fails.
    """
    if table is None:
        table = get_airtable_client()

    try:
        # Use formula to find exact match on Art ID column
        formula = f"{{Art ID}} = '{art_id}'"
        record = table.first(formula=formula)

        if record is None:
            raise RecordNotFoundError(art_id)

        return record

    except RecordNotFoundError:
        raise
    except Exception as e:
        raise AirtableAPIError(f"Failed to find record: {e}", e) from e


def update_tags(art_id: str, tags: dict[str, Any], table: Table | None = None) -> RecordDict:
    """Update TagsKG column for a record identified by Art ID.

    Args:
        art_id: The Art ID of the record to update.
        tags: Dictionary of tags to store as JSON string.
        table: Optional Table instance. If None, uses default client.

    Returns:
        Updated record dict.

    Raises:
        RecordNotFoundError: If no record found with the given Art ID.
        AirtableAPIError: If the API call fails.
    """
    if table is None:
        table = get_airtable_client()

    # Find the record first
    record = find_by_art_id(art_id, table)

    try:
        # Serialize tags to JSON string
        tags_json = json.dumps(tags, ensure_ascii=False, indent=2)

        # Update the TagsKG field
        updated_record = table.update(record["id"], {"TagsKG": tags_json})
        return updated_record

    except Exception as e:
        raise AirtableAPIError(f"Failed to update record: {e}", e) from e
