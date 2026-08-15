import re
import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import SUPERGROUP_ID, THREADS
from utils.storage import set_state, get_state, clear_temp_details

logger = logging.getLogger(__name__)

# ── Field parsing ───────────────────────────────────────────────────
FIELD_PATTERNS = {
    "name":      r"name\s*:\s*(.+)",
    "twitter":   r"twitter(?:\s*/\s*x)?\s*:\s*(.+)",
    "telegram":  r"telegram\s*:\s*(.+)",
    "interests": r"interests?\s*:\s*(.+)",
}

FORM_TEMPLATE = (
    "Name: John Doe\n"
    "Twitter: @johndoe\n"
    "Telegram: @johndoe\n"
    "Interests: Technology, Finance & Investing"
)


def parse_details(text: str) -> dict:
    """Parse a single free-text message into the four fields.
    Returns a dict with any fields found; missing fields are omitted."""
    fields = {}
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        for key, pattern in FIELD_PATTERNS.items():
            match = re.match(pattern, line, re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                if value:
                    fields[key] = value
    return fields


# ── Helper: Track message IDs ──────────────────────────────────────
def track_message(context: ContextTypes.DEFAULT_TYPE, message_id: int):
    if "onboarding_messages" not in context.user_data:
        context.user_data["onboarding_messages"] = []
    context.user_data["onboarding_messages"].append(message_id)


# ── Helper: Delete all tracked messages ───────────────────────────
async def wipe_welcome_messages(context: ContextTypes.DEFAULT_TYPE, extra_ids: list):
    all_ids = context.user_data.get("onboarding_messages", []) + extra_ids
    for msg_id in all_ids:
        try:
            await context.bot.delete_message(
                chat_id=SUPERGROUP_ID,
                message_id=msg_id
            )
        except Exception as e:
            logger.warning("Could not delete onboarding message message_id=%s: %s", msg_id, e)


# ── Step 1: New member joins → silently restrict + mark pending ───
async def greet_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != SUPERGROUP_ID:
        return

    for member in update.message.new_chat_members:
        if member.is_bot:
            continue

        user_id = member.id
        set_state(user_id, "filling_details")
        logger.info("New member pending onboarding user_id=%s first_name=%s", user_id, member.first_name)

        await context.bot.restrict_chat_member(
            chat_id=SUPERGROUP_ID,
            user_id=user_id,
            permissions={
                "can_send_messages": True,
                "can_send_media_messages": False,
                "can_send_polls": False,
                "can_send_other_messages": False,
                "can_add_web_page_previews": False,
                "can_change_info": False,
                "can_invite_users": False,
                "can_pin_messages": False,
            }
        )

        # No welcome message, no button — user goes straight to typing details.
        # Their own join event message is tracked so it gets wiped too.
        track_message(context, update.message.message_id)


# ── Step 2: Catch details message → parse → submit directly ───────
async def collect_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # Only act on users who are still mid-onboarding — ignore everyone else's
    # normal chatter in the Welcome topic.
    if get_state(user_id) != "filling_details":
        return

    track_message(context, update.message.message_id)

    parsed = parse_details(update.message.text or "")
    required = ["name", "twitter", "telegram", "interests"]
    missing = [f for f in required if f not in parsed or not parsed[f]]

    if missing:
        sent = await context.bot.send_message(
            chat_id=SUPERGROUP_ID,
            message_thread_id=THREADS["welcome"],
            text=(
                "⚠️ I couldn't find: *" + ", ".join(missing) + "*.\n\n"
                "Please resend all four details in this exact format:\n\n"
                f"`{FORM_TEMPLATE}`"
            ),
            parse_mode="Markdown"
        )
        track_message(context, sent.message_id)
        logger.warning(
            "Onboarding details incomplete user_id=%s missing=%s",
            user_id, missing
        )
        return

    name      = parsed["name"]
    twitter   = parsed["twitter"]
    telegram  = parsed["telegram"]
    interests = parsed["interests"]

    logger.info("Onboarding details parsed user_id=%s", user_id)

    # 1. Post profile to Networking topic
    try:
        await context.bot.send_message(
            chat_id=SUPERGROUP_ID,
            message_thread_id=THREADS["networking"],
            text=(
                "🤝 *New Member Profile*\n\n"
                f"*Name:* {name}\n"
                f"*Twitter/X:* {twitter}\n"
                f"*Telegram:* {telegram}\n"
                f"*Interests:* {interests}\n\n"
            ),
            parse_mode="Markdown"
        )
        logger.info("Profile posted to Networking topic user_id=%s", user_id)
    except Exception as e:
        logger.error("Networking profile post failed user_id=%s: %s", user_id, e)

    # 2. Announce in General topic
    try:
        await context.bot.send_message(
            chat_id=SUPERGROUP_ID,
            message_thread_id=THREADS["general"],
            text=(
                f"*{name}* has just joined EXPLOR!\n\n"
                f"*Interests:* {interests}\n"
                f"*Twitter/X:* {twitter}\n"
                f"*Telegram:* {telegram}\n\n"
                "Welcome them to the community! "
            ),
            parse_mode="Markdown"
        )
        logger.info("Entry announced in General topic user_id=%s", user_id)
    except Exception as e:
        logger.error("General announcement failed user_id=%s: %s", user_id, e)

    # 3. Grant full access
    try:
        await context.bot.restrict_chat_member(
            chat_id=SUPERGROUP_ID,
            user_id=user_id,
            permissions={
                "can_send_messages": True,
                "can_send_media_messages": True,
                "can_send_polls": True,
                "can_send_other_messages": True,
                "can_add_web_page_previews": True,
                "can_change_info": False,
                "can_invite_users": True,
                "can_pin_messages": False,
            }
        )
        logger.info("Full access granted user_id=%s", user_id)
    except Exception as e:
        logger.error("Access grant failed user_id=%s: %s", user_id, e)

    # 4. Mark complete
    set_state(user_id, "complete")
    clear_temp_details(user_id)

    # Wipe all tracked onboarding messages (join event, warnings, details message)
    await wipe_welcome_messages(context, [])
    logger.info("Welcome topic onboarding messages wiped user_id=%s", user_id)

    # 5. Clear data AFTER wipe
    context.user_data.clear()
