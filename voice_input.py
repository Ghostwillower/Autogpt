"""Voice input utilities for Ghosthand.

This module records audio from the microphone and transcribes it using
OpenAI Whisper. Recording is limited to a short duration so it can be
used from the command line or GUI without additional interaction.
"""

from pathlib import Path
import tempfile

from logger import log


def listen_and_transcribe(duration: int = 10) -> str:
    """Record from the microphone and return the transcribed text.

    Parameters
    ----------
    duration : int, optional
        Recording duration in seconds, by default ``10``.

    Returns
    -------
    str
        The recognised text or an empty string if transcription failed.
    """

    log(f"Recording for {duration}s ...")
    try:
        import sounddevice as sd
        import soundfile as sf
    except Exception as exc:  # pragma: no cover - optional dependency
        log(f"Audio capture unavailable: {exc}", "ERROR")
        return ""

    fs = 16000
    try:
        audio = sd.rec(int(duration * fs), samplerate=fs, channels=1)
        sd.wait()
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            sf.write(tmp.name, audio, fs)
            wav_path = tmp.name
    except Exception as exc:
        log(f"Recording failed: {exc}", "ERROR")
        return ""

    log("Transcribing audio ...")
    try:
        import whisper

        model = whisper.load_model("base")
        result = model.transcribe(wav_path)
        text = result.get("text", "").strip()
    except Exception as exc:
        log(f"Transcription failed: {exc}", "ERROR")
        text = ""
    finally:
        try:
            Path(wav_path).unlink(missing_ok=True)
        except Exception:
            pass

    log(f"Transcribed text: {text}")
    return text
