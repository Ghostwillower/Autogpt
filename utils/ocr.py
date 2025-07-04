"""Utility module providing OCR capabilities.

Currently a stub demonstrating where text recognition functions would
live.
"""

from typing import Optional

import pytesseract
from PIL import Image


def extract_text(image_path: str, user: str = "") -> Optional[str]:
    """Extract text from an image using ``pytesseract``.

    Parameters
    ----------
    image_path : str
        Path to the image file.
    user : str, optional
        Identifier for the user requesting OCR.

    Returns
    -------
    str or None
        The recognised text or ``None`` if extraction failed.
    """

    print(f"[OCR] Extracting text from {image_path}")
    try:
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img)
        return text
    except Exception as e:
        print(f"[OCR] Failed to extract text: {e}")
        return None
