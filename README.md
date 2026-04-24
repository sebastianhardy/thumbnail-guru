# Thumbnail Forge

> The thumb-stopper engine. Scored hooks + dark-moody AI scenes + brand-grade typography. Built on Claude Code principles, powered by Google's Nano Banana Pro.

Built by **[Sebastian Hardy](https://www.youtube.com/@learnaibeforeitstolate)** · [@sebastianhardy_](https://instagram.com/sebastianhardy_)

---

## What it does

You paste a transcript, a title, and a screenshot of 10 thumbnails you love. Thumbnail Forge does the rest:

1. **Extracts facts** from the transcript: named tools, specific numbers, named roles, emotional levers.
2. **Generates 10 viral text hooks** using a 20-pattern library (Forbidden Knowledge, Pattern Break, Identity Filter, Reverse Brag, Before/After, and 15 more). Each hook is scored on Specificity + Intrigue out of 20.
3. **Picks the top 3** diversified by pattern.
4. **Generates base images** via Nano Banana Pro (Google's image model, free tier): dark moody scenes, branded 3D icons, recognizable competitor logos to trigger the designer-threat reflex.
5. **Renders text overlays** in your brand typography via Chrome headless: chunky split-color with thick outlines, 3D extruded block letters, or clean minimal sans.
6. **Outputs 9 scored variants** at 1280×720, ready to A/B upload.

One command. Ninety seconds. Nine thumbnails with different scored hooks.

---

## Who it's for

- Solo creators on YouTube who ship weekly and can't afford a designer.
- Operators and agency owners who want Apple-grade thumbnails without Figma.
- Anyone who has looked at their last 10 video thumbnails and thought "these don't look like a channel."

**Not for:** channels that need hand-crafted illustrations or pixel-perfect print-quality assets.

---

## Install

Requires Python 3.10+, Chrome, and a free Gemini API key from [aistudio.google.com](https://aistudio.google.com).

```bash
git clone https://github.com/sebastianhardy/thumbnail-forge.git
cd thumbnail-forge
pip install -e .
```

That installs the `tf` command globally.

---

## Quickstart

```bash
# 1. Run the onboarding wizard (first-run only, ~10 min)
tf onboard

# 2. Generate thumbnails for a video
tf thumb --transcript path/to/video.txt --title "My Video Title"

# 3. Outputs land in ~/.thumbnail-forge/videos/<slug>/out/
open ~/.thumbnail-forge/videos/my-video-title/out/
```

---

## The onboarding flow

`tf onboard` asks you (in order):

| Step | Question | Why it matters |
|------|----------|----------------|
| 1 | Gemini API key | Powers the image generation. Free tier is enough for ~100 thumbs/month. |
| 2 | YouTube channel URL | Used for attribution metadata on your PNGs. |
| 3 | Niche (one sentence) | Guides the hook patterns (e.g. AI-for-founders vs. cooking vlogs use different patterns). |
| 4 | Audience (one line) | Identity filters need to know who you're calling out. |
| 5 | Face in thumbnails? | y/n/optional. If yes, path to reference portrait. |
| 6 | 10 reference thumbnails | URLs or local files. Defines your visual aesthetic. Store them once, reuse forever. |
| 7 | 3-5 competitors | Channels whose aesthetic you want to match/beat. Used for the "competitor shattered" composition. |
| 8 | Aesthetic preset | Warm Premium · High Contrast Tech · Playful Retro · Clean Minimal · Custom |
| 9 | Forbidden looks | What you explicitly don't want (e.g. "no ring lights, no stock photos, no yellow arrows"). |
| 10 | Copyright name | Embedded in PNG metadata so your files stay yours. |

Answers are saved to `~/.thumbnail-forge/config.json`. You can re-run `tf onboard` any time to update.

---

## The three text-overlay styles

| Style | Example hook | When to use |
|-------|--------------|-------------|
| **A — Split-color chunky outline** | `CANVA TO / COCA-COLA` (orange + white, Paytone One, thick bone outline) | Tutorial, build-in-public, list videos |
| **B — 3D extruded block letters** | `DELETE FIGMA` (Bowlby One, cascading drop shadow) | Reaction, bold take, hot take |
| **C — Clean minimal sans** | `Figma is dead for founders.` (Inter 800, subtle shadow) | Death-of-X, controversial call-out, "it's over" energy |

`tf thumb` auto-picks the best style for each of your top 3 hooks based on the hook's pattern.

---

## The 20-pattern hook engine

Every hook Thumbnail Forge generates is drawn from one of 20 proven patterns:

1. Forbidden Knowledge · 2. Negative Superlative · 3. Specific Number Reveal · 4. Identity Filter · 5. Before/After Identity Gap · 6. Interrupted Action · 7. Insider Confession · 8. Pattern Break Declaration · 9. Multi-Million Dollar Claim · 10. Single-Question Interrupt · 11. Tool Stack Reveal · 12. POV Framing · 13. One-Weird-Trick Revival · 14. Time-Compressed Result · 15. Controversial Call-Out · 16. Curiosity Cliffhanger · 17. Authority Shortcut · 18. Reverse Brag · 19. Public Artifact Reveal · 20. Direct Challenge.

See [docs/extending.md](docs/extending.md) to add your own.

---

## Storage layout

All your data lives at `~/.thumbnail-forge/`:

```
~/.thumbnail-forge/
├── config.json                 # API key, channel, aesthetic, preferences
├── references/                 # Your 10 reference thumbnails (permanent)
├── competitors.json            # Competitor channels
└── videos/
    └── 2026-04-23-my-video/
        ├── context.json        # title, transcript path, facts extracted
        ├── hooks.md            # 10 scored hooks + pick rationale
        └── out/                # 9 generated thumbnails
```

Everything is local. Nothing is uploaded anywhere except the Gemini API call to generate the images.

---

## Extending the toolkit

The `tf` CLI is designed for more than thumbnails. The architecture supports future modules:

- `tf script` — YouTube long-form script generator (coming)
- `tf reels` — Short-form content (Reels/TikTok/Shorts) with scored hooks (coming)
- `tf package` — Full upload pack (title, description, chapters, tags) (coming)
- `tf repurpose` — Long-form → multi-platform cross-post pack (coming)

See [docs/architecture.md](docs/architecture.md) for how to add your own command.

---

## License

[Personal Use License](LICENSE) — free to use for your own channel. Not for resale, rebranding, or paid services. Copyright © 2026 Sebastian Hardy.

For commercial licensing, contact Sebastian via [YouTube](https://www.youtube.com/@learnaibeforeitstolate).

---

## Follow

If this saves you 40 hours a year, return the favor:

- **YouTube:** [@learnaibeforeitstolate](https://www.youtube.com/@learnaibeforeitstolate) · AI workflows for founders who actually ship
- **Instagram:** [@sebastianhardy_](https://instagram.com/sebastianhardy_) · build-in-public, daily
- **LinkedIn:** [Sebastian Hardy](https://linkedin.com/in/iamsebastianhardy) · operator-grade AI takes

Thanks for using Thumbnail Forge.
