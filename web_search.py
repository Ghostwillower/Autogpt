"""Simple web search utilities for Ghosthand."""

import requests
from bs4 import BeautifulSoup

from logger import log


def search_web(query: str) -> dict:
    """Search the web and return a short summary and top links.

    Parameters
    ----------
    query : str
        Search query string.

    Returns
    -------
    dict
        Dictionary with ``summary`` text and a list of ``top_links``.
    """
    log(f"Searching the web for '{query}'", "WEB")
    try:
        resp = requests.get(
            "https://duckduckgo.com/html/",
            params={"q": query},
            timeout=30,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        links = []
        snippets = []
        for res in soup.select(".result"):
            link_tag = res.find("a", class_="result__a")
            if link_tag:
                links.append(link_tag.get("href"))
            snippet = res.find(class_="result__snippet")
            if snippet:
                snippets.append(snippet.get_text(strip=True))
            if len(links) >= 3:
                break
        summary = " ".join(snippets)[:200]
        log(f"Web search returned {len(links)} links", "WEB")
        return {"summary": summary, "top_links": links}
    except Exception as exc:  # pragma: no cover - network dependent
        log(f"Web search failed: {exc}", "ERROR")
        return {"summary": "", "top_links": []}
