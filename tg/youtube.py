"""YouTube Data API v3 client.

Used during onboarding to validate competitor channel URLs and fetch basic
channel info (name, handle, sub count). Also supports fetching recent
thumbnails from a channel so users can auto-populate reference images.

All functions return None / empty collections on error — never raise. The
YouTube API key is OPTIONAL; when missing, validation silently degrades to
"just store the URL string as-is".
"""
from __future__ import annotations

import re
from typing import Optional

import requests


_API_BASE = "https://www.googleapis.com/youtube/v3"


# ─── URL parsing ───────────────────────────────────────────────────────────

def parse_channel_identifier(url: str) -> tuple[str, str]:
    """Parse a YouTube URL and return (kind, identifier).

    Kinds:
      - "handle": @thing
      - "channel": UCxxxxxxxxxxxxxxxxxxxxxx (24 chars)
      - "user": legacy /user/ URLs
      - "custom": /c/ URLs
      - "": unparseable
    """
    url = url.strip().rstrip("/")
    if not url:
        return ("", "")

    patterns = [
        ("handle", r"youtube\.com/@([\w.\-]+)"),
        ("channel", r"youtube\.com/channel/(UC[\w\-]+)"),
        ("user", r"youtube\.com/user/([\w.\-]+)"),
        ("custom", r"youtube\.com/c/([\w.\-]+)"),
    ]
    for kind, pat in patterns:
        m = re.search(pat, url)
        if m:
            return (kind, m.group(1))

    # Bare handle like "@thing"
    if url.startswith("@"):
        return ("handle", url.lstrip("@"))

    return ("", "")


# ─── Channel lookup ────────────────────────────────────────────────────────

def get_channel_info(url: str, api_key: str) -> Optional[dict]:
    """Fetch channel metadata. Returns dict or None on any error.

    Returned dict keys:
      id (channel ID)
      name (display title)
      handle (@custom URL if any)
      subscribers (int, 0 if hidden)
      thumbnail_url (small avatar)
      video_count (int)
    """
    if not api_key:
        return None

    kind, ident = parse_channel_identifier(url)
    if not kind:
        return None

    params: dict[str, str] = {"part": "snippet,statistics", "key": api_key}
    if kind == "handle":
        params["forHandle"] = "@" + ident
    elif kind == "channel":
        params["id"] = ident
    elif kind in ("user", "custom"):
        # Legacy URL types — forUsername still works for some
        params["forUsername"] = ident
    else:
        return None

    try:
        r = requests.get(f"{_API_BASE}/channels", params=params, timeout=10)
        if not r.ok:
            return None
        items = r.json().get("items", [])
        if not items:
            return None
        c = items[0]
        snippet = c.get("snippet", {})
        stats = c.get("statistics", {})
        return {
            "id": c.get("id", ""),
            "name": snippet.get("title", ""),
            "handle": snippet.get("customUrl", ""),
            "subscribers": int(stats.get("subscriberCount", 0)) if stats.get("subscriberCount") else 0,
            "thumbnail_url": snippet.get("thumbnails", {}).get("default", {}).get("url", ""),
            "video_count": int(stats.get("videoCount", 0)) if stats.get("videoCount") else 0,
        }
    except Exception:
        return None


# ─── Recent thumbnails ─────────────────────────────────────────────────────

def get_recent_thumbnails(channel_id: str, api_key: str, count: int = 5) -> list[dict]:
    """Return [{title, thumbnail_url, video_url}] for recent videos."""
    if not api_key or not channel_id:
        return []

    params = {
        "part": "snippet",
        "channelId": channel_id,
        "type": "video",
        "order": "date",
        "maxResults": str(min(max(count, 1), 10)),
        "key": api_key,
    }
    try:
        r = requests.get(f"{_API_BASE}/search", params=params, timeout=10)
        if not r.ok:
            return []
        items = r.json().get("items", [])
        out: list[dict] = []
        for item in items:
            snip = item.get("snippet", {})
            vid = item.get("id", {}).get("videoId", "")
            if not vid:
                continue
            thumbs = snip.get("thumbnails", {})
            thumb_url = (
                thumbs.get("maxres", {}).get("url")
                or thumbs.get("high", {}).get("url")
                or thumbs.get("medium", {}).get("url")
                or thumbs.get("default", {}).get("url", "")
            )
            out.append({
                "title": snip.get("title", ""),
                "thumbnail_url": thumb_url,
                "video_url": f"https://www.youtube.com/watch?v={vid}",
            })
        return out
    except Exception:
        return []


# ─── Formatting helpers ────────────────────────────────────────────────────

def humanize_subs(n: int) -> str:
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return str(n)
