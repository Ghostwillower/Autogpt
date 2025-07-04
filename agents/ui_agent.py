"""Agent responsible for UI automation.

This module exposes small helpers that interact with the user's desktop.
It currently relies on the :mod:`pyautogui` package for cross‑platform
mouse and keyboard control but falls back gracefully if it is not
available (for instance on headless systems).
"""


def click(x: int, y: int) -> None:
    """Simulate a mouse click at the given coordinates.

    Parameters
    ----------
    x, y : int
        Screen coordinates where the click should occur.
    """

    print(f"[UI] Click at ({x}, {y})")
    try:
        import pyautogui

        pyautogui.click(x=x, y=y)
    except Exception as exc:  # pragma: no cover - environment specific
        print(f"[UI] Click failed: {exc}")


def type_text(text: str) -> None:
    """Simulate typing text using the keyboard.

    Parameters
    ----------
    text : str
        The text to type.
    """

    print(f"[UI] Typing: {text}")
    try:
        import pyautogui

        pyautogui.write(text)
    except Exception as exc:  # pragma: no cover - environment specific
        print(f"[UI] Type failed: {exc}")
