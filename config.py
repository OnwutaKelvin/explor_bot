import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
SUPERGROUP_ID = int(os.getenv("SUPERGROUP_ID"))

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