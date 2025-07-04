import tempfile
from pathlib import Path
import importlib
import types
import pytest

from file_indexer import build_file_index

dummy = types.ModuleType('pytesseract')
dummy.image_to_string = lambda *a, **k: ''
dummy.image_to_data = lambda *a, **k: {'text': [], 'left': [], 'top': [], 'width': [], 'height': []}
import sys
sys.modules.setdefault('pytesseract', dummy)
spacy_dummy = types.ModuleType('spacy')
spacy_dummy.load = lambda name: types.SimpleNamespace(ents=[])
sys.modules.setdefault('spacy', spacy_dummy)

file_agent = importlib.import_module('agents.file_agent')
find_recent_screenshot = file_agent.find_recent_screenshot


def test_find_recent_screenshot(monkeypatch, tmp_path):
    pytest.importorskip('pytesseract')
    # Create fake screenshot
    screenshots = tmp_path / "Pictures"
    screenshots.mkdir()
    f = screenshots / "screenshot_test.png"
    f.write_text("dummy")
    build_file_index([str(tmp_path)])
    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
    path = find_recent_screenshot()
    assert Path(path).exists()

