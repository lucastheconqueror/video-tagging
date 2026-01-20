"""Tests for audio extraction and analysis pipeline."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestAudioExtract:
    """Tests for audio_extract module."""

    def test_extract_audio_file_not_found(self):
        """Test that missing video file raises FileNotFoundError."""
        from videotagger.audio_extract import extract_audio

        with pytest.raises(FileNotFoundError, match="Video file not found"):
            extract_audio("/nonexistent/video.mp4")

    @patch("videotagger.audio_extract.subprocess.run")
    def test_extract_audio_success(self, mock_run):
        """Test successful audio extraction."""
        from videotagger.audio_extract import extract_audio

        # Create a temp video file (fake)
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            f.write(b"fake video content")
            video_path = Path(f.name)

        # Create expected output
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(b"fake audio content")
            expected_output = Path(f.name)

        try:
            mock_run.return_value = MagicMock(stdout="", stderr="", returncode=0)

            # Extract audio
            result = extract_audio(video_path, output_path=expected_output)

            # Verify FFmpeg was called
            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]
            assert call_args[0] == "ffmpeg"
            assert "-vn" in call_args  # No video
            assert str(video_path) in call_args

            assert result == expected_output

        finally:
            video_path.unlink(missing_ok=True)
            expected_output.unlink(missing_ok=True)

    @patch("videotagger.audio_extract.subprocess.run")
    def test_extract_audio_ffmpeg_not_found(self, mock_run):
        """Test error when FFmpeg is not installed."""
        from videotagger.audio_extract import extract_audio

        mock_run.side_effect = FileNotFoundError("ffmpeg not found")

        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            f.write(b"fake video")
            video_path = Path(f.name)

        try:
            with pytest.raises(RuntimeError, match="FFmpeg not found"):
                extract_audio(video_path)
        finally:
            video_path.unlink(missing_ok=True)


class TestAudioAnalysisResult:
    """Tests for AudioAnalysisResult dataclass."""

    def test_to_dict(self):
        """Test conversion to dictionary."""
        from videotagger.audio_analysis import AudioAnalysisResult, SpeechSegment

        result = AudioAnalysisResult(
            voice_detected=True,
            voice_segments=[SpeechSegment(start_sec=0.5, end_sec=2.3)],
            voice_mood="happy",
            voice_mood_confidence=0.85,
            music_genre="pop",
            music_genre_confidence=0.72,
            music_subgenres=["mainstream"],
            processing_time_ms=245.7,
            models_invoked=["silero_vad", "wav2vec2_emotion", "efficientnet_genre"],
        )

        d = result.to_dict()

        assert d["voice_detected"] is True
        assert d["voice_mood"] == "happy"
        assert d["voice_mood_confidence"] == 0.85
        assert d["voice_segments_seconds"] == [[0.5, 2.3]]
        assert d["music_genre"] == "pop"
        assert d["music_genre_confidence"] == 0.72
        assert d["music_subgenres"] == ["mainstream"]
        assert d["processing_time_ms"] == 245.7
        assert "silero_vad" in d["models_invoked"]

    def test_to_dict_no_voice(self):
        """Test dictionary output when no voice detected."""
        from videotagger.audio_analysis import AudioAnalysisResult

        result = AudioAnalysisResult(
            voice_detected=False,
            voice_mood="none",
            voice_mood_confidence=1.0,
            music_genre="electronic",
            music_genre_confidence=0.6,
        )

        d = result.to_dict()

        assert d["voice_detected"] is False
        assert d["voice_mood"] == "none"
        assert d["voice_segments_seconds"] == []


class TestSpeechSegment:
    """Tests for SpeechSegment dataclass."""

    def test_duration(self):
        """Test duration calculation."""
        from videotagger.audio_analysis import SpeechSegment

        segment = SpeechSegment(start_sec=1.5, end_sec=4.5)
        assert segment.duration == 3.0


class TestAudioConfig:
    """Tests for AudioConfig settings."""

    def test_audio_config_defaults(self):
        """Test default audio configuration values."""
        from videotagger.config import AudioConfig

        config = AudioConfig()

        assert config.enabled is True
        assert config.vad_threshold == 0.5
        assert config.min_speech_duration_ms == 250
        assert config.sample_rate == 16000

    def test_audio_config_validation(self):
        """Test audio config validation."""
        from pydantic import ValidationError

        from videotagger.config import AudioConfig

        # VAD threshold must be 0-1
        with pytest.raises(ValidationError):
            AudioConfig(vad_threshold=1.5)

        # Sample rate must be positive
        with pytest.raises(ValidationError):
            AudioConfig(min_speech_duration_ms=-1)


class TestExtractSpeechAudio:
    """Tests for speech segment extraction."""

    def test_extract_speech_audio(self):
        """Test extracting speech segments from waveform."""
        import numpy as np

        from videotagger.audio_analysis import SpeechSegment, extract_speech_audio

        # Create fake waveform (1 second at 16kHz)
        sample_rate = 16000
        waveform = np.arange(sample_rate, dtype=np.float32)

        # Extract segment from 0.25s to 0.75s
        segments = [SpeechSegment(start_sec=0.25, end_sec=0.75)]

        result = extract_speech_audio(waveform, segments, sample_rate)

        # Should be 0.5 seconds = 8000 samples
        assert len(result) == 8000
        # First sample should be at index 4000 (0.25 * 16000)
        assert result[0] == 4000

    def test_extract_speech_audio_empty(self):
        """Test with no segments."""
        import numpy as np

        from videotagger.audio_analysis import extract_speech_audio

        waveform = np.arange(16000, dtype=np.float32)
        result = extract_speech_audio(waveform, [], 16000)

        assert len(result) == 0


class TestIntegration:
    """Integration tests for the full audio pipeline."""

    @pytest.mark.skip(reason="Requires ML models to be installed")
    def test_analyze_audio_full_pipeline(self):
        """Test full audio analysis pipeline.

        This test requires:
        - torch
        - transformers
        - librosa
        - Silero VAD model (downloaded on first run)
        """
        from videotagger.audio_analysis import analyze_audio

        # Would need a real audio file here
        pass

    def test_merged_output_schema(self):
        """Test that merged output has expected schema."""
        from videotagger.audio_analysis import AudioAnalysisResult

        # Simulate what runpod_processor produces
        vision_result = {
            "setting": "Office",
            "branded_items": [],
            "cta": [],
            "key_text": ["productivity", "software"],
            "content_type": "tutorial",
        }

        audio_result = AudioAnalysisResult(
            voice_detected=True,
            voice_mood="neutral",
            voice_mood_confidence=0.8,
            music_genre="ambient",
            music_genre_confidence=0.5,
            models_invoked=["silero_vad", "wav2vec2_emotion", "efficientnet_genre"],
        )

        # Merge like runpod_processor does
        merged = {**vision_result, "audio_analysis": audio_result.to_dict()}

        # Verify structure
        assert "setting" in merged
        assert "audio_analysis" in merged
        assert merged["audio_analysis"]["voice_detected"] is True
        assert merged["audio_analysis"]["voice_mood"] == "neutral"
        assert merged["audio_analysis"]["music_genre"] == "ambient"
