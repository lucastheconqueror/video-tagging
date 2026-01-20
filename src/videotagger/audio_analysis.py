"""Composite Audio Tagging Pipeline.

Multi-model audio analysis with:
- Silero VAD: Voice Activity Detection (gatekeeper)
- Wav2Vec2-XLSR-Emotion: Speech emotion classification
- EfficientNet-B0: Music genre classification via spectrograms

Architecture follows "Small Experts" pattern for efficiency and hallucination prevention.
See: agent-os/specs/audio-pipeline-architecture.md
"""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)

# Lazy-loaded model cache
_model_cache: dict[str, Any] = {}


@dataclass
class SpeechSegment:
    """A detected speech segment with timestamps."""

    start_sec: float
    end_sec: float

    @property
    def duration(self) -> float:
        return self.end_sec - self.start_sec


@dataclass
class ProsodyFeatures:
    """Prosody features extracted via signal processing."""

    tempo_bpm: float = 0.0
    mean_pitch_hz: float = 0.0
    pitch_variation_hz: float = 0.0
    energy_level: float = 0.0
    voiceover_style: str = "unknown"

    def to_dict(self) -> dict[str, Any]:
        return {
            "tempo_bpm": round(self.tempo_bpm, 1),
            "mean_pitch_hz": round(self.mean_pitch_hz, 1),
            "pitch_variation_hz": round(self.pitch_variation_hz, 1),
            "energy_level": round(self.energy_level, 4),
            "voiceover_style": self.voiceover_style,
        }


@dataclass
class AudioAnalysisResult:
    """Complete audio analysis output."""

    # Voice detection
    voice_detected: bool
    voice_segments: list[SpeechSegment] = field(default_factory=list)

    # Emotion (only if voice detected) - ML-based
    voice_mood: str = "none"
    voice_mood_confidence: float = 1.0

    # Prosody (only if voice detected) - signal processing
    prosody: ProsodyFeatures | None = None

    # Music genre (always computed)
    music_genre: str = "unknown"
    music_genre_confidence: float = 0.0
    music_subgenres: list[str] = field(default_factory=list)

    # Metadata
    processing_time_ms: float = 0.0
    models_invoked: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            "voice_detected": self.voice_detected,
            "voice_mood": self.voice_mood,
            "voice_mood_confidence": round(self.voice_mood_confidence, 3),
            "voice_segments_seconds": [
                [round(s.start_sec, 2), round(s.end_sec, 2)] for s in self.voice_segments
            ],
            "music_genre": self.music_genre,
            "music_genre_confidence": round(self.music_genre_confidence, 3),
            "music_subgenres": self.music_subgenres,
            "processing_time_ms": round(self.processing_time_ms, 1),
            "models_invoked": self.models_invoked,
        }
        if self.prosody:
            result["prosody"] = self.prosody.to_dict()
        return result


def _load_audio_waveform(audio_path: Path, sample_rate: int = 16000) -> tuple[np.ndarray, int]:
    """Load audio file as numpy waveform.

    Args:
        audio_path: Path to WAV file.
        sample_rate: Expected sample rate.

    Returns:
        Tuple of (waveform array, sample_rate).
    """
    try:
        import librosa

        waveform, sr = librosa.load(audio_path, sr=sample_rate, mono=True)
        return waveform, sr
    except ImportError:
        # Fallback to scipy if librosa not available
        from scipy.io import wavfile

        sr, waveform = wavfile.read(audio_path)
        if waveform.dtype == np.int16:
            waveform = waveform.astype(np.float32) / 32768.0
        if len(waveform.shape) > 1:
            waveform = waveform.mean(axis=1)
        return waveform, sr


def _get_vad_model():
    """Load Silero VAD model (cached)."""
    if "silero_vad" not in _model_cache:
        import torch

        logger.info("Loading Silero VAD model...")
        model, utils = torch.hub.load(
            repo_or_dir="snakers4/silero-vad",
            model="silero_vad",
            force_reload=False,
            trust_repo=True,
        )
        _model_cache["silero_vad"] = (model, utils)
        logger.info("Silero VAD loaded")

    return _model_cache["silero_vad"]


def _get_emotion_pipeline():
    """Load Wav2Vec2 emotion classification pipeline (cached).
    
    Uses superb/wav2vec2-base-superb-er which is trained on:
    - IEMOCAP dataset (conversational emotion)
    - Classes: neu (neutral), hap (happy), sad, ang (angry)
    """
    if "emotion" not in _model_cache:
        from transformers import pipeline

        logger.info("Loading Wav2Vec2-SUPERB emotion model...")
        pipe = pipeline(
            "audio-classification",
            model="superb/wav2vec2-base-superb-er",
            device=-1,  # CPU
        )
        _model_cache["emotion"] = pipe
        logger.info("Wav2Vec2-SUPERB emotion model loaded")

    return _model_cache["emotion"]


def _get_genre_model():
    """Load EfficientNet genre classifier (cached).

    Note: This requires a pretrained model. For now, we use a placeholder
    that will be replaced with a real model.
    """
    if "genre" not in _model_cache:
        # For MVP, we'll use a simple spectrogram-based heuristic
        # Real implementation would load: efficientnet_b0 trained on GTZAN/FMA
        logger.info("Loading genre classifier...")
        _model_cache["genre"] = "placeholder"
        logger.info("Genre classifier loaded (placeholder)")

    return _model_cache["genre"]


def detect_speech(
    waveform: np.ndarray,
    sample_rate: int = 16000,
    threshold: float = 0.5,
) -> tuple[bool, list[SpeechSegment]]:
    """Detect voice activity in audio using Silero VAD.

    Args:
        waveform: Audio waveform as numpy array.
        sample_rate: Sample rate of the audio.
        threshold: Voice probability threshold.

    Returns:
        Tuple of (has_speech, list of speech segments).
    """
    import torch

    model, utils = _get_vad_model()
    get_speech_timestamps = utils[0]

    # Convert to torch tensor
    audio_tensor = torch.from_numpy(waveform).float()

    # Get speech timestamps
    speech_timestamps = get_speech_timestamps(
        audio_tensor,
        model,
        sampling_rate=sample_rate,
        threshold=threshold,
        min_speech_duration_ms=250,
        min_silence_duration_ms=100,
    )

    # Convert to SpeechSegment objects
    segments = [
        SpeechSegment(
            start_sec=ts["start"] / sample_rate,
            end_sec=ts["end"] / sample_rate,
        )
        for ts in speech_timestamps
    ]

    has_speech = len(segments) > 0
    total_speech = sum(s.duration for s in segments)
    logger.debug(f"VAD: {len(segments)} segments, {total_speech:.1f}s total speech")

    return has_speech, segments


def extract_speech_audio(
    waveform: np.ndarray,
    segments: list[SpeechSegment],
    sample_rate: int = 16000,
) -> np.ndarray:
    """Extract and concatenate speech segments from waveform.

    Args:
        waveform: Full audio waveform.
        segments: List of speech segments to extract.
        sample_rate: Sample rate.

    Returns:
        Concatenated speech-only waveform.
    """
    if not segments:
        return np.array([], dtype=np.float32)

    speech_chunks = []
    for seg in segments:
        start_sample = int(seg.start_sec * sample_rate)
        end_sample = int(seg.end_sec * sample_rate)
        speech_chunks.append(waveform[start_sample:end_sample])

    return np.concatenate(speech_chunks)


def analyze_emotion(
    speech_waveform: np.ndarray,
    sample_rate: int = 16000,
    min_confidence: float = 0.25,
) -> tuple[str, float]:
    """Analyze emotion in speech audio using Wav2Vec2.

    Args:
        speech_waveform: Speech-only audio waveform.
        sample_rate: Sample rate.
        min_confidence: Minimum confidence to report emotion (below = "neutral").

    Returns:
        Tuple of (emotion label, confidence score).
    """
    if len(speech_waveform) < sample_rate * 0.5:  # Less than 0.5s
        logger.debug("Speech too short for emotion analysis")
        return "none", 1.0

    pipe = _get_emotion_pipeline()

    # Process in chunks if audio is long (>30s) to avoid memory issues
    max_samples = sample_rate * 30
    if len(speech_waveform) > max_samples:
        # Take first 30 seconds only
        speech_waveform = speech_waveform[:max_samples]
        logger.debug("Truncated audio to 30s for emotion analysis")

    # Run inference
    results = pipe(
        {"raw": speech_waveform, "sampling_rate": sample_rate},
        top_k=5,
    )

    if not results:
        return "neutral", 0.5

    top_result = results[0]
    raw_label = top_result["label"].lower()
    confidence = top_result["score"]

    # Map SUPERB model labels to full names
    # SUPERB uses: neu, hap, sad, ang
    label_map = {
        "neu": "neutral",
        "hap": "happy",
        "sad": "sad",
        "ang": "angry",
    }
    emotion = label_map.get(raw_label, raw_label)

    # If confidence is low (near uniform distribution), classify as "neutral"
    # This handles professional voiceovers that aren't emotionally expressive
    if confidence < min_confidence:
        top_preds = [(label_map.get(r["label"].lower(), r["label"]), round(r["score"], 2)) 
                     for r in results[:3]]
        logger.debug(
            f"Low confidence ({confidence:.2f}) - classifying as neutral. "
            f"Top predictions: {top_preds}"
        )
        return "neutral", confidence

    logger.debug(f"Emotion: {emotion} ({confidence:.2f})")
    return emotion, confidence


def extract_music_gaps(
    waveform: np.ndarray,
    speech_segments: list[SpeechSegment],
    sample_rate: int = 16000,
    min_gap_sec: float = 0.5,
) -> list[np.ndarray]:
    """Extract audio segments where there's no speech (music-only gaps).

    Args:
        waveform: Full audio waveform.
        speech_segments: List of speech segments to exclude.
        sample_rate: Sample rate.
        min_gap_sec: Minimum gap duration to consider.

    Returns:
        List of music-only audio chunks.
    """
    if not speech_segments:
        # No speech = entire audio is music
        return [waveform]

    music_chunks = []
    last_end = 0.0

    for segment in speech_segments:
        gap_duration = segment.start_sec - last_end
        if gap_duration >= min_gap_sec:
            start_sample = int(last_end * sample_rate)
            end_sample = int(segment.start_sec * sample_rate)
            music_chunks.append(waveform[start_sample:end_sample])
        last_end = segment.end_sec

    # Check for gap after last speech segment
    audio_duration = len(waveform) / sample_rate
    final_gap = audio_duration - last_end
    if final_gap >= min_gap_sec:
        start_sample = int(last_end * sample_rate)
        music_chunks.append(waveform[start_sample:])

    return music_chunks


def analyze_genre(
    waveform: np.ndarray,
    sample_rate: int = 16000,
    speech_segments: list[SpeechSegment] | None = None,
) -> tuple[str, float, list[str]]:
    """Analyze music genre using spectrogram analysis.

    Uses the "Gaps" method: analyzes only non-speech segments to avoid
    voice interference with music classification.

    Args:
        waveform: Full audio waveform.
        sample_rate: Sample rate.
        speech_segments: Optional speech segments to exclude from analysis.

    Returns:
        Tuple of (genre, confidence, subgenres).
    """
    try:
        import librosa
    except ImportError:
        logger.warning("librosa not installed, skipping genre analysis")
        return "unknown", 0.0, []

    # Extract music-only segments (gaps between speech)
    if speech_segments:
        music_chunks = extract_music_gaps(waveform, speech_segments, sample_rate)
        if music_chunks:
            # Use the longest music chunk for analysis
            analysis_audio = max(music_chunks, key=len)
            total_music_sec = sum(len(chunk) / sample_rate for chunk in music_chunks)
            logger.debug(
                f"Analyzing music from {len(music_chunks)} gaps "
                f"({total_music_sec:.1f}s total, using {len(analysis_audio)/sample_rate:.1f}s chunk)"
            )
        else:
            # No gaps found, fall back to full audio
            logger.debug("No music gaps found, analyzing full audio")
            analysis_audio = waveform
    else:
        # No speech segments provided, analyze full audio
        analysis_audio = waveform

    # Skip if audio too short
    if len(analysis_audio) < sample_rate * 0.5:
        logger.debug("Music segment too short for genre analysis")
        return "unknown", 0.0, []

    # Compute mel spectrogram
    mel_spec = librosa.feature.melspectrogram(
        y=analysis_audio,
        sr=sample_rate,
        n_mels=128,
        fmax=8000,
    )
    mel_db = librosa.power_to_db(mel_spec, ref=np.max)

    # Extract spectral features
    spectral_centroid = librosa.feature.spectral_centroid(y=analysis_audio, sr=sample_rate)
    tempo_result, _ = librosa.beat.beat_track(y=analysis_audio, sr=sample_rate)
    rms = librosa.feature.rms(y=analysis_audio)
    spectral_rolloff = librosa.feature.spectral_rolloff(y=analysis_audio, sr=sample_rate)
    zcr = librosa.feature.zero_crossing_rate(analysis_audio)

    avg_centroid = float(np.mean(spectral_centroid))
    avg_rms = float(np.mean(rms))
    avg_rolloff = float(np.mean(spectral_rolloff))
    avg_zcr = float(np.mean(zcr))
    tempo = float(np.atleast_1d(tempo_result)[0]) if hasattr(tempo_result, '__iter__') else float(tempo_result)

    # Enhanced heuristic classification
    # Dramatic/Cinematic: Low centroid + moderate rolloff (orchestral texture)
    # Can be fast or slow tempo, but low-to-moderate energy
    if avg_centroid < 2000 and 2500 < avg_rolloff < 4500 and avg_rms < 0.06:
        genre = "dramatic"
        subgenres = ["cinematic", "orchestral"]
        confidence = 0.7

    # Electronic: High tempo, high energy, high ZCR
    elif tempo > 120 and avg_rms > 0.08 and avg_zcr > 0.1:
        genre = "electronic"
        subgenres = ["edm", "dance"]
        confidence = 0.65

    # Classical/Orchestral: Low tempo, rich harmonics, low centroid
    elif tempo < 90 and avg_centroid < 2000 and avg_rolloff > 3500:
        genre = "classical"
        subgenres = ["orchestral"]
        confidence = 0.6

    # Rock: High energy, mid-range centroid
    elif avg_rms > 0.12 and 2000 < avg_centroid < 3500:
        genre = "rock"
        subgenres = ["alternative"]
        confidence = 0.6

    # Pop: Moderate tempo, bright sound
    elif tempo > 100 and avg_centroid > 3000:
        genre = "pop"
        subgenres = ["mainstream"]
        confidence = 0.55

    # Ambient: Low energy, slow
    elif avg_rms < 0.04 and tempo < 100:
        genre = "ambient"
        subgenres = ["background"]
        confidence = 0.5

    # Default
    else:
        genre = "unknown"
        subgenres = []
        confidence = 0.3

    logger.debug(
        f"Genre: {genre} ({confidence:.2f}), "
        f"tempo={tempo:.0f}, centroid={avg_centroid:.0f}, "
        f"rolloff={avg_rolloff:.0f}, rms={avg_rms:.4f}"
    )
    return genre, confidence, subgenres


def analyze_audio(audio_path: str | Path) -> AudioAnalysisResult:
    """Run complete audio analysis pipeline.

    This is the main entry point for audio analysis. It runs:
    1. Silero VAD to detect speech
    2. Wav2Vec2 emotion (only if speech detected)
    3. EfficientNet genre (always)

    Args:
        audio_path: Path to WAV audio file (16kHz mono recommended).

    Returns:
        AudioAnalysisResult with all extracted tags.
    """
    import time

    start_time = time.time()
    audio_path = Path(audio_path)

    result = AudioAnalysisResult(
        voice_detected=False,
        models_invoked=["silero_vad"],
    )

    try:
        # Load audio
        logger.info(f"Analyzing audio: {audio_path}")
        waveform, sr = _load_audio_waveform(audio_path)
        logger.debug(f"Loaded audio: {len(waveform)/sr:.1f}s at {sr}Hz")

        # Run VAD first (needed for genre analysis)
        has_speech, segments = detect_speech(waveform, sr)
        result.voice_detected = has_speech
        result.voice_segments = segments

        # Run genre analysis with speech segments (uses "gaps" method)
        result.models_invoked.append("genre_heuristic")
        try:
            genre, conf, subgenres = analyze_genre(waveform, sr, speech_segments=segments)
            result.music_genre = genre
            result.music_genre_confidence = conf
            result.music_subgenres = subgenres
        except Exception as e:
            logger.error(f"Genre analysis failed: {e}")
            result.errors.append(f"genre: {e}")

        # Conditional: Run prosody only if speech detected
        if result.voice_detected:
            logger.debug("Speech detected, running prosody analysis")
            result.models_invoked.append("prosody")

            try:
                from videotagger.prosody import analyze_prosody

                prosody_result = analyze_prosody(audio_path)
                result.prosody = ProsodyFeatures(
                    tempo_bpm=prosody_result.tempo_bpm,
                    mean_pitch_hz=prosody_result.mean_pitch_hz,
                    pitch_variation_hz=prosody_result.pitch_variation_hz,
                    energy_level=prosody_result.energy_level,
                    voiceover_style=prosody_result.voiceover_style,
                )
                # Use prosody style as the mood
                result.voice_mood = prosody_result.voiceover_style
                result.voice_mood_confidence = 1.0
            except Exception as e:
                logger.error(f"Prosody analysis failed: {e}")
                result.errors.append(f"prosody: {e}")
        else:
            logger.debug("No speech detected, skipping prosody analysis")
            result.voice_mood = "none"
            result.voice_mood_confidence = 1.0

    except Exception as e:
        logger.error(f"Audio analysis failed: {e}")
        result.errors.append(str(e))

    result.processing_time_ms = (time.time() - start_time) * 1000
    logger.info(
        f"Audio analysis complete: voice={result.voice_detected}, "
        f"mood={result.voice_mood}, genre={result.music_genre}, "
        f"time={result.processing_time_ms:.0f}ms"
    )

    return result


def analyze_video_audio(video_path: str | Path) -> AudioAnalysisResult:
    """Extract audio from video and run analysis pipeline.

    Convenience function that handles audio extraction.

    Args:
        video_path: Path to video file.

    Returns:
        AudioAnalysisResult with all extracted tags.
    """
    from videotagger.audio_extract import extract_audio

    video_path = Path(video_path)
    audio_path = None

    try:
        # Extract audio to temp file
        audio_path = extract_audio(video_path)

        # Run analysis
        result = analyze_audio(audio_path)
        return result

    finally:
        # Clean up temp audio file
        if audio_path and audio_path.exists():
            audio_path.unlink()
            logger.debug(f"Cleaned up temp audio: {audio_path}")
