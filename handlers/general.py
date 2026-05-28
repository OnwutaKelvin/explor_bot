from telegram import Update
from telegram.ext import ContextTypes
from config import GROUP_NAMES
from config import SUPERGROUP_ID, THREADS

async def explor_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    groups_list = "\n".join([f"  {v}" for v in GROUP_NAMES.values()])
    await update.message.reply_text(
        f"🌍 *About EXPLOR*\n\n"
        f"EXPLOR is a thriving community built for growth, connection, and opportunity.\n\n"
        f"*Our 8 Groups:*\n{groups_list}\n\n"
        f"Use /help to see all available commands.",
        parse_mode="Markdown"
    )

async def help_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
       chat_id=SUPERGROUP_ID,
       message_thread_id=THREADS["events"],      # 👈 change key per handler
       text="your message here",
       parse_mode="Markdown"
)