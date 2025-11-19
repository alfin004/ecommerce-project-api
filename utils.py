import csv
import io
from typing import List, Dict
import requests


def sheet_link_to_csv_url(sheet_url: str) -> str:
    """Convert a standard Google Sheet URL to an export=csv URL."""
    if not sheet_url:
        raise ValueError("Sheet URL is empty")
    if "export?format=csv" in sheet_url:
        return sheet_url
    if "/edit" in sheet_url:
        base, _, tail = sheet_url.partition("/edit")
        gid = "0"
        if "gid=" in tail:
            after_gid = tail.split("gid=", 1)[1]
            gid = gid.split("&", 1)[0]
        return f"{base}/export?format=csv&gid={gid}"
    # Fallback
    return sheet_url.rstrip("/") + "/export?format=csv"


def fetch_sheet_rows(sheet_url: str) -> List[Dict[str, str]]:
    csv_url = sheet_link_to_csv_url(sheet_url)
    resp = requests.get(csv_url)
    resp.raise_for_status()
    content = resp.content.decode("utf-8")
    reader = csv.DictReader(io.StringIO(content))
    return list(reader)
