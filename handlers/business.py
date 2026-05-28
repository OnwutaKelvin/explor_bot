from telegram import Update
from telegram.ext import ContextTypes
from config import SUPERGROUP_ID, THREADS

async def finance_tip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tips = [
        "💡 Track every naira/dollar. Profit is not the same as cash flow.",
        "💡 Pay yourself a salary even in your own business.",
        "💡 Separate personal and business finances from day one.",
        "💡 Build a 3-month emergency fund before scaling.",
        "💡 Revenue is vanity, profit is sanity, cash flow is reality.",
    ]
    import random
    await update.message.reply_text(
        f"💼 *Business & Finance Tip*\n\n{random.choice(tips)}",
        parse_mode="Markdown"
    )

async def pitch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Usage: /pitch <business name> | <what you do> | <looking for>"""
    if not context.args:
        await update.message.reply_text(
            "Usage: /pitch <business name> | <what you do> | <looking for>"
        )
        return

    text = " ".join(context.args)
    parts = [p.strip() for p in text.split("|")]
    if len(parts) < 3:
        await update.message.reply_text("Please provide all 3 parts separated by |")
        return

    biz, desc, need = parts
    await context.bot.send_message(
       chat_id=SUPERGROUP_ID,
       message_thread_id=THREADS["events"],      # 👈 change key per handler
       text="your message here",
       parse_mode="Markdown"
)