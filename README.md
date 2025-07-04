# Ghosthand

Ghosthand is a desktop automation agent.  It accepts natural language instructions, plans a sequence of actions and then executes them using dedicated agent modules.  Results are stored in a SQLite memory database so that future runs can reference previous goals.

## Project layout

- `main.py` - CLI entry point and orchestrator.  It generates plans via `planner.generate_plan` and dispatches each step to the appropriate agent module.  Voice input/output and a simple Tkinter GUI are also available.
- `planner.py` - Translates free-form goals into structured action plans using keyword heuristics or GPT-4 when available.
- `memory.py` - Lightweight SQLite helper used to store goal history and provide fuzzy lookup of past tasks.
- `file_indexer.py` - Maintains an index of user files for quick searching.
- `agents/`
  - `file_agent.py` - File operations such as locating screenshots or redacting names in images.
  - `comms_agent.py` - Communication helpers for sending emails or generic webhook messages.
  - `ui_agent.py` - Desktop automation utilities built on `pyautogui`.
- `utils/ocr.py` - OCR helpers powered by `pytesseract`.
- `loyalty.py` - Enforces ownership and ethical rules.
- `security.py` - Basic identity verification helpers.
- `voice_auth.py` - Enrolls and verifies the owner's voiceprint.
- `core_guard.py` - Protects startup integrity and checks for tampering.
- `gui.py` - Optional Tkinter interface to run goals from a desktop panel.
- `chrome_extension/` - Optional browser extension that forwards web text to
  ChatGPT using the current session and relays the response back to Ghosthand.

This repository is a minimal working example rather than a production-ready assistant, but it demonstrates how different modules cooperate to perform complex multi-step tasks.

## Notes
- Many features rely on optional packages such as Whisper, spaCy and Playwright.
- Some functionality requires microphone and speaker access.
- Use caution and review the code before running in sensitive environments.
