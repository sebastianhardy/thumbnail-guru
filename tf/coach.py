"""Coach: rotating tips, asks, and asides that appear after generation.

Triggers:
  - Milestone runs (1, 3, 5, 10, 25, 50): fixed message from the milestone bank.
  - Every 3rd non-milestone run OR 33% random chance: rotate through the tips,
    social invites, podcast nudges, and funny messages.

Messages live in `data/coach_messages.yaml` so they can be edited without
touching Python.
"""
from __future__ import annotations

import random
from pathlib import Path
from typing import Any

import yaml

from . import brand


_DATA_PATH = Path(__file__).parent.parent / "data" / "coach_messages.yaml"
_MILESTONE_RUNS = {1, 3, 5, 10, 25, 50}


def _load() -> dict[str, Any]:
    with _DATA_PATH.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _fmt(text: str, run_count: int) -> str:
    return (
        text.replace("{linkedin_url}", brand.LINKEDIN_URL)
            .replace("{instagram_url}", brand.INSTAGRAM_URL)
            .replace("{instagram_handle}", brand.INSTAGRAM_HANDLE)
            .replace("{youtube_url}", brand.YOUTUBE_URL)
            .replace("{youtube_handle}", brand.YOUTUBE_HANDLE)
            .replace("{skool_url}", brand.SKOOL_URL)
            .replace("{run_count}", str(run_count))
            .strip()
    )


def pick_message(run_count: int, *, force_category: str | None = None) -> str | None:
    """Return a coaching message string, or None if no message should show.

    Logic:
      - Milestone runs (1, 3, 5, 10, 25, 50): fixed milestone message.
      - Every 3rd run OR 33% random: pick from the rotating pools.
      - Otherwise: return None (no message).
    """
    data = _load()

    if run_count in _MILESTONE_RUNS:
        milestones = data.get("milestones", {})
        msg = milestones.get(run_count) or milestones.get(str(run_count))
        if msg:
            return _fmt(msg, run_count)

    # Rotate every 3rd run OR 33% random chance
    should_show = (run_count % 3 == 0) or (random.random() < 0.33)
    if not should_show:
        return None

    # Pick category — weight growth_tips higher than the others
    categories = force_category or _weighted_category()
    pool = data.get(categories, [])
    if not pool:
        return None
    return _fmt(random.choice(pool), run_count)


def _weighted_category() -> str:
    """Weighted random category pick.
    50% more_content (archive/YouTube), 20% community (Skool),
    20% social_invites (LinkedIn/IG), 10% funny.
    """
    roll = random.random()
    if roll < 0.50:
        return "more_content"
    if roll < 0.70:
        return "community"
    if roll < 0.90:
        return "social_invites"
    return "funny"


def format_for_terminal(message: str) -> str:
    """Wrap message in a soft banner for the terminal."""
    if not message:
        return ""
    lines = message.split("\n")
    width = max(60, min(72, max(len(l) for l in lines) + 4))
    top = "┌" + "─" * (width - 2) + "┐"
    bot = "└" + "─" * (width - 2) + "┘"
    content = "\n".join(f"│ {l.ljust(width - 4)} │" for l in lines)
    return f"\n{top}\n{content}\n{bot}"
