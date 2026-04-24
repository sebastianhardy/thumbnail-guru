# Thumbnail Guru

> The thumb-stopper engine. Scored viral hooks + Nano Banana Pro scenes + brand-grade typography. One command. Beginner-friendly.

Built by **[Sebastian Hardy](https://www.youtube.com/@learnaibeforeitstolate)** · [@sebastianhardy_](https://www.instagram.com/sebastianhardy_/) · [Skool](https://skool.com/viral-ads)

---

## What it does

1. **Generates scored viral text hooks** for your video from a 20-pattern library (Forbidden Knowledge, Pattern Break, Identity Filter, Reverse Brag, Before/After, and 15 more). Each hook is scored on Specificity + Intrigue out of 20.
2. **Generates dark-moody base images** via Google's Nano Banana Pro (Gemini 3 Pro Image): 3D-rendered icons, competitor logos to trigger the designer-threat reflex.
3. **Renders baked-in text overlays** in brand-grade typography via Chrome headless: chunky split-color with outlines, 3D extruded block letters, or clean minimal sans.
4. **Outputs 3, 5, or 10 variants** at 1280×720, ready to A/B test on YouTube.

One command. About 30 seconds per thumbnail.

---

## Quickstart

Three steps. The third one does the rest.

```bash
git clone https://github.com/sebastianhardy/thumbnail-guru.git
cd thumbnail-guru
pip install -e .
```

Then run the tool with no arguments:

```bash
tg
```

If it's your first run, the wizard kicks in automatically. It walks you through:

- Getting a free Gemini API key (opens the browser for you)
- Optionally getting a YouTube API key (for competitor validation + reference thumbnail auto-fetch)
- Your channel, niche, audience, 5 competitors, visual style, and face preference

About 10 minutes end to end. Keys save to `~/.thumbnail-guru/.env` — never committed anywhere.

---

## Generate your first thumbnail

After onboarding:

```bash
# From a video title alone
tg thumb --title "I Built My Entire Brand With AI"

# From a transcript (richer hooks)
tg thumb --title "Your title" --transcript path/to/transcript.txt

# Pick how many variants (prompts if omitted)
tg thumb --title "Your title" --count 10
```

Output lands in `~/.thumbnail-guru/videos/<slug>/out/`.

---

## Important: what this tool actually runs on

**This tool does NOT use Claude.** The AI stack is:

| Layer | Tech | Why |
|-------|------|-----|
| Hook generation | Pure Python (deterministic) | Reliable, reproducible, no LLM tokens spent |
| Image generation | Google Nano Banana Pro (Gemini 3 Pro Image) | Best-in-class text rendering + photorealism |
| Text overlay | HTML/CSS + Chrome headless | Pixel-perfect typography, no font guessing |

**About pricing:** Nano Banana Pro is Google's paid image model. Google AI Studio gives you a free tier that covers light personal use (a handful of thumbnails per day is typically fine). Serious volume incurs charges — check [AI Studio pricing](https://aistudio.google.com) for current rates. You control the spend.

---

## The 20-pattern hook engine

Every hook is drawn from a proven viral pattern, scored on Specificity + Intrigue:

Forbidden Knowledge · Negative Superlative · Specific Number Reveal · Identity Filter · Before/After Identity Gap · Interrupted Action · Insider Confession · Pattern Break Declaration · Multi-Million Dollar Claim · Single-Question Interrupt · Tool Stack Reveal · POV Framing · One-Weird-Trick Revival · Time-Compressed Result · Controversial Call-Out · Curiosity Cliffhanger · Authority Shortcut · Reverse Brag · Public Artifact Reveal · Direct Challenge.

Pattern diversity is enforced: you never get 10 hooks of the same type. See [docs/extending.md](docs/extending.md) to add your own.

---

## Storage

All your data lives at `~/.thumbnail-guru/`:

```
~/.thumbnail-guru/
├── .env                         # API keys (never committed)
├── config.json                  # channel, aesthetic, competitors, preferences
├── references/                  # reference thumbnail images
└── videos/
    └── 2026-04-23-my-video/
        ├── context.json         # extracted facts + picked hooks
        ├── hooks.md             # scored hook table
        └── out/                 # generated thumbnails
```

Everything is local. The only outbound traffic is the Gemini API call to render base images, and (optionally) the YouTube API call to validate competitor URLs.

---

## Extending

`tg` is designed for more than thumbnails. The architecture supports future modules:

- `tg script` — long-form YouTube script generator (coming)
- `tg reels` — short-form content with scored hooks (coming)
- `tg package` — full upload pack: title, description, chapters, tags (coming)

See [docs/architecture.md](docs/architecture.md) for how to add your own command.

---

## Requirements

- Python 3.10+
- Google Chrome (for headless overlay rendering)
- Free Gemini API key from [aistudio.google.com](https://aistudio.google.com)
- Optional: YouTube Data API v3 key from [console.cloud.google.com](https://console.cloud.google.com)

macOS and Linux fully supported. Windows support is best-effort.

---

## License

[Personal Use License](LICENSE) — free for your own channel. Not for resale, rebranding, or paid services. © 2026 Sebastian Hardy.

For commercial licensing, reach out via [YouTube](https://www.youtube.com/@learnaibeforeitstolate) or [LinkedIn](https://www.linkedin.com/in/iamsebastianhardy/).

---

## Follow

More AI workflows like this — tutorials, build-in-public, and the full stack walk-throughs:

- **YouTube:** [@learnaibeforeitstolate](https://www.youtube.com/@learnaibeforeitstolate)
- **Instagram:** [@sebastianhardy_](https://www.instagram.com/sebastianhardy_/)
- **LinkedIn:** [iamsebastianhardy](https://www.linkedin.com/in/iamsebastianhardy/)
- **Skool community:** [skool.com/viral-ads](https://skool.com/viral-ads) — deep-dive tutorials on AI and ads

Thanks for using Thumbnail Guru.
