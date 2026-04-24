# Architecture

Thumbnail Guru is a CLI tool (`tf`) built on a four-layer architecture designed to scale beyond thumbnails.

```
┌───────────────────────────────────────────────────────┐
│  CLI layer (Click)                                    │
│    tg onboard · tg thumb · tg hooks · tg config       │
│    └─ future: tg script · tg reels · tg repurpose     │
└──────────────────┬────────────────────────────────────┘
                   │
┌──────────────────▼────────────────────────────────────┐
│  Engine layer                                         │
│    hooks.py        facts + 20-pattern scoring         │
│    generator.py    Gemini image gen + Chrome overlay  │
│    onboard.py      first-run wizard                   │
└──────────────────┬────────────────────────────────────┘
                   │
┌──────────────────▼────────────────────────────────────┐
│  Data layer (YAML, data-first)                        │
│    patterns.yaml         20 hook patterns             │
│    compositions.yaml     scene templates              │
│    overlay_styles.yaml   typography + CSS styles      │
└──────────────────┬────────────────────────────────────┘
                   │
┌──────────────────▼────────────────────────────────────┐
│  User data layer (~/.thumbnail-guru/)                │
│    config.json           API key, preferences         │
│    references/           user's inspirational thumbs  │
│    videos/<slug>/out/    generated thumbnails         │
└───────────────────────────────────────────────────────┘
```

## Why this structure

**Data-first.** Patterns, compositions, and overlay styles live in YAML so they can be edited without touching Python. A non-engineer can add a new hook pattern or overlay style in 5 minutes.

**Engine is stateless.** `hooks.py` and `generator.py` take input, return output. All state lives in the user-data layer or is passed in via config. Makes testing trivial.

**CLI is thin.** Commands in `cli.py` only orchestrate: read config, pass to engine, render output. Adding `tg script` later means adding one command, one engine module, and one YAML data file.

**User data is local-first.** Everything lives at `~/.thumbnail-guru/`. Nothing is uploaded to a server Thumbnail Guru controls. The only outbound call is the Gemini API request to generate base images.

## Extending with new commands

Say you want to add `tg script` (long-form YouTube script generator). Here's the recipe:

1. Create `tg/script.py` — the engine module. Pattern it after `tg/hooks.py`.
2. Create `data/script_templates.yaml` — the data (outline templates, section templates, etc.).
3. Add `@main.command()` for `tg script` in `cli.py`.
4. Re-use `config.load()` for user preferences.
5. Save output to `~/.thumbnail-guru/videos/<slug>/script.md`.

Each new command slots in without touching existing ones.

## The image generation flow

```
hook (picked)  ────────┐
                       │
                       ▼
              ┌────────────────┐
              │ composition?   │  → matches hook.pattern_id
              │ (YAML lookup)  │     to composition template
              └───────┬────────┘
                      │
                      ▼
              ┌────────────────┐
              │ base image     │  → Gemini API (Nano Banana Pro)
              │ (cached by     │     prompt = composition +
              │  composition)  │     user palette + competitors
              └───────┬────────┘
                      │
                      ▼
              ┌────────────────┐
              │ overlay style? │  → matches hook.pattern_id
              │ (YAML lookup)  │     to typography style
              └───────┬────────┘
                      │
                      ▼
              ┌────────────────┐
              │ HTML render    │  → Chrome headless screenshot
              │ + crop to 720  │     1280x820 → crop to 1280x720
              └───────┬────────┘
                      │
                      ▼
             ~/.thumbnail-guru/videos/<slug>/out/<file>.png
```

Base images are cached per composition so three hooks using the same composition only trigger one Gemini call.

## The hook scoring model

Fully deterministic. No LLM for scoring.

- **Specificity (1-10):** +2 per named tool, +2 per apex brand, +1 per named role, +2 per number. Base 4.
- **Intrigue (1-10):** +2 for question mark or ellipsis, +2 for death/kill verbs, +3 for forbidden framing, +1 for action verbs (copy/steal/any/zero), +1 for negation pattern, +1 for reactance-heavy patterns.
- **Total (2-20):** sum.

Hooks scoring below 15/20 are filtered. Templates that can't fill their required slots (e.g. need `{brand}` but none in transcript) are skipped. Pattern diversity is enforced: no more than 2 hooks per pattern in the final output.

## What's NOT here (by design)

- No LLM hook generator. Templates are deterministic — the "intelligence" is in the 20-pattern library curated from research, not in an LLM call. Reliable, reproducible, free.
- No cloud storage. No accounts. No telemetry.
- No UI. CLI only. Future shipped as commands, not dashboards.
