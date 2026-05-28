from config import SUPERGROUP_ID, THREADS, RESTRICTED_THREADS
from utils.storage import is_onboarded

def get_thread_key(chat_id: int, thread_id: int | None) -> str | None:
    if chat_id != SUPERGROUP_ID:
        return None
    for key, tid in THREADS.items():
        if tid == thread_id:
            return key
    return None

def is_explor_group(chat_id: int) -> bool:
    return chat_id == SUPERGROUP_ID

async def guard_access(update, context) -> bool:
    """
    Returns True and blocks the message if user hasn't onboarded.
    Use at the top of any handler to restrict access.
    """
    user_id = update.effective_user.id
    thread_id = update.message.message_thread_id if update.message else None

    if not is_onboarded(user_id) and thread_id in RESTRICTED_THREADS:
        await context.bot.send_message(
            chat_id=SUPERGROUP_ID,
            message_thread_id=THREADS["welcome"],
            text=(
                f"⛔ Hi {update.effective_user.first_name}, "
                "please complete your registration in the "
                "👋 Welcome topic before accessing other areas."
            )
        )
        # Delete their message in the restricted topic
        try:
            await update.message.delete()
        except Exception:
            pass
        return True
    return False