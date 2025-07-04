"""Voice-based authentication utilities for Ghosthand."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import numpy as np
from logger import log


VOICEPRINT_DIR = Path("voiceprints")
VOICEPRINT_DIR.mkdir(exist_ok=True)


def enroll_user(username: str, audio_path: str) -> str:
    """Enroll a new user using a short WAV sample.

    Parameters
    ----------
    username : str
        Identifier of the user to enrol.
    audio_path : str
        Path to the WAV file containing the user's voice.

    Returns
    -------
    str
        Path to the saved voiceprint.
    """
    log(f"Enrolling voice for {username}", "GUARD")
    try:
        from resemblyzer import VoiceEncoder, preprocess_wav
        import soundfile as sf

        wav, sr = sf.read(audio_path)
        wav = preprocess_wav(wav, sr)
        encoder = VoiceEncoder()
        embed = encoder.embed_utterance(wav)
    except Exception as exc:  # pragma: no cover - optional heavy deps
        log(f"Voice enrollment failed: {exc}", "ERROR")
        raise

    VOICEPRINT_DIR.mkdir(exist_ok=True)
    out_path = VOICEPRINT_DIR / f"{username}.npy"
    np.save(out_path, embed)
    log(f"Enrollment successful for {username}", "GUARD")
    return str(out_path)


def verify_user(audio_path: str) -> str:
    """Verify an audio sample against enrolled voiceprints.

    Parameters
    ----------
    audio_path : str
        Path to the WAV sample to check.

    Returns
    -------
    str
        Best matching username or ``"unknown"``.
    """
    try:
        from resemblyzer import VoiceEncoder, preprocess_wav
        import soundfile as sf

        wav, sr = sf.read(audio_path)
        wav = preprocess_wav(wav, sr)
        encoder = VoiceEncoder()
        sample_embed = encoder.embed_utterance(wav)
    except Exception as exc:  # pragma: no cover
        log(f"Voice verification failed: {exc}", "ERROR")
        return "unknown"

    best_user = "unknown"
    best_score = 0.0
    for vp in VOICEPRINT_DIR.glob("*.npy"):
        try:
            embed = np.load(vp)
            score = float(np.dot(sample_embed, embed) / (np.linalg.norm(sample_embed) * np.linalg.norm(embed)))
            if score > best_score:
                best_score = score
                best_user = vp.stem
        except Exception:
            continue

    log(f"Voice verification score {best_score:.2f} for {best_user}", "GUARD")
    if best_score >= 0.75:
        return best_user
    return "unknown"


def record_voice_sample(save_path: str, seconds: int = 5) -> None:
    """Record audio from the microphone to ``save_path``."""
    log(f"Recording voice sample to {save_path}", "GUARD")
    try:
        import sounddevice as sd
        import soundfile as sf
    except Exception as exc:  # pragma: no cover
        log(f"Audio libraries unavailable: {exc}", "ERROR")
        raise

    fs = 16000
    try:
        audio = sd.rec(int(seconds * fs), samplerate=fs, channels=1)
        sd.wait()
        sf.write(save_path, audio, fs)
    except Exception as exc:
        log(f"Recording failed: {exc}", "ERROR")
        raise


def is_enrolled(username: str) -> bool:
    """Return ``True`` if a voiceprint for ``username`` exists."""
    return (VOICEPRINT_DIR / f"{username}.npy").exists()
