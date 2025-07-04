"""Voice output utilities for Ghosthand.

Provides a simple wrapper around ``pyttsx3`` so the agent can speak
status updates or results to the user.
"""


from logger import log


def speak(text: str) -> None:
    """Convert ``text`` to speech.

    Parameters
    ----------
    text : str
        The text that should be spoken aloud.
    """

    log(f"Speak: {text}")
    try:
        import pyttsx3
        engine = pyttsx3.init()
        engine.say(text)
        engine.runAndWait()
    except Exception as exc:  # pragma: no cover - best effort
        log(f"Failed to speak: {exc}", "ERROR")
