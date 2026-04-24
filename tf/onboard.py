"""Onboarding wizard. Run on first use via `tf onboard`."""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import click
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, IntPrompt, Prompt

from . import brand, config


console = Console()

_AESTHETIC_PRESETS = [
    {
        "id": "warm_premium",
        "name": "Warm Premium",
        "desc": "Dark moody studio, warm rim light, bone + terracotta palette. Editorial feel (Monocle, Kinfolk).",
        "palette": {"bg_dark": "#1C1B19", "bg_light": "#F4EFE7", "accent": "#B8693A", "text": "#F4EFE7"},
    },
    {
        "id": "high_contrast",
        "name": "High Contrast Tech",
        "desc": "Deep black, electric-blue accent, fog. Developer / AI channel energy.",
        "palette": {"bg_dark": "#000000", "bg_light": "#F5F5F7", "accent": "#00B2FF", "text": "#F5F5F7"},
    },
    {
        "id": "playful_retro",
        "name": "Playful Retro",
        "desc": "Chunky fonts, bright accent, fun energy. Creator/comedy channel style.",
        "palette": {"bg_dark": "#2A1A3F", "bg_light": "#FFEDA1", "accent": "#FF3E7F", "text": "#FFFFFF"},
    },
    {
        "id": "clean_minimal",
        "name": "Clean Minimal",
        "desc": "Off-white, sans-serif, lots of whitespace. Iman Gadzhi / Dan Koe territory.",
        "palette": {"bg_dark": "#1A1A1A", "bg_light": "#FAFAFA", "accent": "#0A0A0A", "text": "#1A1A1A"},
    },
    {
        "id": "destruction",
        "name": "Apocalyptic",
        "desc": "Cracked ground, embers, 'X is dead' energy. For controversial call-outs.",
        "palette": {"bg_dark": "#0D0A08", "bg_light": "#F4EFE7", "accent": "#FF4500", "text": "#F4EFE7"},
    },
]


def run() -> None:
    """Full onboarding flow."""
    console.print(Panel.fit(brand.welcome_banner().strip(), border_style="yellow"))
    console.print()
    console.print("[bold]Welcome.[/bold] This takes ~10 minutes. Answers save to [cyan]~/.thumbnail-forge/[/cyan].\n")

    cfg = config.load()

    if config.is_onboarded():
        if not Confirm.ask("[yellow]You're already onboarded. Re-run anyway?[/yellow]", default=False):
            console.print("Exiting. Run [cyan]tf thumb[/cyan] to generate a thumbnail.")
            return

    cfg = _step_api_key(cfg)
    cfg = _step_channel(cfg)
    cfg = _step_niche(cfg)
    cfg = _step_face(cfg)
    cfg = _step_aesthetic(cfg)
    cfg = _step_forbidden(cfg)
    cfg = _step_references(cfg)
    cfg = _step_competitors(cfg)
    cfg = _step_copyright(cfg)

    config.save(cfg)

    console.print()
    console.print(Panel.fit(
        "[bold green]Setup complete.[/bold green]\n\n"
        "Next step:\n"
        "  [cyan]tf thumb --transcript path/to/video.txt --title \"My Video Title\"[/cyan]\n\n"
        "Or interactive:\n"
        "  [cyan]tf thumb[/cyan]",
        border_style="green",
    ))
    console.print()
    console.print(f"[dim]{brand.FOOTER_SHORT}[/dim]")


# ─── Steps ─────────────────────────────────────────────────────────────────

def _step_api_key(cfg: dict[str, Any]) -> dict[str, Any]:
    console.print("[bold yellow][1/9][/bold yellow] Gemini API key")
    console.print("Get a free one at https://aistudio.google.com")
    existing = cfg.get("gemini_api_key", "")
    if existing:
        if Confirm.ask(f"Keep existing key (ending ...{existing[-4:]})?", default=True):
            return cfg
    key = Prompt.ask("Paste your Gemini API key", password=True)
    cfg["gemini_api_key"] = key.strip()
    console.print("[green]✓[/green] Saved.\n")
    return cfg


def _step_channel(cfg: dict[str, Any]) -> dict[str, Any]:
    console.print("[bold yellow][2/9][/bold yellow] Your channel")
    url = Prompt.ask(
        "YouTube channel URL", default=cfg.get("youtube_channel_url", "")
    )
    cfg["youtube_channel_url"] = url.strip()
    match = re.search(r"@([\w.-]+)", url)
    cfg["youtube_handle"] = f"@{match.group(1)}" if match else ""
    console.print(f"[green]✓[/green] Handle: [cyan]{cfg['youtube_handle']}[/cyan]\n")
    return cfg


def _step_niche(cfg: dict[str, Any]) -> dict[str, Any]:
    console.print("[bold yellow][3/9][/bold yellow] What's the channel about?")
    cfg["niche"] = Prompt.ask(
        "Niche (one sentence)", default=cfg.get("niche", "")
    ).strip()
    cfg["audience"] = Prompt.ask(
        "Who's your audience? (one line)", default=cfg.get("audience", "")
    ).strip()
    console.print()
    return cfg


def _step_face(cfg: dict[str, Any]) -> dict[str, Any]:
    console.print("[bold yellow][4/9][/bold yellow] Face in thumbnails?")
    choice = Prompt.ask(
        "Include your face in thumbnails?",
        choices=["yes", "no", "optional"],
        default=cfg.get("face_preference", "no"),
    )
    cfg["face_preference"] = choice
    if choice != "no":
        path = Prompt.ask(
            "Path to reference portrait (leave blank to set later)",
            default=cfg.get("face_reference_path", ""),
        )
        if path:
            p = Path(path).expanduser()
            if p.exists():
                cfg["face_reference_path"] = str(p)
                console.print(f"[green]✓[/green] Saved portrait path.")
            else:
                console.print(f"[red]✗[/red] File not found. Skipping.")
    console.print()
    return cfg


def _step_aesthetic(cfg: dict[str, Any]) -> dict[str, Any]:
    console.print("[bold yellow][5/9][/bold yellow] Aesthetic preset")
    for i, preset in enumerate(_AESTHETIC_PRESETS, 1):
        console.print(f"  [cyan]{i}.[/cyan] [bold]{preset['name']}[/bold]")
        console.print(f"     {preset['desc']}")
    console.print(f"  [cyan]{len(_AESTHETIC_PRESETS)+1}.[/cyan] Custom (define your own)")

    default_idx = 1
    for i, p in enumerate(_AESTHETIC_PRESETS, 1):
        if p["id"] == cfg.get("aesthetic"):
            default_idx = i
            break

    choice = IntPrompt.ask("Pick one", default=default_idx, show_default=True)
    if 1 <= choice <= len(_AESTHETIC_PRESETS):
        preset = _AESTHETIC_PRESETS[choice - 1]
        cfg["aesthetic"] = preset["id"]
        cfg["palette"] = preset["palette"]
    else:
        cfg["aesthetic"] = "custom"
        console.print("Custom palette:")
        cfg["palette"] = {
            "bg_dark": Prompt.ask("  Dark background hex", default="#1C1B19"),
            "bg_light": Prompt.ask("  Light background hex", default="#F4EFE7"),
            "accent": Prompt.ask("  Accent hex", default="#B8693A"),
            "text": Prompt.ask("  Text hex", default="#F4EFE7"),
        }
    console.print()
    return cfg


def _step_forbidden(cfg: dict[str, Any]) -> dict[str, Any]:
    console.print("[bold yellow][6/9][/bold yellow] Forbidden looks")
    console.print("What do you [bold]NOT[/bold] want? (e.g. 'no ring lights, no stock photos, no yellow arrows')")
    existing = ", ".join(cfg.get("forbidden_looks", []))
    raw = Prompt.ask("Comma-separated", default=existing)
    cfg["forbidden_looks"] = [x.strip() for x in raw.split(",") if x.strip()]
    console.print()
    return cfg


def _step_references(cfg: dict[str, Any]) -> dict[str, Any]:
    console.print("[bold yellow][7/9][/bold yellow] Reference thumbnails")
    console.print(
        "Paste up to 10 URLs or local paths of thumbnails you love. "
        "These define your target aesthetic. Empty line to finish."
    )
    refs = []
    for i in range(1, 11):
        ref = Prompt.ask(f"  Ref {i}", default="")
        if not ref:
            break
        refs.append(ref.strip())
    cfg["reference_thumbnails"] = refs
    console.print(f"[green]✓[/green] Saved {len(refs)} references.\n")
    return cfg


def _step_competitors(cfg: dict[str, Any]) -> dict[str, Any]:
    console.print("[bold yellow][8/9][/bold yellow] Competitor channels")
    console.print("3-5 creators whose thumbnails you want to compete with.")
    comps = []
    for i in range(1, 6):
        c = Prompt.ask(f"  Competitor {i} (name or handle)", default="")
        if not c:
            break
        comps.append(c.strip())
    cfg["competitors"] = comps
    console.print(f"[green]✓[/green] Saved {len(comps)} competitors.\n")
    return cfg


def _step_copyright(cfg: dict[str, Any]) -> dict[str, Any]:
    console.print("[bold yellow][9/9][/bold yellow] Copyright / attribution")
    cfg["copyright_name"] = Prompt.ask(
        "Name to embed in PNG metadata",
        default=cfg.get("copyright_name", cfg.get("youtube_handle", "").lstrip("@") or "Your Name"),
    )
    console.print()
    return cfg
