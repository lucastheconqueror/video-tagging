"""Prosody-based voiceover style classifier.

Classifies voiceover style using pure signal processing (no ML models).
Extracts pitch, tempo, and energy to determine marketing-relevant tags.

Features:
- Pitch (F0): High = Energetic/Excited, Low = Calm/Authoritative
- Speech Rate: Fast = Hype/Promo, Slow = Tutorial/Explainer  
- Energy (RMS): Loud = Aggressive/Exciting, Quiet = ASMR/Intimate
"""

import logging
from dataclasses import dataclass
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class ProsodyResult:
    """Prosody analysis results."""

    tempo_bpm: float
    mean_pitch_hz: float
    pitch_variation_hz: float
    energy_level: float
    voiceover_style: str

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "tempo_bpm": round(self.tempo_bpm, 1),
            "mean_pitch_hz": round(self.mean_pitch_hz, 1),
            "pitch_variation_hz": round(self.pitch_variation_hz, 1),
            "energy_level": round(self.energy_level, 4),
            "voiceover_style": self.voiceover_style,
        }


def _classify_style(
    tempo: float,
    pitch: float,
    pitch_std: float,
    energy: float,
) -> str:
    """Map prosody features to marketing-relevant tags.

    Thresholds are empirical - tune based on your data.

    Args:
        tempo: Speech tempo in BPM.
        pitch: Mean pitch (F0) in Hz.
        pitch_std: Pitch standard deviation in Hz.
        energy: Mean RMS energy level.

    Returns:
        Marketing style tag.
    """
    # High Energy + High Tempo = Hype/Promo
    if energy > 0.05 and tempo > 140:
        return "hype" if pitch > 180 else "aggressive"

    # High Pitch Variation = Emotional/Storytelling
    if pitch_std > 30:
        return "storytelling"

    # Fast + Normal Energy = Explainer/Tutorial
    if tempo > 120 and energy < 0.08:
        return "tutorial"

    # Low Pitch + Slow = Authoritative/Corporate
    if pitch < 150 and tempo < 100:
        return "authoritative"

    # Low Energy + Slow = ASMR/Intimate
    if energy < 0.03 and tempo < 90:
        return "intimate"

    # Default
    return "neutral"


def analyze_prosody(audio_path: str | Path) -> ProsodyResult:
    """Analyze voiceover prosody using signal processing.

    No ML models needed - uses librosa for tempo/energy and
    Parselmouth (Praat) for accurate pitch extraction.

    Args:
        audio_path: Path to audio file (WAV recommended).

    Returns:
        ProsodyResult with extracted features and style classification.
    """
    import librosa
    import parselmouth

    audio_path = Path(audio_path)
    logger.debug(f"Analyzing prosody: {audio_path}")

    # Load audio
    y, sr = librosa.load(audio_path, sr=16000)

    # --- Feature 1: Speech Rate (Tempo) ---
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    tempo_result = librosa.feature.tempo(onset_envelope=onset_env, sr=sr)
    tempo = float(np.atleast_1d(tempo_result)[0])

    # --- Feature 2: Pitch (F0 - Fundamental Frequency) ---
    # Use Parselmouth (Praat wrapper) for accurate pitch
    snd = parselmouth.Sound(str(audio_path))
    pitch = snd.to_pitch()
    pitch_values = pitch.selected_array["frequency"]
    pitch_values = pitch_values[pitch_values > 0]  # Remove unvoiced frames

    if len(pitch_values) > 0:
        mean_pitch = float(np.mean(pitch_values))
        pitch_std = float(np.std(pitch_values))
    else:
        mean_pitch = 0.0
        pitch_std = 0.0

    # --- Feature 3: Energy (RMS - Loudness) ---
    rms = librosa.feature.rms(y=y)[0]
    mean_energy = float(np.mean(rms))

    # --- Classification ---
    style = _classify_style(tempo, mean_pitch, pitch_std, mean_energy)

    logger.debug(
        f"Prosody: tempo={tempo:.1f}bpm, pitch={mean_pitch:.1f}Hz, "
        f"pitch_std={pitch_std:.1f}Hz, energy={mean_energy:.4f}, style={style}"
    )

    return ProsodyResult(
        tempo_bpm=tempo,
        mean_pitch_hz=mean_pitch,
        pitch_variation_hz=pitch_std,
        energy_level=mean_energy,
        voiceover_style=style,
    )


def analyze_video_prosody(video_path: str | Path) -> ProsodyResult:
    """Extract audio from video and analyze prosody.

    Args:
        video_path: Path to video file.

    Returns:
        ProsodyResult with extracted features and style classification.
    """
    from videotagger.audio_extract import extract_audio

    video_path = Path(video_path)
    audio_path = None

    try:
        audio_path = extract_audio(video_path)
        return analyze_prosody(audio_path)
    finally:
        if audio_path and audio_path.exists():
            audio_path.unlink()
