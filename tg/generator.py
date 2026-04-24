"""Thumbnail generator. Gemini / Nano Banana Pro base image → HTML/CSS overlay → PNG."""
from __future__ import annotations

import base64
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Any

import yaml
from PIL import Image

from . import config as cfg


# ─── Chrome detection ──────────────────────────────────────────────────────

_CHROME_CANDIDATES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium-browser",
    "/usr/bin/chromium",
    "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
    "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
]


def find_chrome() -> str | None:
    for p in _CHROME_CANDIDATES:
        if Path(p).exists():
            return p
    found = shutil.which("google-chrome") or shutil.which("chromium") or shutil.which("chrome")
    return found


# ─── Data loading ──────────────────────────────────────────────────────────

_DATA_DIR = Path(__file__).parent.parent / "data"


def load_compositions() -> dict[str, Any]:
    with (_DATA_DIR / "compositions.yaml").open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_overlay_styles() -> dict[str, Any]:
    with (_DATA_DIR / "overlay_styles.yaml").open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# ─── Gemini image generation ──────────────────────────────────────────────

_MODEL = "gemini-3-pro-image-preview"


def _build_icon_description(user_cfg: dict[str, Any]) -> str:
    """Generic primary-tool icon based on user's palette."""
    accent = user_cfg.get("palette", {}).get("accent", "#B8693A")
    return (
        f"a 3D-rendered glossy rounded square app icon, in the color {accent}, "
        f"with a white abstract sunburst/asterisk symbol in the center, soft "
        f"warm bottom glow, studio product render"
    )


def _build_competitor_icons(user_cfg: dict[str, Any], limit: int = 3) -> str:
    """Describe competitor icons. Falls back to generic if none provided."""
    competitors = user_cfg.get("competitors", [])[:limit]
    if not competitors:
        return (
            "three glossy rounded square app icons: one white with a black Apple "
            "logo, one white with the coral Airbnb symbol, one white with the "
            "black Uber wordmark, each roughly 200px tall, studio product render"
        )
    parts = []
    for c in competitors:
        name = c if isinstance(c, str) else c.get("name", "")
        parts.append(
            f"a 3D-rendered glossy rounded square app icon for {name}, studio "
            f"product render"
        )
    return ", next to ".join(parts)


def generate_base_image(
    composition: dict[str, Any],
    user_cfg: dict[str, Any],
    api_key: str,
) -> Image.Image:
    """Call Nano Banana Pro with the composition prompt, return PIL Image."""
    from google import genai
    from google.genai import types

    compositions = load_compositions()
    backgrounds = compositions.get("backgrounds", {})
    bg_key = _aesthetic_to_bg(user_cfg.get("aesthetic", "warm_premium"))
    background = backgrounds.get(bg_key, backgrounds.get("dark_studio", {})).get("prompt", "")

    icon = _build_icon_description(user_cfg)
    competitors = _build_competitor_icons(user_cfg)

    prompt = (
        composition["prompt"]
        .replace("{background}", background.strip())
        .replace("{user_icon_desc}", icon)
        .replace("{competitor_icons}", competitors)
        .replace("{competitor_icons_1}", competitors.split(",")[0] if "," in competitors else competitors)
        .replace("{competitor_icons_2}", competitors.split(",")[-1] if "," in competitors else competitors)
        .replace("{aspirational_icons}", competitors)
    )

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=_MODEL,
        contents=[prompt.strip()],
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE", "TEXT"],
        ),
    )
    for part in response.candidates[0].content.parts:
        if part.inline_data is not None:
            return Image.open(BytesIO(part.inline_data.data))
    raise RuntimeError("Gemini returned no image")


def _aesthetic_to_bg(aesthetic: str) -> str:
    return {
        "warm_premium": "dark_studio",
        "high_contrast": "high_contrast",
        "playful_retro": "seamless_cyc",
        "clean_minimal": "clean_minimal",
        "destruction": "destruction",
    }.get(aesthetic, "dark_studio")


# ─── Text overlay ─────────────────────────────────────────────────────────

@dataclass
class OverlayJob:
    base_image: Image.Image
    hook_text: str
    style_id: str
    split_point: str | None = None  # for split-color styles: split after this word


def _split_hook(text: str) -> tuple[str, str]:
    """Split a hook into (first_colored_line, second_white_line).

    Heuristic: split near the middle, preferring natural word boundaries and
    preserving meaningful halves.
    """
    words = text.split()
    if len(words) <= 1:
        return "", text
    if len(words) == 2:
        return words[0], words[1]
    mid = len(words) // 2
    return " ".join(words[:mid]), " ".join(words[mid:])


def _html_for(image_b64: str, style: dict[str, Any], hook_text: str) -> str:
    style_id = style["id"]
    fonts_url = load_overlay_styles().get("fonts_url", "")

    if style_id == "split_color_outline":
        line1, line2 = _split_hook(hook_text.upper())
        text_html = f"""
          <div class="stack">
            <div class="line highlight">{line1}</div>
            <div class="line white">{line2}</div>
          </div>
        """
    elif style_id == "extruded_3d":
        text_html = f"""
          <div class="stack">
            <div class="line3d">{hook_text.upper()}</div>
          </div>
        """
    else:  # clean_minimal_sans
        text_html = f"""
          <div class="stack">
            <div class="clean">{hook_text}</div>
          </div>
        """

    return f"""<!DOCTYPE html>
<html><head>
<meta charset="UTF-8">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="{fonts_url}" rel="stylesheet">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  html, body {{ width: 1280px; height: 720px; overflow: hidden; }}
  .frame {{ position: relative; width: 1280px; height: 720px; }}
  .bg {{ width: 1280px; height: 720px; display: block; object-fit: cover; }}
  {style["css"]}
</style>
</head><body>
<div class="frame">
  <img class="bg" src="data:image/png;base64,{image_b64}">
  {text_html}
</div>
</body></html>"""


def render_overlay(
    base_image: Image.Image,
    hook_text: str,
    style: dict[str, Any],
    out_path: Path,
) -> Path:
    """Composite text overlay on the base image, return output path."""
    chrome = find_chrome()
    if not chrome:
        raise RuntimeError(
            "Chrome/Chromium not found. Install Google Chrome: "
            "https://www.google.com/chrome/"
        )

    # Encode base image as base64
    buf = BytesIO()
    base_image.save(buf, format="PNG")
    image_b64 = base64.b64encode(buf.getvalue()).decode()

    html = _html_for(image_b64, style, hook_text)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
        f.write(html)
        html_path = f.name

    try:
        raw_png = out_path.with_suffix(".raw.png")
        subprocess.run(
            [
                chrome,
                "--headless=new",
                "--disable-gpu",
                "--hide-scrollbars",
                "--no-sandbox",
                "--window-size=1280,820",
                "--virtual-time-budget=5000",
                "--force-device-scale-factor=1",
                f"--screenshot={raw_png}",
                f"file://{html_path}",
            ],
            check=True,
            capture_output=True,
            timeout=45,
        )
        img = Image.open(raw_png)
        if img.size != (1280, 720):
            img = img.crop((0, 0, 1280, 720))
        img.save(out_path)
        raw_png.unlink(missing_ok=True)
        return out_path
    finally:
        Path(html_path).unlink(missing_ok=True)


# ─── Orchestrator ─────────────────────────────────────────────────────────

def pick_composition_for_hook(pattern_id: str) -> dict[str, Any]:
    """Given a hook pattern, pick the best-matching composition template."""
    compositions = load_compositions()
    for comp in compositions["compositions"]:
        if pattern_id in comp.get("pairs_with_hooks", []):
            return comp
    return compositions["compositions"][0]  # fallback to first


def pick_style_for_pattern(pattern_id: str) -> dict[str, Any]:
    """Given a hook pattern, pick the best overlay style."""
    styles = load_overlay_styles()["styles"]
    for style in styles:
        if pattern_id in style.get("pairs_with_patterns", []):
            return style
    return styles[0]  # fallback


def generate_thumbnail_set(
    hooks: list[Any],
    user_cfg: dict[str, Any],
    video_dir: Path,
) -> list[dict[str, Any]]:
    """For each hook, generate a base image (cached by composition) and apply overlay.

    Returns a list of result dicts with path, hook, score, style, composition.
    """
    results = []
    out_dir = video_dir / "out"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Cache base images by composition id so we don't regen the same scene
    base_cache: dict[str, Image.Image] = {}

    for i, hook in enumerate(hooks, 1):
        comp = pick_composition_for_hook(hook.pattern_id)
        style = pick_style_for_pattern(hook.pattern_id)

        if comp["id"] not in base_cache:
            print(f"  [{i}/{len(hooks)}] Generating base image for composition '{comp['id']}'...")
            base_cache[comp["id"]] = generate_base_image(
                comp, user_cfg, cfg.gemini_api_key()
            )

        base = base_cache[comp["id"]]
        slug = _slug(hook.text)
        out_path = out_dir / f"{i:02d}-{comp['id']}-{style['id']}-{slug}.png"

        print(f"  [{i}/{len(hooks)}] Rendering overlay: '{hook.text}'")
        render_overlay(base, hook.text, style, out_path)

        results.append({
            "path": str(out_path),
            "filename": out_path.name,
            "hook": hook.text,
            "pattern": hook.pattern_name,
            "spec": hook.specificity,
            "intrigue": hook.intrigue,
            "score": hook.score,
            "composition": comp["name"],
            "style": style["name"],
        })

    return results


def _slug(text: str) -> str:
    import re
    s = text.lower()
    s = re.sub(r"[^a-z0-9\s-]", "", s)
    s = re.sub(r"\s+", "-", s).strip("-")
    return s[:40] or "hook"
