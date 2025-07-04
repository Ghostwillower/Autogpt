"""Agent responsible for file operations.

This module provides functions for reading from and writing to files as
well as helper utilities used by the planner, such as locating the most
recent screenshot or redacting names from an image.
"""

import glob
import os
from pathlib import Path
from typing import Optional, List

from logger import log
from file_indexer import search_index

import pytesseract
from PIL import Image, ImageFilter
import spacy

from utils.ocr import extract_text


def read_text(path: str, user: str = "") -> Optional[str]:
    """Read a text file if it exists."""
    p = Path(path)
    if p.exists():
        return p.read_text()
    return None


def write_text(path: str, content: str, user: str = "") -> None:
    """Write text to a file, creating parent directories if necessary."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)


def find_by_keywords(keywords: List[str], filetype: Optional[str] = None, user: str = "") -> List[str]:
    """Search indexed files for given keywords."""
    matches = search_index(keywords, filetype)
    log(f"find_by_keywords({keywords}) -> {matches}")
    return matches


def find_recent_screenshot(user: str = "") -> str:
    """Find the most recent screenshot in common folders.

    Searches the user's ``Downloads``, ``Pictures`` and ``Desktop`` folders
    for files containing ``"screenshot"`` in their filename and ending in
    ``.png`` or ``.jpg``. The most recently modified file is returned as an
    absolute path.
    Parameters
    ----------
    user : str, optional
        Identifier for the user requesting the screenshot; currently unused but
        kept for audit purposes.

    Returns
    -------
    str
        Absolute path to the most recent screenshot.
    """

    log("Searching for recent screenshot")
    home = Path.home()
    search_dirs = [home / "Downloads", home / "Pictures", home / "Desktop"]
    candidates = []

    for directory in search_dirs:
        if not directory.exists():
            continue
        for ext in ("*.png", "*.jpg", "*.jpeg"):
            for path in directory.glob(ext):
                if "screenshot" in path.name.lower():
                    candidates.append(path)

    if not candidates:
        log("No screenshots found in common folders", "INFO")
        matches = search_index(["screenshot"], None)
        for m in matches:
            if m.lower().endswith(('.png', '.jpg', '.jpeg')):
                candidates.append(Path(m))
        if not candidates:
            raise FileNotFoundError("No screenshot found in common folders")

    latest = max(candidates, key=lambda p: p.stat().st_mtime)
    latest_path = str(latest.resolve())
    log(f"Found screenshot: {latest_path}")
    return latest_path


def redact_names(image_path: str, user: str = "") -> str:
    """Detect and blur names in an image.

    This function performs OCR on ``image_path`` using ``pytesseract`` and
    runs the text through the small spaCy English model to locate ``PERSON``
    entities. Bounding boxes corresponding to detected name tokens are blurred
    with a Gaussian filter. A new image prefixed with ``redacted_`` is saved in
    the same directory and its path is returned.

    Parameters
    ----------
    image_path : str
        Path to the image that should be processed.
    user : str, optional
        Identifier for the user requesting the redaction.

    Returns
    -------
    str
        Path to the redacted image file.
    """

    log(f"Redacting names in {image_path}")

    try:
        text = extract_text(image_path) or ""
    except Exception as e:
        log(f"Failed to extract text: {e}", "ERROR")
        text = ""

    try:
        nlp = spacy.load("en_core_web_sm")
        doc = nlp(text)
        names = [ent.text for ent in doc.ents if ent.label_ == "PERSON"]
    except Exception as e:
        log(f"spaCy error: {e}", "ERROR")
        names = []

    if not names:
        log("No names detected; copying image")
        p = Path(image_path)
        out_path = p.with_name(f"redacted_{p.stem}.png")
        Image.open(image_path).save(out_path)
        return str(out_path)

    try:
        pil_img = Image.open(image_path)
        data = pytesseract.image_to_data(pil_img, output_type=pytesseract.Output.DICT)
        tokens = data.get("text", [])
    except Exception as e:
        log(f"OCR data extraction failed: {e}", "ERROR")
        tokens = []

    name_tokens = {w.lower() for n in names for w in n.split()}

    for i, word in enumerate(tokens):
        cleaned = word.strip().strip('.,:;!?').lower()
        if not cleaned:
            continue
        if cleaned in name_tokens:
            x, y = data["left"][i], data["top"][i]
            w, h = data["width"][i], data["height"][i]
            region = pil_img.crop((x, y, x + w, y + h))
            region = region.filter(ImageFilter.GaussianBlur(radius=8))
            pil_img.paste(region, (x, y))

    p = Path(image_path)
    redacted_path = p.with_name(f"redacted_{p.stem}.png")
    try:
        pil_img.save(redacted_path)
        log(f"Redacted image saved to: {redacted_path}")
    except Exception as e:
        log(f"Failed to save redacted image: {e}", "ERROR")
        redacted_path = p

    return str(redacted_path)
