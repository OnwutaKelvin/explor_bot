import logging
import platform
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from time import monotonic

from telegram import Update
from telegram.ext import ContextTypes

from config import ADMIN_IDS, LOG_DIR, SUPERGROUP_ID, THREADS
from utils.storage import get_state_counts

logger = logging.getLogger(__name__)

STARTED_AT = datetime.now(timezone.utc)
STARTED_MONOTONIC = monotonic()
RECENT_ERRORS: list[str] = []
MAX_RECENT_ERRORS = 5


def _format_user(update: Update) -> str:
    user = update.effective_user
    if not user:
        return "unknown_user"
    username = f"@{user.username}" if user.username else "no_username"
    return f"{user.id} {username}"


def _format_thread(update: Update) -> str:
    message = update.effective_message
    thread_id = message.message_thread_id if message else None
    for key, configured_thread_id in THREADS.items():
        if configured_thread_id == thread_id:
            return f"{key}:{thread_id}"
    return str(thread_id)


def _remember_error(message: str) -> None:
    RECENT_ERRORS.append(message)
    del RECENT_ERRORS[:-MAX_RECENT_ERRORS]


def get_uptime() -> str:
    seconds = int(monotonic() - STARTED_MONOTONIC)
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    if days:
        return f"{days}d {hours}h {minutes}m {seconds}s"
    if hours:
        return f"{hours}h {minutes}m {seconds}s"
    return f"{minutes}m {seconds}s"


async def log_update(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    if not message or not update.effective_chat:
        return

    if update.effective_chat.id != SUPERGROUP_ID:
        logger.info(
            "Ignored update outside configured group chat_id=%s user=%s",
            update.effective_chat.id,
            _format_user(update),
        )
        return

    if message.text and message.text.startswith("/"):
        command = message.text.split(maxsplit=1)[0]
        logger.info(
            "Command received command=%s user=%s thread=%s message_id=%s",
            command,
            _format_user(update),
            _format_thread(update),
            message.message_id,
        )
    else:
        logger.debug(
            "Message received type=%s user=%s thread=%s message_id=%s",
            _message_type(message),
            _format_user(update),
            _format_thread(update),
            message.message_id,
        )


def _message_type(message) -> str:
    if message.text:
        return "text"
    if message.photo:
        return "photo"
    if message.video:
        return "video"
    if message.document:
        return "document"
    if message.sticker:
        return "sticker"
    if message.voice:
        return "voice"
    if message.audio:
        return "audio"
    return "other"


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    error = context.error
    error_name = type(error).__name__ if error else "UnknownError"
    error_text = str(error) if error else "No error object available"
    _remember_error(f"{error_name}: {error_text}")

    logger.error(
        "Unhandled exception while processing update=%r",
        update,
        exc_info=(type(error), error, error.__traceback__) if error else None,
    )


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not user or user.id not in ADMIN_IDS:
        await update.message.reply_text("You are not authorized to view bot status.")
        logger.warning(
            "Unauthorized /status attempt user=%s thread=%s",
            _format_user(update),
            _format_thread(update),
        )
        return

    from handlers.guard import get_networking_strikes_snapshot

    state_counts = get_state_counts()
    strikes = get_networking_strikes_snapshot()
    bot_log = Path(LOG_DIR) / "bot.log"
    error_log = Path(LOG_DIR) / "errors.log"

    details = [
        "<b>EXPLOR Bot Status</b>",
        f"Uptime: {escape(get_uptime())}",
        f"Started UTC: {escape(STARTED_AT.isoformat(timespec='seconds'))}",
        f"Python: {escape(platform.python_version())}",
        "",
        "<b>Onboarding State</b>",
        f"Complete: {state_counts.get('complete', 0)}",
        f"Pending: {state_counts.get('pending', 0)}",
        f"Filling details: {state_counts.get('filling_details', 0)}",
        f"New/unknown: {state_counts.get('new', 0)}",
        "",
        "<b>Guard</b>",
        f"Networking strike users: {len(strikes)}",
        "",
        "<b>Logs</b>",
        f"Bot log: {escape(str(bot_log))}",
        f"Error log: {escape(str(error_log))}",
    ]

    if RECENT_ERRORS:
        details.extend(["", "<b>Recent Errors</b>"])
        details.extend(escape(item) for item in RECENT_ERRORS[-MAX_RECENT_ERRORS:])
    else:
        details.extend(["", "<b>Recent Errors</b>", "None recorded"])

    await update.message.reply_text("\n".join(details), parse_mode="HTML")
    logger.info("Status reported to admin user=%s", _format_user(update))
