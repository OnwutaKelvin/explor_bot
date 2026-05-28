from telegram import Update
from telegram.ext import ContextTypes
from config import SUPERGROUP_ID, THREADS

async def introduce(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Usage: /introduce <name> | <what you do> | <looking to connect with>"""
    if not context.args:
        await update.message.reply_text(
            "Usage: /introduce <name> | <what you do> | <looking to connect with>"
        )
        return

    text = " ".join(context.args)
    parts = [p.strip() for p in text.split("|")]
    if len(parts) < 3:
        await update.message.reply_text("Please provide all 3 parts separated by |")
        return

    name, role, connect = parts
    await context.bot.send_message(
       chat_id=SUPERGROUP_ID,
       message_thread_id=THREADS["events"],      # 👈 change key per handler
       text="your message here",
       parse_mode="Markdown"
)
    
    