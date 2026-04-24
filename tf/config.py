"""User configuration management. All data lives at ~/.thumbnail-forge/."""
import json
import os
import shutil
from pathlib import Path
from typing import Any

HOME_DIR = Path.home() / ".thumbnail-forge"
CONFIG_PATH = HOME_DIR / "config.json"
REFERENCES_DIR = HOME_DIR / "references"
COMPETITORS_PATH = HOME_DIR / "competitors.json"
VIDEOS_DIR = HOME_DIR / "videos"
CACHE_DIR = HOME_DIR / "cache"

DEFAULT_CONFIG: dict[str, Any] = {
    "version": "0.1.0",
    "gemini_api_key": "",
    "youtube_channel_url": "",
    "youtube_handle": "",
    "niche": "",
    "audience": "",
    "copyright_name": "",
    "face_preference": "no",
    "face_reference_path": "",
    "aesthetic": "warm_premium",
    "palette": {
        "bg_dark": "#1C1B19",
        "bg_light": "#F4EFE7",
        "accent": "#B8693A",
        "text": "#F4EFE7",
    },
    "forbidden_looks": [],
    "competitors": [],
    "reference_thumbnails": [],
    # Usage / telemetry
    "run_count": 0,
    "telemetry_consent": False,
    "coach_messages_enabled": True,
}


def increment_run_count() -> int:
    """Bump the thumb-command run counter and return the new value."""
    cfg = load()
    cfg["run_count"] = int(cfg.get("run_count", 0)) + 1
    save(cfg)
    return cfg["run_count"]


def ensure_dirs() -> None:
    """Create ~/.thumbnail-forge/ scaffold if missing."""
    for p in (HOME_DIR, REFERENCES_DIR, VIDEOS_DIR, CACHE_DIR):
        p.mkdir(parents=True, exist_ok=True)


def load() -> dict[str, Any]:
    """Load config. Returns DEFAULT_CONFIG merged with saved values."""
    ensure_dirs()
    if not CONFIG_PATH.exists():
        return dict(DEFAULT_CONFIG)
    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        saved = json.load(f)
    merged = dict(DEFAULT_CONFIG)
    merged.update(saved)
    return merged


def save(cfg: dict[str, Any]) -> None:
    ensure_dirs()
    with CONFIG_PATH.open("w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)


def is_onboarded() -> bool:
    """Check whether the user has finished onboarding."""
    if not CONFIG_PATH.exists():
        return False
    cfg = load()
    return bool(cfg.get("gemini_api_key")) and bool(cfg.get("youtube_channel_url"))


def store_reference(src: str | Path, index: int) -> Path:
    """Copy a reference thumbnail into ~/.thumbnail-forge/references/ and return new path.

    src may be a local file path. URLs are stored as-is in the config; only
    local files are copied.
    """
    ensure_dirs()
    src_path = Path(src).expanduser()
    if not src_path.exists():
        raise FileNotFoundError(f"Reference file not found: {src}")
    dest = REFERENCES_DIR / f"ref-{index:02d}{src_path.suffix.lower()}"
    shutil.copy2(src_path, dest)
    return dest


def video_dir(slug: str) -> Path:
    """Return ~/.thumbnail-forge/videos/<slug>/ ensuring it exists."""
    d = VIDEOS_DIR / slug
    (d / "out").mkdir(parents=True, exist_ok=True)
    return d


def slugify(title: str) -> str:
    """Simple URL-safe slug."""
    import re
    s = title.lower().strip()
    s = re.sub(r"[^a-z0-9\s-]", "", s)
    s = re.sub(r"[\s_-]+", "-", s)
    return s.strip("-")[:60] or "untitled"
