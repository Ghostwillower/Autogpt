"""Utilities for downloading and extracting files."""

import os
import shutil
from pathlib import Path
from typing import Optional
import zipfile

import requests
from logger import log


def download_file(url: str, save_dir: str = "./downloads") -> str:
    """Download a file and return the saved path."""
    log(f"Downloading {url}", "WEB")
    try:
        Path(save_dir).mkdir(parents=True, exist_ok=True)
        filename = os.path.basename(url.split("?")[0]) or "download"
        path = Path(save_dir) / filename
        with requests.get(url, stream=True, timeout=30) as r:
            r.raise_for_status()
            with open(path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
        log(f"Saved {path} ({path.stat().st_size} bytes)", "WEB")
        return str(path)
    except Exception as exc:  # pragma: no cover - network dependent
        log(f"Download failed: {exc}", "ERROR")
        raise


def extract_file(path: str, extract_to: str) -> bool:
    """Extract or convert a file to a usable format."""
    log(f"Extracting {path} to {extract_to}")
    try:
        Path(extract_to).mkdir(parents=True, exist_ok=True)
        ext = Path(path).suffix.lower()
        if ext == ".zip":
            with zipfile.ZipFile(path, "r") as zf:
                zf.extractall(extract_to)
            log("Unzipped archive")
            return True
        elif ext == ".pdf":
            try:
                from pdfminer.high_level import extract_text

                text = extract_text(path)
                out_file = Path(extract_to) / (Path(path).stem + ".txt")
                out_file.write_text(text or "")
                log(f"Extracted PDF text to {out_file}")
                return True
            except Exception as exc:
                log(f"PDF extract failed: {exc}", "ERROR")
                return False
        elif ext == ".docx":
            try:
                import docx

                doc = docx.Document(path)
                text = "\n".join(p.text for p in doc.paragraphs)
                out_file = Path(extract_to) / (Path(path).stem + ".txt")
                out_file.write_text(text)
                log(f"Converted DOCX to text at {out_file}")
                return True
            except Exception as exc:
                log(f"DOCX extract failed: {exc}", "ERROR")
                return False
        elif ext == ".txt":
            dest = Path(extract_to) / Path(path).name
            shutil.copy(path, dest)
            log(f"Copied text file to {dest}")
            return True
        else:
            log(f"No extractor for {ext}", "WARNING")
            return False
    except Exception as exc:
        log(f"Extraction failed: {exc}", "ERROR")
        return False
