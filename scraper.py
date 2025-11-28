import re
import requests
from bs4 import BeautifulSoup

# A simple User-Agent so Amazon treats us more like a normal browser
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


def extract_asin(identifier: str) -> str | None:
    """
    Accepts either:
    - A raw ASIN like 'B0DJ33ZFJH'
    - A full Amazon URL
    and tries to extract the ASIN.

    Returns the ASIN string or None if it can't find one.
    """
    identifier = identifier.strip()

    # If it looks like a pure ASIN (10 characters, letters/numbers)
    if re.fullmatch(r"[A-Z0-9]{10}", identifier, flags=re.IGNORECASE):
        return identifier.upper()

    # Try to extract ASIN from URL
    # Common patterns: /dp/ASIN, /gp/product/ASIN
    match = re.search(r"/(dp|gp/product)/([A-Z0-9]{10})", identifier, flags=re.IGNORECASE)
    if match:
        return match.group(2).upper()

    return None


def fetch_listing_by_asin(asin: str) -> dict:
    """
    Fetches the Amazon product page for the given ASIN and tries to extract:
    - title
    - bullets (as a single string with newlines)
    - description (short/medium text if available)

    Returns a dict with keys: 'asin', 'title', 'bullets', 'description'
    Any missing field will be set to "".
    """
    url = f"https://www.amazon.com/dp/{asin}"
    resp = requests.get(url, headers=HEADERS, timeout=15)

    if resp.status_code != 200:
        return {
            "asin": asin,
            "title": "",
            "bullets": "",
            "description": "",
            "error": f"HTTP {resp.status_code} when fetching {url}",
        }

    soup = BeautifulSoup(resp.text, "lxml")

    # Title
    title_el = soup.select_one("#productTitle")
    title = title_el.get_text(strip=True) if title_el else ""

    # Bullets: typically under #feature-bullets
    bullet_els = soup.select("#feature-bullets ul li span")
    bullets_list = []

    for b in bullet_els:
        txt = b.get_text(" ", strip=True)
        # Skip empty or 'Add to Cart' weird things
        if txt and "click to open expanded" not in txt.lower():
            bullets_list.append(txt)

    bullets = "\n".join(f"- {b}" for b in bullets_list)

    # Description: this is messy on Amazon, but we can try a few common spots
    desc = ""

    # Try classic productDescription div
    desc_el = soup.select_one("#productDescription")
    if desc_el:
        desc = desc_el.get_text(" ", strip=True)

    # Fallback: sometimes description is in #bookDescription_feature_div or others.
    if not desc:
        alt_desc_el = soup.select_one("#bookDescription_feature_div")
        if alt_desc_el:
            desc = alt_desc_el.get_text(" ", strip=True)

    # If still empty, you might later parse A+ content, but that's more complex.
    return {
        "asin": asin,
        "title": title or "",
        "bullets": bullets or "",
        "description": desc or "",
        "error": "",
    }


def fetch_listing(identifier: str) -> dict:
    """
    Public helper:
    - Takes either an ASIN or an Amazon URL.
    - Extracts ASIN.
    - Fetches listing via fetch_listing_by_asin.

    Returns a dict like fetch_listing_by_asin, but with 'error' if ASIN is invalid.
    """
    asin = extract_asin(identifier)
    if not asin:
        return {
            "asin": "",
            "title": "",
            "bullets": "",
            "description": "",
            "error": f"Could not extract ASIN from: {identifier}",
        }

    return fetch_listing_by_asin(asin)
