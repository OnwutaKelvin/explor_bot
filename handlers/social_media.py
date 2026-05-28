from telegram import Update
from telegram.ext import ContextTypes
from config import SUPERGROUP_ID, THREADS

TIPS = [
    "📌 Post consistently — at least 3x per week to stay relevant.",
    "📌 Use trending hashtags relevant to your niche.",
    "📌 Engage with your audience — reply to every comment early on.",
    "📌 Short-form video (Reels, TikTok, Shorts) has the highest organic reach.",
    "📌 Collaborate with others in your niche for cross-promotion.",
    "📌 Your bio should clearly state who you help and how.",
    "📌 Analytics don't lie — review them weekly and adjust your content.",
]

_tip_index = 0

async def growth_tip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global _tip_index
    tip = TIPS[_tip_index % len(TIPS)]
    _tip_index += 1
    await update.message.reply_text(
        f"💡 *Social Media Growth Tip*\n\n{tip}",
        parse_mode="Markdown"
    )

async def share_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Usage: /profile @handle | platform | niche"""
    if not context.args:
        await update.message.reply_text("Usage: /profile @handle | platform | niche")
        return

    text = " ".join(context.args)
    parts = [p.strip() for p in text.split("|")]
    if len(parts) < 3:
        await update.message.reply_text("Please provide: @handle | platform | niche")
        return

    handle, platform, niche = parts
    await context.bot.send_message(
        chat_id=SUPERGROUP_ID,
        message_thread_id=THREADS["events"],      # 👈 change key per handler
        text="your message here",
        parse_mode="Markdown"
)