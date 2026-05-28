from telegram import Update
from telegram.ext import ContextTypes
from config import SUPERGROUP_ID, THREADS

async def post_event(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Usage: /event <title> | <date> | <description>"""
    if not context.args:
        await update.message.reply_text(
            "Usage: /event <title> | <date> | <description>\n"
            "Example: /event EXPLOR Meetup | Dec 20, 2025 | Monthly networking session"
        )
        return

    text = " ".join(context.args)
    parts = [p.strip() for p in text.split("|")]

    if len(parts) < 3:
        await update.message.reply_text("Please provide: title | date | description")
        return

    title, date, desc = parts[0], parts[1], parts[2]
    await update.message.reply_text(
        f"📅 *NEW EVENT*\n\n"
        f"🏷️ *{title}*\n"
        f"📆 {date}\n"
        f"📝 {desc}\n\n"
        f"React with ✅ if you're attending!",
        parse_mode="Markdown"
    )

async def list_rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
       chat_id=SUPERGROUP_ID,
       message_thread_id=THREADS["events"],      # 👈 change key per handler
       text="your message here",
       parse_mode="Markdown"
)