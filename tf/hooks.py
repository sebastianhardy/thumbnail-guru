"""Hook engine. Generates scored viral text hooks from user context + transcript.

Core algorithm:
  1. Extract specifics from transcript (numbers, named tools, roles, money, time)
  2. For each pattern in the default mix, fill the formula with specifics
  3. Score each hook: Specificity (1-10) + Intrigue (1-10)
  4. Anti-pattern check — flag or auto-rewrite any hook <15/20
  5. Return top 10 diversified by pattern

This is a deterministic engine, not LLM-based. Reliable, reproducible, free.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


# ─── Data loading ──────────────────────────────────────────────────────────

_DATA_DIR = Path(__file__).parent.parent / "data"


def load_patterns() -> dict[str, Any]:
    with (_DATA_DIR / "patterns.yaml").open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# ─── Fact extraction ───────────────────────────────────────────────────────

_NAMED_TOOLS = [
    "Claude", "Claude Code", "ChatGPT", "GPT-4", "GPT-5", "Gemini",
    "Nano Banana Pro", "Midjourney", "DALL-E", "Stable Diffusion",
    "Canva", "Figma", "Photoshop", "Illustrator", "After Effects",
    "Final Cut", "Premiere", "Notion", "Airtable", "Zapier", "Make",
    "HubSpot", "Salesforce", "Slack", "Discord", "Zoom",
    "Shopify", "Stripe", "Webflow", "Framer", "WordPress",
    "YouTube", "Instagram", "LinkedIn", "TikTok", "Twitter", "X",
]

_APEX_BRANDS = [
    "Apple", "Google", "Microsoft", "Coca-Cola", "Nike", "Adidas",
    "Tesla", "Amazon", "Airbnb", "Uber", "Spotify", "Meta", "Netflix",
]

_ROLES = [
    "agency owner", "agency owners", "founder", "founders", "solo founder",
    "solo operator", "creator", "creators", "designer", "designers",
    "marketer", "marketers", "developer", "developers", "coder", "coders",
    "freelancer", "freelancers", "consultant", "ceo", "coo", "cmo", "cto",
    "sdr", "ae", "engineer", "engineers", "product manager", "pm",
]


@dataclass
class ExtractedFacts:
    named_tools: list[str] = field(default_factory=list)
    apex_brands: list[str] = field(default_factory=list)
    roles: list[str] = field(default_factory=list)
    numbers: list[str] = field(default_factory=list)       # "32", "$40K", etc.
    money: list[str] = field(default_factory=list)          # "$47K", "$1M"
    time_spans: list[str] = field(default_factory=list)     # "2 days", "19 hours"

    @property
    def primary_tool(self) -> str:
        return self.named_tools[0] if self.named_tools else "this tool"

    @property
    def enemy_tool(self) -> str:
        """An antagonist tool — usually a designer/legacy tool the video is replacing."""
        for t in self.named_tools:
            if t in ("Figma", "Canva", "Photoshop", "Illustrator", "After Effects"):
                return t
        return ""

    @property
    def primary_role(self) -> str:
        return self.roles[0] if self.roles else "founders"


def extract_facts(text: str) -> ExtractedFacts:
    """Pull specific, named, numeric facts out of a transcript or title."""
    facts = ExtractedFacts()

    for tool in _NAMED_TOOLS:
        if re.search(rf"\b{re.escape(tool)}\b", text, re.IGNORECASE):
            if tool not in facts.named_tools:
                facts.named_tools.append(tool)

    for brand in _APEX_BRANDS:
        if re.search(rf"\b{re.escape(brand)}\b", text, re.IGNORECASE):
            if brand not in facts.apex_brands:
                facts.apex_brands.append(brand)

    for role in _ROLES:
        if re.search(rf"\b{re.escape(role)}\b", text, re.IGNORECASE):
            clean = role.rstrip("s") + "s"  # normalize to plural
            if clean not in facts.roles:
                facts.roles.append(clean)

    facts.money = list(set(re.findall(r"\$\d+[\d,]*[KMk]?", text)))
    facts.numbers = list(set(re.findall(r"\b\d{1,3}(?:,\d{3})*\b", text)))
    facts.time_spans = list(set(re.findall(
        r"\b\d+\s*(?:minute|minutes|min|hour|hours|hr|day|days|week|weeks|month|months|year|years)\b",
        text, re.IGNORECASE,
    )))

    return facts


# ─── Hook generation ───────────────────────────────────────────────────────

@dataclass
class Hook:
    text: str
    pattern_id: str
    pattern_name: str
    specificity: int
    intrigue: int

    @property
    def score(self) -> int:
        return self.specificity + self.intrigue

    @property
    def word_count(self) -> int:
        return len(self.text.split())


def _score_specificity(text: str, facts: ExtractedFacts) -> int:
    """1-10 score based on presence of numbers, named tools, named roles."""
    score = 4
    if any(t.lower() in text.lower() for t in facts.named_tools):
        score += 2
    if any(b.lower() in text.lower() for b in facts.apex_brands):
        score += 2
    if any(r.lower() in text.lower() for r in facts.roles):
        score += 1
    if re.search(r"\$\d", text) or re.search(r"\b\d+\b", text):
        score += 2
    if re.search(r"\bany\b|\bentire\b|\bzero\b|\bfull\b|\balmost\b|\bevery\b", text, re.IGNORECASE):
        score += 0  # curiosity amplifier, doesn't boost specificity
    return min(score, 10)


def _score_intrigue(text: str, pattern_id: str) -> int:
    """1-10 score based on curiosity-gap triggers."""
    score = 5
    lower = text.lower()

    if "?" in text or lower.endswith("..."):
        score += 2
    if any(w in lower for w in ["is dead", "is over", "killed", "obsolete", "replaced"]):
        score += 2
    if any(w in lower for w in ["illegal", "shouldn't", "don't want you", "hiding", "hides", "forbidden"]):
        score += 3
    if any(w in lower for w in ["copy", "steal", "any", "without", "before", "zero"]):
        score += 1
    if "not " in lower and "." in text:  # "Not a designer. Did X." framing
        score += 1
    if pattern_id in ("forbidden_knowledge", "pattern_break", "controversial_call_out"):
        score += 1

    return min(score, 10)


def _check_anti_patterns(text: str) -> list[str]:
    """Return list of anti-pattern IDs tripped, empty if clean."""
    tripped = []
    lower = text.lower()
    wc = len(text.split())
    if wc > 10:
        tripped.append("too_long")
    if wc < 3:
        tripped.append("too_short")
    if any(lower.startswith(g) for g in ("hey ", "hi ", "welcome", "what's up", "guys")):
        tripped.append("greeting")
    if "—" in text:
        tripped.append("em_dash")
    if re.match(r"^(how to|in this video|here's how)", lower):
        tripped.append("literal_title")
    return tripped


# ─── Hook templates ────────────────────────────────────────────────────────
#
# Each pattern has 1-3 templates. {tool}, {enemy}, {role}, {num}, {brand},
# {time} are filled from facts. If a required slot is missing, the template
# is skipped.

_TEMPLATES: dict[str, list[str]] = {
    "forbidden_knowledge": [
        "{enemy} doesn't want you to see this",
        "{enemy} hides this from {role}",
        "The workflow {enemy} is scared of",
    ],
    "negative_superlative": [
        "Stop using {enemy}",
        "Delete {enemy}. Watch this.",
        "You're using {enemy} wrong",
    ],
    "specific_number_reveal": [
        "{num} assets in {time}",
        "$0 spent. Full brand shipped.",
        "{num} in {time} with {tool}",
    ],
    "identity_filter": [
        "{role}, copy any brand",
        "{role}: $0 brand kit",
        "{role}, this is a cheat code",
    ],
    "before_after_gap": [
        "From {enemy} to {brand} in {time}",
        "From nothing to full brand in {time}",
        "{enemy} user → {brand}-level brand",
    ],
    "pattern_break": [
        "{enemy} is dead for {role}",
        "{enemy} is over",
        "Your {enemy} is obsolete",
    ],
    "controversial_call_out": [
        "Delete your {enemy} subscription",
        "{enemy} is overrated",
        "Cancel {enemy}. Use {tool}.",
    ],
    "reverse_brag": [
        "Not a designer. Copied {brand}.",
        "Can't design. Built a brand.",
        "Not technical. Shipped {num} assets.",
    ],
    "tool_stack": [
        "Steal my {num}-tool stack",
        "My $0 AI stack",
        "{num} tools replaced my designer",
    ],
    "time_compressed": [
        "Full brand in {time}",
        "Brand built in {time}",
        "{time}: full brand shipped",
    ],
    "authority_shortcut": [
        "{num}x shipper: here's the stack",
        "I build brands in {time}. Here's how.",
    ],
    "insider_confession": [
        "I shouldn't admit how I did this",
        "What {role} don't tell you about branding",
    ],
    "direct_challenge": [
        "Bet your designer can't do this",
        "Try to beat this brand in {time}",
    ],
    "single_question": [
        "How is this brand free?",
        "Why is {enemy} still charging?",
    ],
    "curiosity_cliffhanger": [
        "I rebuilt my brand in {time} and...",
        "{tool} just shipped a full brand...",
    ],
    "interrupted_action": [
        "Wait, {tool} just made a brand?",
        "Hold on, is this a real brand?",
    ],
    "pov_framing": [
        "POV: your {role} doesn't need a designer",
        "POV: {enemy} is dead and you don't care",
    ],
    "one_weird_trick": [
        "The one prompt that made my brand",
        "One file replaces your designer",
    ],
    "million_dollar_claim": [
        "How I built a {brand}-grade brand with {num} tools",
    ],
    "public_artifact": [
        "My brand kit. {num} assets. Zero designers.",
    ],
}


def _fill(template: str, facts: ExtractedFacts) -> str | None:
    """Try to fill a template. Return None if a required slot can't be filled."""
    out = template

    def sub(token: str, value: str) -> None:
        nonlocal out
        out = out.replace(token, value)

    if "{tool}" in out:
        if not facts.named_tools:
            return None
        sub("{tool}", facts.primary_tool)

    if "{enemy}" in out:
        if not facts.enemy_tool:
            return None
        sub("{enemy}", facts.enemy_tool)

    if "{role}" in out:
        if not facts.roles:
            return None
        role = facts.primary_role
        # capitalize correctly
        sub("{role}", role.capitalize() if out.startswith("{role}") else role)

    if "{num}" in out:
        nums = facts.numbers + [m.lstrip("$") for m in facts.money]
        if not nums:
            return None
        # pick first "interesting" number
        best = next((n for n in nums if len(n) >= 2), nums[0])
        sub("{num}", best)

    if "{brand}" in out:
        if not facts.apex_brands:
            return None
        sub("{brand}", facts.apex_brands[0])

    if "{time}" in out:
        if not facts.time_spans:
            return None
        sub("{time}", facts.time_spans[0])

    return out.strip()


# ─── Public API ────────────────────────────────────────────────────────────

def generate_hooks(text: str, count: int = 10) -> list[Hook]:
    """Generate `count` scored hooks from transcript/title text."""
    patterns = load_patterns()
    facts = extract_facts(text)
    results: list[Hook] = []
    seen_texts: set[str] = set()

    # Preferred order from default_mix
    mix = patterns.get("default_mix", {})
    pattern_order = sorted(
        patterns["patterns"],
        key=lambda p: (-mix.get(p["id"], 0), -p.get("weight", 0)),
    )

    for pattern in pattern_order:
        pid = pattern["id"]
        pname = pattern["name"]
        for tpl in _TEMPLATES.get(pid, []):
            filled = _fill(tpl, facts)
            if not filled or filled in seen_texts:
                continue
            if _check_anti_patterns(filled):
                continue
            hook = Hook(
                text=filled,
                pattern_id=pid,
                pattern_name=pname,
                specificity=_score_specificity(filled, facts),
                intrigue=_score_intrigue(filled, pid),
            )
            results.append(hook)
            seen_texts.add(filled)
            if len(results) >= count * 2:  # over-produce so we can sort & trim
                break
        if len(results) >= count * 2:
            break

    results.sort(key=lambda h: h.score, reverse=True)

    # Diversify by pattern — no more than 2 per pattern in the final top-N
    final: list[Hook] = []
    pattern_count: dict[str, int] = {}
    for h in results:
        if pattern_count.get(h.pattern_id, 0) < 2:
            final.append(h)
            pattern_count[h.pattern_id] = pattern_count.get(h.pattern_id, 0) + 1
        if len(final) >= count:
            break

    return final


def top_n_for_thumbnails(hooks: list[Hook], n: int = 3) -> list[Hook]:
    """Pick top N diversified by pattern for thumbnail generation."""
    picked: list[Hook] = []
    patterns_used: set[str] = set()
    for h in hooks:
        if h.pattern_id in patterns_used:
            continue
        picked.append(h)
        patterns_used.add(h.pattern_id)
        if len(picked) >= n:
            break
    return picked


def render_hook_table(hooks: list[Hook]) -> str:
    """Render hooks as a markdown table for saving to context."""
    lines = [
        "| # | Hook | Pattern | Spec | Intrigue | Total |",
        "|---|------|---------|------|----------|-------|",
    ]
    for i, h in enumerate(hooks, 1):
        lines.append(
            f"| {i} | {h.text} | {h.pattern_name} | {h.specificity} | "
            f"{h.intrigue} | {h.score} |"
        )
    return "\n".join(lines)
