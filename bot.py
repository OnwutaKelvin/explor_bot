from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    filters, ConversationHandler, CallbackQueryHandler
)
import logging
from telegram import Update
from config import (
    BOT_TOKEN,
    SUPERGROUP_ID,
    THREADS,
    TELEGRAM_CONNECT_TIMEOUT,
    TELEGRAM_POOL_TIMEOUT,
    TELEGRAM_READ_TIMEOUT,
    TELEGRAM_WRITE_TIMEOUT,
)
from handlers.welcome import (
    greet_new_member, show_form,
    collect_details, confirm_submit,
    ASK_DETAILS
)
from handlers.guard import guard_access, guard_networking
from handlers.events import post_event, list_rules
from handlers.social_media import growth_tip, share_profile
from handlers.business import finance_tip, pitch
from handlers.opportunities import post_opportunity
from handlers.networking import introduce
from handlers.announcements import announce
from handlers.general import explor_info, help_menu
from utils.logging_config import setup_logging
from utils.monitoring import error_handler, log_update, status_command

logger = logging.getLogger(__name__)


# ── Custom thread filter ───────────────────────────────────────────
class ThreadFilter(filters.MessageFilter):
    def __init__(self, thread_id: int):
        self.thread_id = thread_id
        super().__init__()

    def filter(self, message):
        return message.message_thread_id == self.thread_id

def in_thread(thread_key: str):
    thread_id = THREADS[thread_key]
    return filters.Chat(SUPERGROUP_ID) & ThreadFilter(thread_id)


def main():
    setup_logging()
    logger.info("Starting EXPLOR bot")
    app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .connect_timeout(TELEGRAM_CONNECT_TIMEOUT)
        .read_timeout(TELEGRAM_READ_TIMEOUT)
        .write_timeout(TELEGRAM_WRITE_TIMEOUT)
        .pool_timeout(TELEGRAM_POOL_TIMEOUT)
        .get_updates_connect_timeout(TELEGRAM_CONNECT_TIMEOUT)
        .get_updates_read_timeout(TELEGRAM_READ_TIMEOUT)
        .get_updates_write_timeout(TELEGRAM_WRITE_TIMEOUT)
        .get_updates_pool_timeout(TELEGRAM_POOL_TIMEOUT)
        .build()
    )
    app.add_error_handler(error_handler)

    # Audit incoming updates before moderation or command handlers run.
    app.add_handler(MessageHandler(filters.ALL, log_update), group=-1)

    # ── 🔒 Access Guard — MUST be first ───────────────────────────────
    app.add_handler(MessageHandler(
        filters.Chat(SUPERGROUP_ID) & filters.TEXT,
        guard_access
    ), group=0)

    app.add_handler(MessageHandler(
        filters.Chat(SUPERGROUP_ID) & (
           filters.PHOTO | filters.VIDEO | filters.Document.ALL |
           filters.Sticker.ALL | filters.VOICE | filters.AUDIO
        ),
        guard_access
    ), group=0)
    

    # ── Onboarding Conversation ────────────────────────────────────
    onboarding_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(show_form, pattern=r"^show_form_\d+$")
        ],
        states={
            ASK_DETAILS: [MessageHandler(filters.TEXT & ~filters.COMMAND, collect_details)],
        },
        fallbacks=[],
        per_chat=False,
        per_user=True,
    )

    # ── Welcome & Onboarding ───────────────────────────────────────
    app.add_handler(MessageHandler(
        filters.StatusUpdate.NEW_CHAT_MEMBERS, greet_new_member
    ), group=1)
    # ✅ New
    app.add_handler(CallbackQueryHandler(
        confirm_submit, pattern=r"^confirm_submit_\d+$"
    ), group=1)
    app.add_handler(onboarding_conv, group=1)

    # ── General (all topics) ───────────────────────────────────────
    app.add_handler(CommandHandler("help", help_menu), group=1)
    app.add_handler(CommandHandler("explor", explor_info), group=1)
    app.add_handler(CommandHandler("status", status_command), group=1)

    # ── Events topic ───────────────────────────────────────────────
    app.add_handler(CommandHandler("event", post_event,
        filters=in_thread("events")), group=1)

    # ── Social Media topic ─────────────────────────────────────────
    app.add_handler(CommandHandler("tip", growth_tip,
        filters=in_thread("social_media")), group=1)
    app.add_handler(CommandHandler("profile", share_profile,
        filters=in_thread("social_media")), group=1)

    # ── Business topic ─────────────────────────────────────────────
    app.add_handler(CommandHandler("financetip", finance_tip,
        filters=in_thread("business")), group=1)
    app.add_handler(CommandHandler("pitch", pitch,
        filters=in_thread("business")), group=1)

    # ── Opportunities topic ────────────────────────────────────────
    app.add_handler(CommandHandler("opportunity", post_opportunity,
        filters=in_thread("opportunities")), group=1)

    # ── Networking topic ───────────────────────────────────────────
    app.add_handler(CommandHandler("introduce", introduce,
        filters=in_thread("networking")), group=1)

    # ── Announcement topic ─────────────────────────────────────────
    app.add_handler(CommandHandler("announce", announce,
        filters=in_thread("announcement")), group=1)
    
    
    logger.info("EXPLOR bot is running across all topics")
    app.run_polling()


if __name__ == "__main__":
    main()
