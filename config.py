from __future__ import annotations

import os
from dotenv import load_dotenv

load_dotenv()

def _csv_ints(value: str | None) -> list[int]:
    if not value:
        return []
    return [int(item.strip()) for item in value.split(",") if item.strip()]

BOT_TOKEN = os.getenv("BOT_TOKEN")
SUPERGROUP_ID = int(os.getenv("SUPERGROUP_ID"))
ADMIN_IDS = _csv_ints(os.getenv("ADMIN_IDS")) or [1105956780]
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_DIR = os.getenv("LOG_DIR", "logs")
TELEGRAM_CONNECT_TIMEOUT = float(os.getenv("TELEGRAM_CONNECT_TIMEOUT", "30"))
TELEGRAM_READ_TIMEOUT = float(os.getenv("TELEGRAM_READ_TIMEOUT", "60"))
TELEGRAM_WRITE_TIMEOUT = float(os.getenv("TELEGRAM_WRITE_TIMEOUT", "60"))
TELEGRAM_POOL_TIMEOUT = float(os.getenv("TELEGRAM_POOL_TIMEOUT", "30"))

THREADS = {
    "welcome":       int(os.getenv("WELCOME_THREAD_ID")),
    "events":        int(os.getenv("EVENTS_THREAD_ID")),
    "social_media":  int(os.getenv("SOCIAL_MEDIA_THREAD_ID")),
    "business":      int(os.getenv("BUSINESS_THREAD_ID")),
    "opportunities": int(os.getenv("OPPORTUNITIES_THREAD_ID")),
    "networking":    int(os.getenv("NETWORKING_THREAD_ID")),
    "announcement":  int(os.getenv("ANNOUNCEMENT_THREAD_ID")),
    "general":       int(os.getenv("GENERAL_THREAD_ID")),
}

GROUP_NAMES = {
    "welcome":       "👋 Welcome",
    "events":        "📅 Events & Spaces",
    "social_media":  "📱 Social Media Growth",
    "business":      "💼 Business & Finance",
    "opportunities": "🚀 Opportunities",
    "networking":    "🤝 Networking",
    "announcement":  "📢 Announcement",
    "general":       "💬 General",
}

# Topics restricted until onboarding is complete
RESTRICTED_THREADS = [
    int(os.getenv("EVENTS_THREAD_ID")),
    int(os.getenv("SOCIAL_MEDIA_THREAD_ID")),
    int(os.getenv("BUSINESS_THREAD_ID")),
    int(os.getenv("OPPORTUNITIES_THREAD_ID")),
    int(os.getenv("NETWORKING_THREAD_ID")),
    int(os.getenv("ANNOUNCEMENT_THREAD_ID")),
    int(os.getenv("GENERAL_THREAD_ID")),
]
