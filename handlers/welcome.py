import re
import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes, ConversationHandler,
    CallbackQueryHandler, MessageHandler, filters
)
from config import SUPERGROUP_ID, THREADS
from utils.storage import set_state, clear_temp_details

logger = logging.getLogger(__name__)

# Conversation states — now just one, since details are entered in a single message
ASK_DETAILS = 0

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


# ── Step 1: New member joins → single "get started" prompt ────────
async def greet_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != SUPERGROUP_ID:
        return

    for member in update.message.new_chat_members:
        if member.is_bot:
            continue

        user_id = member.id
        set_state(user_id, "pending")
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

        try:
            with open("assets/welcome.jpg", "rb") as photo:
                sent_photo = await context.bot.send_photo(
                    chat_id=SUPERGROUP_ID,
                    message_thread_id=THREADS["welcome"],
                    photo=photo,
                )
            track_message(context, sent_photo.message_id)
        except Exception as e:
            logger.warning("Could not send welcome image user_id=%s: %s", user_id, e)

        keyboard = [[InlineKeyboardButton(
            "Get Started ➡️",
            callback_data=f"show_form_{user_id}"
        )]]

        sent = await context.bot.send_message(
            chat_id=SUPERGROUP_ID,
            message_thread_id=THREADS["welcome"],
            text=f"👋 *Welcome, {member.first_name}!* Tap below to get started.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        track_message(context, sent.message_id)


# ── Step 2: Show single-message form ───────────────────────────────
async def show_form(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    if str(user_id) not in query.data:
        await query.answer("⛔ This button is not for you.", show_alert=True)
        logger.warning("Rejected form callback for wrong user user_id=%s data=%s", user_id, query.data)
        return

    track_message(context, query.message.message_id)

    set_state(user_id, "filling_details")
    logger.info("Onboarding form started user_id=%s", user_id)

    context.user_data["name"] = ""
    context.user_data["twitter"] = ""
    context.user_data["telegram"] = ""
    context.user_data["interests"] = ""

    sent = await context.bot.send_message(
        chat_id=SUPERGROUP_ID,
        message_thread_id=THREADS["welcome"],
        text=(
            "📝 *Member Details Form*\n\n"
            "Reply with *one message* containing all four details below, "
            "each on its own line, in this exact format:\n\n"
            f"`{FORM_TEMPLATE}`\n\n"
            "Your details will be shared in the Networking topic so "
            "members can connect with you.\n\n"
            "_Type_ `none` _for Twitter or Telegram if you don't have one._"
        ),
        parse_mode="Markdown"
    )
    track_message(context, sent.message_id)

    return ASK_DETAILS


# ── Step 3: Parse the single details message → Show Confirmation ──
async def collect_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
            update.effective_user.id, missing
        )
        return ASK_DETAILS

    context.user_data["name"] = parsed["name"]
    context.user_data["twitter"] = parsed["twitter"]
    context.user_data["telegram"] = parsed["telegram"]
    context.user_data["interests"] = parsed["interests"]

    logger.info("Onboarding details parsed user_id=%s", update.effective_user.id)

    user_id = update.effective_user.id

    keyboard = [
        [InlineKeyboardButton(
            "✅ Submit", callback_data=f"confirm_submit_{user_id}"
        )],
        [InlineKeyboardButton(
            "✏️ Start Over", callback_data=f"show_form_{user_id}"
        )]
    ]

    sent = await context.bot.send_message(
        chat_id=SUPERGROUP_ID,
        message_thread_id=THREADS["welcome"],
        text=(
            "――――――――――――――――――\n"
            "📋 *Please confirm your details:*\n\n"
            f"*Name:* {context.user_data['name']}\n"
            f"*Twitter/X:* {context.user_data['twitter']}\n"
            f"*Telegram:* {context.user_data['telegram']}\n"
            f"*Interests:* {context.user_data['interests']}\n\n"
            "――――――――――――――――――\n"
            "Click *Submit* to complete your registration\n"
            "or *Start Over* to correct your details 👇"
        ),
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    track_message(context, sent.message_id)

    return ConversationHandler.END


# ── Step 4: Final Submit ───────────────────────────────────────────
async def confirm_submit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id

    if str(user_id) not in query.data:
        await query.answer("⛔ This button is not for you.", show_alert=True)
        return

    name      = context.user_data.get("name", "N/A")
    twitter   = context.user_data.get("twitter", "N/A")
    telegram  = context.user_data.get("telegram", "N/A")
    interests = context.user_data.get("interests", "N/A")

    logger.info("Onboarding final submit user_id=%s", user_id)

    if name == "N/A" or name == "":
        await context.bot.send_message(
            chat_id=SUPERGROUP_ID,
            message_thread_id=THREADS["welcome"],
            text=(
                "⚠️ Your details seem incomplete.\n"
                "Please click *Start Over* and fill in the form again."
            ),
            parse_mode="Markdown"
        )
        logger.warning("Onboarding submit rejected for incomplete details user_id=%s", user_id)
        return

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

    # Wipe BEFORE clearing user_data so message IDs are still available
    await wipe_welcome_messages(context, [query.message.message_id])
    logger.info("Welcome topic onboarding messages wiped user_id=%s", user_id)

    # 5. Clear data AFTER wipe
    context.user_data.clear()
