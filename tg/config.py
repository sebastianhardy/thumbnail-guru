"""User configuration management. All data lives at ~/.thumbnail-guru/."""
import json
import os
import shutil
from pathlib import Path
from typing import Any

HOME_DIR = Path.home() / ".thumbnail-guru"
CONFIG_PATH = HOME_DIR / "config.json"
ENV_PATH = HOME_DIR / ".env"
REFERENCES_DIR = HOME_DIR / "references"
COMPETITORS_PATH = HOME_DIR / "competitors.json"
VIDEOS_DIR = HOME_DIR / "videos"
CACHE_DIR = HOME_DIR / "cache"

DEFAULT_CONFIG: dict[str, Any] = {
    "version": "0.2.0",
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
    # Usage
    "run_count": 0,
    "coach_messages_enabled": True,
}


# ─── .env file support ─────────────────────────────────────────────────────
# API keys live in ~/.thumbnail-guru/.env (not in config.json) so they can
# be edited directly, rotated, or overridden via env vars.

def load_env() -> dict[str, str]:
    """Load ~/.thumbnail-guru/.env into a dict. Returns {} if missing."""
    if not ENV_PATH.exists():
        return {}
    out: dict[str, str] = {}
    for raw in ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        k, _, v = line.partition("=")
        out[k.strip()] = v.strip().strip("'\"")
    return out


def write_env(keys: dict[str, str]) -> None:
    """Merge-and-write keys into ~/.thumbnail-guru/.env.
    Preserves existing keys not in the update dict.
    """
    ensure_dirs()
    existing = load_env()
    existing.update({k: v for k, v in keys.items() if v})
    lines = [
        "# Thumbnail Guru API keys. Do not commit this file.",
        "# Regenerate any key at any time — just paste the new value below.",
        "",
    ]
    for k, v in existing.items():
        lines.append(f"{k}={v}")
    ENV_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    try:
        ENV_PATH.chmod(0o600)  # owner-only read/write
    except OSError:
        pass


def gemini_api_key() -> str:
    """Return the Gemini API key. Order: .env → env var → empty."""
    return (
        load_env().get("GEMINI_API_KEY", "")
        or os.environ.get("GEMINI_API_KEY", "")
        or ""
    )


def youtube_api_key() -> str:
    """Return the YouTube API key. Optional — empty if user skipped."""
    return (
        load_env().get("YOUTUBE_API_KEY", "")
        or os.environ.get("YOUTUBE_API_KEY", "")
        or ""
    )


def increment_run_count() -> int:
    """Bump the thumb-command run counter and return the new value."""
    cfg = load()
    cfg["run_count"] = int(cfg.get("run_count", 0)) + 1
    save(cfg)
    return cfg["run_count"]


def ensure_dirs() -> None:
    """Create ~/.thumbnail-guru/ scaffold if missing."""
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
    """Check whether the user has finished onboarding.

    Two conditions:
      1. A Gemini API key exists (required).
      2. The user has gone through the full wizard (a YouTube channel URL
         is the proxy — it's the last required step before optional ones).
    """
    if not CONFIG_PATH.exists():
        return False
    if not gemini_api_key():
        return False
    cfg = load()
    return bool(cfg.get("youtube_channel_url"))


def store_reference(src: str | Path, index: int) -> Path:
    """Copy a reference thumbnail into ~/.thumbnail-guru/references/ and return new path.

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
    """Return ~/.thumbnail-guru/videos/<slug>/ ensuring it exists."""
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
