from telegram import Update
from telegram.ext import ContextTypes
from config import SUPERGROUP_ID, THREADS

ADMIN_IDS = [1105956780]  # 🔒 Replace with your Telegram user ID

async def announce(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("⛔ You are not authorized to make announcements.")
        return

    if not context.args:
        await update.message.reply_text("Usage: /announce <your message>")
        return

    message = " ".join(context.args)
    announcement = (
        f"📢 *EXPLOR ANNOUNCEMENT*\n\n"
        f"{message}\n\n"
        f"— The EXPLOR Team"
    )

    success = 0
    for topic, thread_id in THREADS.items():
        try:
            await context.bot.send_message(
                chat_id=SUPERGROUP_ID,
                message_thread_id=thread_id,  # 👈 sends to each topic
                text=announcement,
                parse_mode="Markdown"
            )
            success += 1
        except Exception as e:
            print(f"Failed to send to {topic}: {e}")

    await update.message.reply_text(
        f"✅ Announcement sent to {success}/{len(THREADS)} topics."
    )