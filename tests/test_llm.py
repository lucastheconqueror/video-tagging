"""Tests for LLM client."""

from unittest.mock import MagicMock, patch

import pytest

from videotagger.exceptions import LLMError
from videotagger.llm import build_vision_messages, parse_tags_response


class TestBuildVisionMessages:
    """Tests for building vision API messages."""

    def test_includes_system_prompt(self) -> None:
        """Test that system prompt is included."""
        messages = build_vision_messages(["base64data"])

        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert "video content tagger" in messages[0]["content"]

    def test_includes_user_prompt_with_images(self) -> None:
        """Test that user message includes text and images."""
        frames = ["frame1_base64", "frame2_base64"]
        messages = build_vision_messages(frames)

        user_content = messages[1]["content"]

        # Should have text + 2 images
        assert len(user_content) == 3
        assert user_content[0]["type"] == "text"
        assert user_content[1]["type"] == "image_url"
        assert user_content[2]["type"] == "image_url"

    def test_formats_base64_as_data_url(self) -> None:
        """Test that base64 is wrapped in data URL format."""
        messages = build_vision_messages(["testbase64"])

        image_content = messages[1]["content"][1]
        assert "data:image/jpeg;base64,testbase64" in image_content["image_url"]["url"]


class TestParseTagsResponse:
    """Tests for parsing LLM responses."""

    def test_parses_valid_json(self) -> None:
        """Test parsing of valid JSON response."""
        response = """{
            "location": "Gym",
            "brand_objects": ["Nike Shoes"],
            "visual_text": ["PUSH HARDER"],
            "mood": "Energetic",
            "excitement": "High"
        }"""

        result = parse_tags_response(response)

        assert result["location"] == "Gym"
        assert result["mood"] == "Energetic"
        assert "Nike Shoes" in result["brand_objects"]

    def test_handles_markdown_code_block(self) -> None:
        """Test that markdown code blocks are stripped."""
        response = """```json
{
    "location": "Office",
    "brand_objects": [],
    "visual_text": [],
    "mood": "Calm",
    "excitement": "Low"
}
```"""

        result = parse_tags_response(response)

        assert result["location"] == "Office"

    def test_raises_error_for_invalid_json(self) -> None:
        """Test that invalid JSON raises LLMError."""
        with pytest.raises(LLMError) as exc_info:
            parse_tags_response("not valid json")

        assert "Failed to parse" in str(exc_info.value)

    def test_raises_error_for_missing_fields(self) -> None:
        """Test that missing required fields raises LLMError."""
        response = '{"location": "Gym"}'  # Missing other fields

        with pytest.raises(LLMError) as exc_info:
            parse_tags_response(response)

        assert "missing required fields" in str(exc_info.value)

    def test_converts_non_list_to_list(self) -> None:
        """Test that non-list values are converted to lists."""
        response = """{
            "location": "Street",
            "brand_objects": "Single Brand",
            "visual_text": "Single Text",
            "mood": "Chill",
            "excitement": "Low"
        }"""

        result = parse_tags_response(response)

        assert isinstance(result["brand_objects"], list)
        assert result["brand_objects"] == ["Single Brand"]


class TestAnalyzeFrames:
    """Tests for the analyze_frames function."""

    def test_calls_openai_api_correctly(self) -> None:
        """Test that OpenAI API is called with correct structure."""
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content="""{
                        "location": "Test",
                        "brand_objects": [],
                        "visual_text": [],
                        "mood": "Neutral",
                        "excitement": "Low"
                    }"""
                )
            )
        ]

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response

        with patch("videotagger.llm.get_llm_client", return_value=mock_client):
            from videotagger.llm import analyze_frames

            # Need to pass a config to avoid loading settings
            mock_config = MagicMock()
            mock_config.model = "test-model"

            result = analyze_frames(["test_frame"], config=mock_config)

            assert result["location"] == "Test"
            mock_client.chat.completions.create.assert_called_once()
