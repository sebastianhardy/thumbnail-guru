# Extending Thumbnail Forge

Three ways to extend without touching the core engine.

## 1. Add a hook pattern

Edit `data/patterns.yaml`. Add a block like:

```yaml
  - id: my_pattern
    name: "My Pattern Name"
    formula: "[how to use this pattern]"
    trigger: "[cognitive trigger]"
    when: "[when to use]"
    weight: 8
    examples:
      - "Example hook 1"
      - "Example hook 2"
```

Then add templates in `tf/hooks.py` under `_TEMPLATES`:

```python
"my_pattern": [
    "{tool} just killed {enemy}",
    "Your {role} doesn't need {enemy} anymore",
],
```

Placeholders available: `{tool}`, `{enemy}`, `{role}`, `{num}`, `{brand}`, `{time}`.
Templates that can't fill their required slots are skipped automatically.

## 2. Add a composition template

Edit `data/compositions.yaml`. Add a block:

```yaml
  - id: my_composition
    name: "My Scene"
    best_for: "When to use this scene"
    pairs_with_hooks: [forbidden_knowledge, pattern_break]
    text_area: "top_center"
    prompt: |
      YouTube thumbnail, 1280x720.
      [your scene description here]
      Placeholders: {background}, {user_icon_desc}, {competitor_icons}
      TOP HALF is empty dark ambient background — reserved for text overlay.
```

The `pairs_with_hooks` list determines which hook patterns auto-select this composition.

## 3. Add a text overlay style

Edit `data/overlay_styles.yaml`:

```yaml
  - id: my_style
    name: "My Style Name"
    best_for: "When to use it"
    pairs_with_patterns: [pattern_ids_here]
    layout: "single_line_top"
    css: |
      .stack {
        position: absolute; top: 40px; left: 0; right: 0;
        text-align: center;
        font-family: 'Your Font', sans-serif;
      }
      /* ... */
```

Add any Google Fonts you reference to the `fonts_url` line at the bottom of the same file.

## 4. Add a new top-level command (e.g. `tf script`)

Recipe:

1. Create `tf/script.py` — your engine (mirror `tf/hooks.py` or `tf/generator.py`).
2. Create `data/script_templates.yaml` — your data.
3. In `tf/cli.py`, add:

```python
@main.command()
@click.option("--transcript", "-T", type=click.Path(exists=True))
def script(transcript):
    """Generate a long-form YouTube script."""
    _require_onboarded()
    cfg = config.load()
    # call your engine, save to ~/.thumbnail-forge/videos/<slug>/script.md
```

4. Update README with the new command.

Each command lives in its own engine module. No cross-dependencies.

## 5. Use a different image model

Edit `tf/generator.py` → `generate_base_image()`. Replace the Gemini call with your model of choice (Stable Diffusion via Replicate, Midjourney via API, OpenAI DALL-E, etc.).

The rest of the pipeline (overlay, output) is model-agnostic.

## 6. Add a Claude Code skill wrapper

If you use Claude Code, you can wrap Thumbnail Forge as a skill:

```
~/.claude/skills/thumb-forge/SKILL.md
```

Contents:

```markdown
---
name: thumb-forge
description: "Generate scored-hook YouTube thumbnails via Thumbnail Forge CLI."
allowed-tools: [Bash, Read]
---

When the user asks for thumbnails, run:
  `tf thumb --title "[title]" --transcript [path-to-transcript]`

Then show the user the generated files and the hooks.md table.
```

This is optional. Thumbnail Forge works standalone without Claude Code.
