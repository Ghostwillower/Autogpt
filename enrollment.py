"""User enrollment helper for Ghosthand.

This module provides a small Tkinter-based wizard that guides new
users through the process of creating a profile and optionally
recording a voice sample for authentication.
"""

from __future__ import annotations

import tempfile
import tkinter as tk
from tkinter import messagebox, simpledialog

from logger import log
from user_profile import detect_user
from voice_auth import record_voice_sample, enroll_user, is_enrolled


def run_enrollment() -> None:
    """Launch the interactive enrollment wizard."""

    root = tk.Tk()
    root.withdraw()  # hide main window while using dialogs

    messagebox.showinfo(
        "Welcome",
        "Welcome to Ghosthand! This short setup will enrol you for a more personalised experience.",
    )

    username = simpledialog.askstring(
        "User Name", "Please enter your preferred user name:", initialvalue=detect_user()
    )
    if not username:
        messagebox.showinfo("Enrollment", "No user name entered. Enrollment cancelled.")
        root.destroy()
        return

    if is_enrolled(username):
        messagebox.showinfo("Enrollment", f"{username} is already enrolled.")
        root.destroy()
        return

    if messagebox.askyesno(
        "Voice Enrollment",
        "Would you like to enrol your voice for security? You'll record a short 5 second sample.",
    ):
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            try:
                record_voice_sample(tmp.name, 5)
                enroll_user(username, tmp.name)
                messagebox.showinfo(
                    "Enrollment", "Voice enrollment complete. You are all set!"
                )
            except Exception as exc:  # pragma: no cover - optional deps
                log(f"Enrollment failed: {exc}", "ERROR")
                messagebox.showerror(
                    "Enrollment", "Voice enrollment failed. You can try again later."
                )
    else:
        messagebox.showinfo(
            "Enrollment", "You can enrol your voice later from the main screen."
        )

    root.destroy()


if __name__ == "__main__":
    run_enrollment()
