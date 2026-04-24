"""Attribution strings. These appear in CLI output, README, and PNG metadata.

The personal-use license requires that these attribution lines remain visible.
"""

AUTHOR = "Sebastian Hardy"
YOUTUBE_URL = "https://www.youtube.com/@learnaibeforeitstolate"
YOUTUBE_HANDLE = "@learnaibeforeitstolate"
INSTAGRAM_HANDLE = "@sebastianhardy_"
INSTAGRAM_URL = "https://instagram.com/sebastianhardy_"
LINKEDIN_URL = "https://linkedin.com/in/iamsebastianhardy"

TAGLINE = "AI workflows for founders who actually ship."

FOOTER_SHORT = (
    f"Built by {AUTHOR} · {YOUTUBE_HANDLE} on YouTube · {INSTAGRAM_HANDLE} on Instagram"
)

FOOTER_LONG = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Thumbnail Forge v{__import__("tf").__version__} · Built by {AUTHOR}

  {TAGLINE}

Follow for more:
  YouTube:   {YOUTUBE_URL}
  Instagram: {INSTAGRAM_URL}
  LinkedIn:  {LINKEDIN_URL}

Personal-use license. Not for resale. © 2026 {AUTHOR}.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""


def welcome_banner() -> str:
    return f"""
╔══════════════════════════════════════════════════════╗
║                                                      ║
║   T H U M B N A I L   F O R G E                      ║
║                                                      ║
║   The thumb-stopper engine.                          ║
║   Built by {AUTHOR:<42}║
║                                                      ║
╚══════════════════════════════════════════════════════╝
"""
