from telegram import Update
from telegram.ext import ContextTypes
import logging
from config import SUPERGROUP_ID, THREADS
from utils.storage import is_onboarded, get_state

logger = logging.getLogger(__name__)

# ── Strike tracker ─────────────────────────────────────────────────
# Tracks how many times a user has tried to post in Networking
# Format: { user_id: strike_count }
networking_strikes = {}

MAX_STRIKES = 3

def get_networking_strikes_snapshot() -> dict[int, int]:
    return dict(networking_strikes)


async def guard_access(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Master guard — runs on every message in the supergroup.
    Handles two restrictions:
    1. Unregistered users blocked from all non-Welcome topics
    2. Networking topic is read-only for all members (admins only)
    3. Users who repeatedly post in Networking get ejected after 3 strikes
    """
    message = update.effective_message
    user = update.effective_user

    if not message or not user:
        return
    if update.effective_chat.id != SUPERGROUP_ID:
        return
    if user.is_bot:
        return

    thread_id = message.message_thread_id

    # ── Check if user is admin ─────────────────────────────────────
    member = await context.bot.get_chat_member(SUPERGROUP_ID, user.id)
    is_admin = member.status in ("administrator", "creator")

    # ── RULE 1: Networking topic is read-only ──────────────────────
    if thread_id == THREADS["networking"]:
        if not is_admin:

            # Delete the message immediately
            try:
                await message.delete()
            except Exception as e:
                logger.warning(
                    "Could not delete networking message user_id=%s message_id=%s: %s",
                    user.id,
                    message.message_id,
                    e,
                )

            # Add a strike
            networking_strikes[user.id] = networking_strikes.get(user.id, 0) + 1
            strikes = networking_strikes[user.id]
            remaining = MAX_STRIKES - strikes

            logger.warning(
                "Networking strike user_id=%s first_name=%s strikes=%s/%s remaining=%s",
                user.id,
                user.first_name,
                strikes,
                MAX_STRIKES,
                remaining,
            )

            # ── Strike 1: First warning ────────────────────────────
            if strikes == 1:
                try:
                    await context.bot.send_message(
                        chat_id=SUPERGROUP_ID,
                        message_thread_id=THREADS["welcome"],
                        text=(
                            f"👋 Hi {user.first_name}!\n\n"
                            "📌 The *Networking* topic is read-only.\n\n"
                            "Member profiles are posted there automatically "
                            "when new members join.\n\n"
                            "To connect with members, reach out via their "
                            "Telegram or Twitter/X handles shown in their profile.\n\n"
                            "You can converse with members on the *General* topic.\n\n"
                            f"⚠️ *Warning 1/{MAX_STRIKES}:* Further attempts "
                            "may result in removal from EXPLOR."
                        ),
                        parse_mode="Markdown"
                    )
                except Exception as e:
                    logger.warning("Could not send strike 1 warning user_id=%s: %s", user.id, e)

            # ── Strike 2: Final warning ────────────────────────────
            elif strikes == 2:
                try:
                    await context.bot.send_message(
                        chat_id=SUPERGROUP_ID,
                        message_thread_id=THREADS["welcome"],
                        text=(
                            f"🚨 {user.first_name}, this is your *final warning!*\n\n"
                            "The *Networking* topic is strictly read-only for members.\n\n"
                            f"⚠️ *Warning 2/{MAX_STRIKES}:* One more attempt and "
                            "you will be removed from EXPLOR."
                        ),
                        parse_mode="Markdown"
                    )
                except Exception as e:
                    logger.warning("Could not send strike 2 warning user_id=%s: %s", user.id, e)

            # ── Strike 3: Eject the user ───────────────────────────
            elif strikes >= MAX_STRIKES:
                try:
                    # Ban then immediately unban = kick (they can rejoin via invite)
                    await context.bot.ban_chat_member(
                        chat_id=SUPERGROUP_ID,
                        user_id=user.id
                    )
                    await context.bot.unban_chat_member(
                        chat_id=SUPERGROUP_ID,
                        user_id=user.id
                    )
                    logger.warning(
                        "User ejected from EXPLOR user_id=%s first_name=%s",
                        user.id,
                        user.first_name,
                    )
                except Exception as e:
                    logger.error("Could not eject user_id=%s: %s", user.id, e)

                # Reset their strike count
                networking_strikes.pop(user.id, None)

                # Announce the ejection in Welcome topic
                try:
                    await context.bot.send_message(
                        chat_id=SUPERGROUP_ID,
                        message_thread_id=THREADS["welcome"],
                        text=(
                            f"🚫 *{user.first_name}* has been removed from EXPLOR "
                            "for repeatedly violating the Networking topic rules.\n\n"
                            "EXPLOR is a premium community — we maintain high standards "
                            "for all members. 🌍"
                        ),
                        parse_mode="Markdown"
                    )
                except Exception as e:
                    logger.warning("Could not post ejection notice user_id=%s: %s", user.id, e)

        return  # Stop here for Networking topic

    # ── Allow everything in Welcome topic ──────────────────────────
    if thread_id == THREADS["welcome"]:
        return

    # ── Allow admins through all other topics ──────────────────────
    if is_admin:
        return

    # ── RULE 2: Block unregistered users from all other topics ─────
    if not is_onboarded(user.id):
        try:
            await message.delete()
            logger.info(
                "Deleted restricted message from unregistered user_id=%s thread_id=%s",
                user.id,
                thread_id,
            )
        except Exception as e:
            logger.warning(
                "Could not delete restricted message user_id=%s thread_id=%s: %s",
                user.id,
                thread_id,
                e,
            )
        try:
            state = get_state(user.id)
            if state in ("new", "pending", "filling_details"):
                await context.bot.send_message(
                    chat_id=SUPERGROUP_ID,
                    message_thread_id=THREADS["welcome"],
                    text=(
                        f"👋 Hi {user.first_name}!\n\n"
                        "⛔ Please complete your registration in the "
                        "*Welcome* topic first to unlock all areas "
                        "of EXPLOR. 🚀"
                    ),
                    parse_mode="Markdown"
                )
                logger.info(
                    "Sent onboarding reminder user_id=%s state=%s thread_id=%s",
                    user.id,
                    state,
                    thread_id,
                )
        except Exception as e:
            logger.warning(
                "Could not send onboarding reminder user_id=%s thread_id=%s: %s",
                user.id,
                thread_id,
                e,
            )


async def guard_networking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Kept for import compatibility — logic moved into guard_access."""
    pass
