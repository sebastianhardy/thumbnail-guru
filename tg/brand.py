"""Attribution strings. These appear in CLI output, README, and PNG metadata.

The personal-use license requires that these attribution lines remain visible.
"""

AUTHOR = "Sebastian Hardy"
YOUTUBE_URL = "https://www.youtube.com/@learnaibeforeitstolate"
YOUTUBE_HANDLE = "@learnaibeforeitstolate"
INSTAGRAM_HANDLE = "@sebastianhardy_"
INSTAGRAM_URL = "https://www.instagram.com/sebastianhardy_/"
LINKEDIN_URL = "https://www.linkedin.com/in/iamsebastianhardy/"
LINKEDIN_HANDLE = "iamsebastianhardy"
SKOOL_URL = "https://skool.com/viral-ads"
SKOOL_NAME = "Viral Ads"

TAGLINE = "AI workflows for founders who actually ship."

# Feedback webhook. Sebastian sets this to a Discord webhook URL or
# equivalent before distributing. Set via:
#   export THUMBNAIL_GURU_WEBHOOK="https://discord.com/api/webhooks/..."
# Or hard-code below. Leave empty to disable outbound telemetry entirely.
FEEDBACK_WEBHOOK_URL = ""

FOOTER_SHORT = (
    f"Built by {AUTHOR} · {YOUTUBE_HANDLE} on YouTube · {INSTAGRAM_HANDLE} on Instagram"
)

FOOTER_LONG = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Thumbnail Guru v{__import__("tg").__version__} · Built by {AUTHOR}

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
║   T H U M B N A I L   G U R U                        ║
║                                                      ║
║   The thumb-stopper engine.                          ║
║   Built by {AUTHOR:<42}║
║                                                      ║
╚══════════════════════════════════════════════════════╝
"""
