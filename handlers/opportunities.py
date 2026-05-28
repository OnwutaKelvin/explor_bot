from telegram import Update
from telegram.ext import ContextTypes
from config import SUPERGROUP_ID, THREADS

async def post_opportunity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Usage: /opportunity <title> | <type> | <details> | <how to apply>"""
    if not context.args:
        await update.message.reply_text(
            "Usage: /opportunity <title> | <type> | <details> | <how to apply>\n"
            "Types: Job | Internship | Freelance | Grant | Collaboration"
        )
        return

    text = " ".join(context.args)
    parts = [p.strip() for p in text.split("|")]
    if len(parts) < 4:
        await update.message.reply_text("Please provide all 4 parts separated by |")
        return

    title, opp_type, details, apply = parts
    await context.bot.send_message(
        chat_id=SUPERGROUP_ID,
        message_thread_id=THREADS["events"],      # 👈 change key per handler
        text="your message here",
        parse_mode="Markdown"
)