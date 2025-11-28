# keepa_client.py
import os
import re

import keepa
from dotenv import load_dotenv

# Load variables from .env
load_dotenv()

KEEPA_API_KEY = os.getenv("KEEPA_API_KEY")

if not KEEPA_API_KEY:
    raise ValueError("KEEPA_API_KEY is not set in .env")

# Create Keepa client
api = keepa.Keepa(KEEPA_API_KEY)

def extract_asin_from_input(identifier: str) -> str | None:
    """
    Accepts either:
      - a plain ASIN (e.g. 'B0DJ33ZFJH'), or
      - a full Amazon URL

    Returns just the ASIN (UPPERCASE) or None if not found.
    """
    # Work with the raw string first
    ident = identifier.strip()

    # If it's exactly a 10-char ASIN (letters or numbers)
    if re.fullmatch(r"[A-Za-z0-9]{10}", ident):
        return ident.upper()

    # Try to extract ASIN from URL (case-insensitive)
    m = re.search(r"/dp/([A-Za-z0-9]{10})", ident, flags=re.IGNORECASE)
    if not m:
        m = re.search(r"/gp/product/([A-Za-z0-9]{10})", ident, flags=re.IGNORECASE)

    if m:
        return m.group(1).upper()

    return None



def get_listing_from_keepa(identifier: str, domain: str = "US") -> dict:
    """
    Given an ASIN or Amazon URL, returns:

      {
        "asin": ...,
        "title": ...,
        "bullets": [ ...list of bullet strings... ],
        "description": ...
      }

    Raises ValueError if anything important goes wrong.
    """
    asin = extract_asin_from_input(identifier)
    if not asin:
        raise ValueError(f"Could not find a valid ASIN in: {identifier}")

    # Query Keepa
    products = api.query(asin, domain=domain)
    if not products:
        raise ValueError(f"Keepa returned no product for ASIN {asin}")

    product = products[0]

    title = product.get("title") or ""
    bullets = product.get("features") or []  # usually list of strings
    description = product.get("description") or ""

    return {
        "asin": asin,
        "title": title,
        "bullets": bullets,
        "description": description,
    }
