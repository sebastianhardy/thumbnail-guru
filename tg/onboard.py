"""Beginner-friendly onboarding wizard. Walks the user through every
decision needed to generate their first thumbnail — like a friend sitting
next to you, not a terse questionnaire.

Invoked by `tg onboard` or automatically the first time `tg` runs.
"""
from __future__ import annotations

import re
import webbrowser
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, IntPrompt, Prompt
from rich.table import Table

from . import brand, config, youtube as yt_api


console = Console()

_AESTHETIC_PRESETS = [
    {
        "id": "warm_premium",
        "name": "Warm Premium",
        "desc": "Dark moody studio, warm rim light, editorial Monocle / Kinfolk feel.",
        "palette": {"bg_dark": "#1C1B19", "bg_light": "#F4EFE7", "accent": "#B8693A", "text": "#F4EFE7"},
    },
    {
        "id": "high_contrast",
        "name": "High Contrast Tech",
        "desc": "Deep black, electric-blue accent. Developer / AI channel energy.",
        "palette": {"bg_dark": "#000000", "bg_light": "#F5F5F7", "accent": "#00B2FF", "text": "#F5F5F7"},
    },
    {
        "id": "playful_retro",
        "name": "Playful Retro",
        "desc": "Chunky fonts, bright accent, fun energy. Creator / comedy style.",
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
        "desc": "Cracked ground, embers. For 'X is dead' / controversial videos.",
        "palette": {"bg_dark": "#0D0A08", "bg_light": "#F4EFE7", "accent": "#FF4500", "text": "#F4EFE7"},
    },
]


# ─── Main entry ────────────────────────────────────────────────────────────

def run() -> None:
    """Full onboarding flow — conversational, explains each step."""
    console.print(brand.welcome_banner())
    console.print(
        "[bold]Hey. I'm going to help you set up Thumbnail Guru.[/bold]\n\n"
        "Takes about 10 minutes. I'll walk you through every step — no skipping.\n"
        "Everything is saved to [cyan]~/.thumbnail-guru/[/cyan] on your machine.\n"
    )

    cfg = config.load()
    already = config.is_onboarded()
    if already:
        if not Confirm.ask(
            "[yellow]You're already set up. Re-run the wizard anyway?[/yellow]",
            default=False,
        ):
            console.print("\nAll good. Try [cyan]tg thumb --title \"Your video\"[/cyan].")
            return
        console.print()

    Prompt.ask("[dim]Press Enter when you're ready[/dim]", default="", show_default=False)
    console.print()

    # ── Keys first, then content ──
    _step_gemini_key()
    yt_key = _step_youtube_key()
    cfg = _step_channel(cfg, yt_key)
    cfg = _step_niche(cfg)
    cfg = _step_competitors(cfg, yt_key)
    cfg = _step_aesthetic(cfg)
    cfg = _step_face(cfg)
    cfg = _step_forbidden(cfg)
    cfg = _step_copyright(cfg)

    config.save(cfg)

    _print_summary(cfg, yt_key)


# ─── Step 1: Gemini API key ────────────────────────────────────────────────

def _step_gemini_key() -> str:
    console.print(Panel(
        "[bold yellow]STEP 1 · Gemini API key[/bold yellow]  [dim](required)[/dim]\n\n"
        "Thumbnail Guru uses Google's [bold]Nano Banana Pro[/bold] (Gemini 3 Pro Image)\n"
        "to generate thumbnails. You need a free API key — 30 seconds to get one.\n\n"
        "[bold]How to get it:[/bold]\n"
        "  [cyan]1.[/cyan] Open [link]https://aistudio.google.com[/link] in your browser\n"
        "  [cyan]2.[/cyan] Sign in with your Google account\n"
        "  [cyan]3.[/cyan] Click [bold]Get API Key[/bold] (top-left menu)\n"
        "  [cyan]4.[/cyan] Click [bold]Create API Key[/bold]\n"
        "  [cyan]5.[/cyan] Copy the long string that starts with [cyan]AIza...[/cyan]\n\n"
        "[yellow]Heads up on pricing:[/yellow] the free tier covers light usage (a few\n"
        "thumbnails per day is fine). Heavy volume may incur small charges from Google.\n"
        "Check AI Studio for current rates.",
        border_style="yellow",
    ))

    if Confirm.ask("Open aistudio.google.com in your browser now?", default=True):
        webbrowser.open("https://aistudio.google.com")

    existing = config.gemini_api_key()
    while True:
        prompt_text = "Paste your Gemini API key"
        if existing:
            prompt_text += f" (press Enter to keep existing ...{existing[-4:]})"
        key = Prompt.ask(prompt_text, password=True, default=existing)
        if key and (key.startswith("AIza") or len(key) >= 30):
            break
        console.print("[red]✗[/red] That doesn't look like a valid key. Try again.")

    config.write_env({"GEMINI_API_KEY": key})
    console.print("[green]✓[/green] Saved to ~/.thumbnail-guru/.env\n")
    return key


# ─── Step 2: YouTube API key (optional) ────────────────────────────────────

def _step_youtube_key() -> str:
    console.print(Panel(
        "[bold yellow]STEP 2 · YouTube API key[/bold yellow]  [dim](optional, but recommended)[/dim]\n\n"
        "With a YouTube API key, Thumbnail Guru can:\n"
        "  • Validate competitor channel URLs as you paste them\n"
        "  • Show channel name and subscriber count for confirmation\n"
        "  • Auto-fetch recent thumbnails from competitors as style references\n\n"
        "Skip this if you just want to type URLs manually — you can come back later.",
        border_style="yellow",
    ))

    if not Confirm.ask("Add a YouTube API key now?", default=True):
        console.print("[dim]Skipping. Competitor URLs will be stored without validation.[/dim]\n")
        return ""

    console.print(
        "\n[bold]How to get it[/bold] (takes 2 minutes):\n"
        "  [cyan]1.[/cyan] Open [link]https://console.cloud.google.com[/link]\n"
        "  [cyan]2.[/cyan] Create a new project (name it anything, e.g. [cyan]thumbnail-guru[/cyan])\n"
        "  [cyan]3.[/cyan] Search for [bold]YouTube Data API v3[/bold] and click [bold]Enable[/bold]\n"
        "  [cyan]4.[/cyan] Click [bold]Credentials[/bold] in the left sidebar\n"
        "  [cyan]5.[/cyan] Click [bold]+ Create Credentials[/bold] → [bold]API key[/bold]\n"
        "  [cyan]6.[/cyan] Copy the key.\n"
    )

    if Confirm.ask("Open Google Cloud Console now?", default=True):
        webbrowser.open("https://console.cloud.google.com/apis/library/youtube.googleapis.com")

    existing = config.youtube_api_key()
    prompt_text = "Paste your YouTube API key (or press Enter to skip)"
    if existing:
        prompt_text += f" — existing ...{existing[-4:]}"
    key = Prompt.ask(prompt_text, password=True, default=existing or "", show_default=False)
    key = key.strip()
    if not key:
        console.print("[dim]Skipped.[/dim]\n")
        return ""

    config.write_env({"YOUTUBE_API_KEY": key})
    console.print("[green]✓[/green] Saved.\n")
    return key


# ─── Step 3: Your channel ──────────────────────────────────────────────────

def _step_channel(cfg: dict[str, Any], yt_key: str) -> dict[str, Any]:
    console.print(Panel(
        "[bold yellow]STEP 3 · Your YouTube channel[/bold yellow]\n\n"
        "Paste your channel URL. Looks like:\n"
        "  [cyan]https://www.youtube.com/@yourhandle[/cyan]",
        border_style="yellow",
    ))

    while True:
        url = Prompt.ask("Your channel URL", default=cfg.get("youtube_channel_url", "")).strip()
        if not url:
            console.print("[red]✗[/red] Need a channel URL to continue.")
            continue
        cfg["youtube_channel_url"] = url
        m = re.search(r"@([\w.-]+)", url)
        if m:
            cfg["youtube_handle"] = f"@{m.group(1)}"

        if yt_key:
            info = yt_api.get_channel_info(url, yt_key)
            if info:
                console.print(
                    f"[green]✓[/green] Found: [bold]{info['name']}[/bold] · "
                    f"{yt_api.humanize_subs(info['subscribers'])} subs · "
                    f"{info['video_count']} videos"
                )
                break
            else:
                console.print("[yellow]⚠[/yellow] Couldn't validate that URL. Check for typos?")
                if not Confirm.ask("Use it anyway?", default=False):
                    continue
                break
        else:
            console.print("[dim]  (skipped validation — no YouTube API key)[/dim]")
            break
    console.print()
    return cfg


# ─── Step 4: Niche + audience ──────────────────────────────────────────────

def _step_niche(cfg: dict[str, Any]) -> dict[str, Any]:
    console.print(Panel(
        "[bold yellow]STEP 4 · What's your channel about?[/bold yellow]\n\n"
        "This shapes which hook patterns get picked for your thumbnails.\n"
        "A cooking channel needs different hooks than an AI-for-founders channel.",
        border_style="yellow",
    ))

    cfg["niche"] = Prompt.ask(
        "Your niche in one sentence (e.g. 'AI workflows for agency owners')",
        default=cfg.get("niche", ""),
    ).strip()

    cfg["audience"] = Prompt.ask(
        "Your audience in one line (e.g. 'solo founders 28-45 who are time-poor')",
        default=cfg.get("audience", ""),
    ).strip()
    console.print()
    return cfg


# ─── Step 5: 5 competitor channels ─────────────────────────────────────────

def _step_competitors(cfg: dict[str, Any], yt_key: str) -> dict[str, Any]:
    console.print(Panel(
        "[bold yellow]STEP 5 · Your 5 competitors[/bold yellow]\n\n"
        "Paste 5 YouTube channel URLs of creators in your niche whose thumbnails\n"
        "you want to [bold]beat or match[/bold]. These drive two things:\n\n"
        "  • Reference aesthetic for your own brand\n"
        "  • 'Competitor shattered' compositions (when your hook pattern calls for it)\n\n"
        "URL format: [cyan]https://www.youtube.com/@handle[/cyan]",
        border_style="yellow",
    ))

    competitors: list[dict[str, Any]] = []
    for i in range(1, 6):
        while True:
            url = Prompt.ask(
                f"Competitor {i}/5" + ("" if i > 1 else " [dim](or Enter to skip this step)[/dim]"),
                default="",
            ).strip()
            if not url:
                if i == 1:
                    console.print("[dim]Skipping competitors. You can add them later.[/dim]\n")
                    return cfg
                return _finalize_competitors(cfg, competitors)

            entry: dict[str, Any] = {"url": url}
            if yt_key:
                info = yt_api.get_channel_info(url, yt_key)
                if info:
                    entry.update({
                        "id": info["id"],
                        "name": info["name"],
                        "handle": info["handle"],
                        "subscribers": info["subscribers"],
                    })
                    console.print(
                        f"  [green]✓[/green] [bold]{info['name']}[/bold] · "
                        f"{yt_api.humanize_subs(info['subscribers'])} subs"
                    )
                    competitors.append(entry)
                    break
                else:
                    console.print("  [yellow]⚠[/yellow] Couldn't validate. Typo?")
                    if Confirm.ask("  Use it anyway?", default=False):
                        competitors.append(entry)
                        break
            else:
                competitors.append(entry)
                console.print("  [dim](saved, no validation)[/dim]")
                break

    return _finalize_competitors(cfg, competitors)


def _finalize_competitors(cfg: dict[str, Any], competitors: list[dict[str, Any]]) -> dict[str, Any]:
    cfg["competitors"] = competitors
    console.print(f"\n[green]✓[/green] Saved {len(competitors)} competitor channel(s).\n")
    return cfg


# ─── Step 6: Aesthetic ─────────────────────────────────────────────────────

def _step_aesthetic(cfg: dict[str, Any]) -> dict[str, Any]:
    console.print(Panel(
        "[bold yellow]STEP 6 · Visual style[/bold yellow]\n\n"
        "Pick the aesthetic for your thumbnails. You can tweak later by re-running\n"
        "the wizard.",
        border_style="yellow",
    ))

    table = Table(show_header=False, box=None, padding=(0, 2))
    for i, p in enumerate(_AESTHETIC_PRESETS, 1):
        table.add_row(f"[cyan]{i}.[/cyan]", f"[bold]{p['name']}[/bold]", p["desc"])
    table.add_row(f"[cyan]{len(_AESTHETIC_PRESETS) + 1}.[/cyan]", "[bold]Custom[/bold]", "Define your own hex codes")
    console.print(table)

    default_idx = 1
    for i, p in enumerate(_AESTHETIC_PRESETS, 1):
        if p["id"] == cfg.get("aesthetic"):
            default_idx = i
            break

    choice = IntPrompt.ask("\nPick one", default=default_idx)
    if 1 <= choice <= len(_AESTHETIC_PRESETS):
        preset = _AESTHETIC_PRESETS[choice - 1]
        cfg["aesthetic"] = preset["id"]
        cfg["palette"] = preset["palette"]
    else:
        cfg["aesthetic"] = "custom"
        console.print("\n[bold]Custom palette:[/bold] paste hex codes (e.g. [cyan]#1C1B19[/cyan])")
        cfg["palette"] = {
            "bg_dark": Prompt.ask("  Dark background", default="#1C1B19"),
            "bg_light": Prompt.ask("  Light background", default="#F4EFE7"),
            "accent": Prompt.ask("  Accent color", default="#B8693A"),
            "text": Prompt.ask("  Text color", default="#F4EFE7"),
        }
    console.print()
    return cfg


# ─── Step 7: Face preference ───────────────────────────────────────────────

def _step_face(cfg: dict[str, Any]) -> dict[str, Any]:
    console.print(Panel(
        "[bold yellow]STEP 7 · Face in thumbnails?[/bold yellow]  [dim](optional)[/dim]\n\n"
        "If you say yes, you'll need a reference portrait photo so the AI can keep\n"
        "your face consistent across thumbnails.\n\n"
        "Say no to keep thumbnails icon-driven (works great, and is the default).",
        border_style="yellow",
    ))

    choice = Prompt.ask(
        "Include your face",
        choices=["yes", "no", "optional"],
        default=cfg.get("face_preference", "no"),
    )
    cfg["face_preference"] = choice
    if choice != "no":
        path = Prompt.ask(
            "Path to reference portrait (or press Enter to set later)",
            default=cfg.get("face_reference_path", ""),
        )
        if path:
            p = Path(path).expanduser()
            if p.exists():
                cfg["face_reference_path"] = str(p)
                console.print(f"[green]✓[/green] Saved.")
            else:
                console.print("[red]✗[/red] Path not found — you can add it later.")
    console.print()
    return cfg


# ─── Step 8: Forbidden looks ───────────────────────────────────────────────

def _step_forbidden(cfg: dict[str, Any]) -> dict[str, Any]:
    console.print(Panel(
        "[bold yellow]STEP 8 · Forbidden looks[/bold yellow]  [dim](optional)[/dim]\n\n"
        "What do you [bold]NOT[/bold] want?\n"
        "Examples: [cyan]no ring lights, no stock photos, no yellow arrows, no cringe reaction faces[/cyan]",
        border_style="yellow",
    ))

    existing = ", ".join(cfg.get("forbidden_looks", []))
    raw = Prompt.ask("Comma-separated list (or Enter to skip)", default=existing)
    cfg["forbidden_looks"] = [x.strip() for x in raw.split(",") if x.strip()]
    console.print()
    return cfg


# ─── Step 9: Copyright ─────────────────────────────────────────────────────

def _step_copyright(cfg: dict[str, Any]) -> dict[str, Any]:
    console.print(Panel(
        "[bold yellow]STEP 9 · Your name (for PNG metadata)[/bold yellow]\n\n"
        "This gets embedded in every thumbnail's EXIF so your files stay yours.",
        border_style="yellow",
    ))

    default = cfg.get("copyright_name") or cfg.get("youtube_handle", "").lstrip("@")
    cfg["copyright_name"] = Prompt.ask("Your name or channel", default=default or "Your Name")
    console.print()
    return cfg


# ─── Final summary ─────────────────────────────────────────────────────────

def _print_summary(cfg: dict[str, Any], yt_key: str) -> None:
    console.print(Panel(
        "[bold green]✓ All set![/bold green]\n\n"
        f"Config saved to: [cyan]{config.CONFIG_PATH}[/cyan]\n"
        f"API keys saved to: [cyan]{config.ENV_PATH}[/cyan]\n\n"
        "[bold]Ready to generate your first thumbnail:[/bold]\n"
        "  [cyan]tg thumb --title \"Your video title here\"[/cyan]\n\n"
        "Or with a transcript:\n"
        "  [cyan]tg thumb --title \"Title\" --transcript path/to/transcript.txt[/cyan]\n\n"
        "Helpful:\n"
        "  [cyan]tg hooks --title \"X\"[/cyan]  → just see scored hook ideas\n"
        "  [cyan]tg onboard[/cyan]                → re-run this wizard\n"
        "  [cyan]tg config --show[/cyan]          → view your current config",
        border_style="green",
    ))
    console.print(
        f"\n[dim]Follow Sebastian for more AI builds:[/dim]\n"
        f"  YouTube: [link]{brand.YOUTUBE_URL}[/link]\n"
        f"  Instagram: [link]{brand.INSTAGRAM_URL}[/link]\n"
        f"  LinkedIn: [link]{brand.LINKEDIN_URL}[/link]\n"
        f"  Skool community: [link]{brand.SKOOL_URL}[/link]\n"
    )
