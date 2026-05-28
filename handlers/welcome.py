from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes, ConversationHandler,
    CallbackQueryHandler, MessageHandler, filters
)
from config import SUPERGROUP_ID, THREADS
from utils.storage import set_state, clear_temp_details

# Conversation states
ASK_NAME, ASK_TWITTER, ASK_TELEGRAM, ASK_INTERESTS = range(4)


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
            print(f"⚠️ Could not delete message {msg_id}: {e}")


# ── Step 1: New member joins ───────────────────────────────────────
async def greet_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != SUPERGROUP_ID:
        return

    for member in update.message.new_chat_members:
        if member.is_bot:
            continue

        user_id = member.id
        set_state(user_id, "pending")

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

        # ✅ Step A: Send the welcome image first
        try:
            with open("assets/welcome.jpg", "rb") as photo:
                sent_photo = await context.bot.send_photo(
                    chat_id=SUPERGROUP_ID,
                    message_thread_id=THREADS["welcome"],
                    photo=photo,
                )
            # ✅ Track the photo message so it gets wiped after onboarding
            track_message(context, sent_photo.message_id)
        except Exception as e:
            print(f"⚠️ Could not send welcome image: {e}")

        # ✅ Step B: Send the welcome text + Continue button
        sent = await context.bot.send_message(
            chat_id=SUPERGROUP_ID,
            message_thread_id=THREADS["welcome"],
            text=(
                f"👋 *Welcome to EXPLOR, {member.first_name}!*\n\n"
                "EXPLOR is a premium growth-focused community connecting "
                "ambitious individuals through opportunities, "
                "networking, business, creativity & innovation. 🚀\n\n"
                "Click *Continue* to get started 👇"
            ),
            parse_mode="Markdown",
        )

        # ✅ Step C: Embed message ID in button so show_rules can track it
        keyboard = [[InlineKeyboardButton(
            "Continue ➡️",
            callback_data=f"show_rules_{user_id}_{sent.message_id}"
        )]]

        await context.bot.edit_message_reply_markup(
            chat_id=SUPERGROUP_ID,
            message_id=sent.message_id,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


# ── Step 2: Show Rules ─────────────────────────────────────────────
async def show_rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id

    # ✅ FIX 3: Extract welcome_msg_id from callback_data
    # Format: show_rules_{user_id}_{welcome_msg_id}
    parts = query.data.split("_")
    welcome_msg_id = int(parts[-1])

    if str(user_id) not in query.data:
        await query.answer("⛔ This button is not for you.", show_alert=True)
        return

    # 4: Track the welcome message and the button click message
    track_message(context, welcome_msg_id)
    track_message(context, query.message.message_id)

    keyboard = [[InlineKeyboardButton(
        "Continue ➡️", callback_data=f"show_form_{user_id}"
    )]]

    # 5: Track the rules message
    sent = await context.bot.send_message(
        chat_id=SUPERGROUP_ID,
        message_thread_id=THREADS["welcome"],
        text=(
            "📋 *EXPLOR Community Rules*\n\n"
            "Please read carefully before proceeding.\n\n"
            "📜 EXPLOR Community Rules:\n\n"
            "1. Respect Everyone.\n"
            "Treat all members with respect.\n"
            "No hate, harassment, bullying or toxic behavior.\n\n"
            "2. No Spam.\n"
            "No spam, scams, fake opportunities or excessive promotions.\n\n"
            "3. Add Value.\n"
            "Contribute meaningful conversations, ideas, opportunities & support.\n\n"
            "4. Stay On Topic.\n"
            "Use the correct topic/category for discussions.\n\n"
            "5. No Toxic Arguments.\n"
            "Healthy discussions are welcome.\n"
            "Disrespectful fights and unnecessary drama are not.\n\n"
            "6. No Unauthorized Advertising.\n"
            "Do not promote businesses, groups, channels or services without admin approval.\n\n"
            "7. Protect the Community Quality.\n"
            "We want EXPLOR to remain organized, premium & valuable for everyone.\n\n"
            "8. No Explicit or Offensive Content.\n"
            "Keep the community professional and welcoming.\n\n"
            "9. Respect Privacy.\n"
            "Do not share personal information or screenshots without permission.\n\n"
            "10. Follow Admin Instructions.\n"
            "Moderators and admins help maintain the quality of the community.\n\n"
            "By staying in EXPLOR, you agree to help maintain a respectful, "
            "growth-focused & high-value community environment.\n"
        ),
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    track_message(context, sent.message_id)


# ── Step 3: Start Form ─────────────────────────────────────────────
async def show_form(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    if str(user_id) not in query.data:
        await query.answer("⛔ This button is not for you.", show_alert=True)
        return

    set_state(user_id, "filling_details")

    # 6: Only clear form fields — preserve onboarding_messages list
    context.user_data["name"] = ""
    context.user_data["twitter"] = ""
    context.user_data["telegram"] = ""
    context.user_data["interests"] = ""

    # 7: Track the form intro message
    sent = await context.bot.send_message(
        chat_id=SUPERGROUP_ID,
        message_thread_id=THREADS["welcome"],
        text=(
            "📝 *Member Details Form*\n\n"
            "Let's get to know you! Your details will be shared "
            "in the Networking topic so members can connect with you.\n\n"
            "Type your answer and send it as a message here "
            "in the *Welcome* topic.\n\n"
            "――――――――――――――――――\n"
            "*Question 1 of 4*\n\n"
            "👤 What is your *name?*"
        ),
        parse_mode="Markdown"
    )
    track_message(context, sent.message_id)

    return ASK_NAME


# ── Step 4: Save Name → Ask Twitter ───────────────────────────────
async def ask_twitter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text.strip()
    print(f"📝 Name saved: {context.user_data['name']}")

    # 8: Track user's answer message
    track_message(context, update.message.message_id)

    # 9: Track bot's question message
    sent = await context.bot.send_message(
        chat_id=SUPERGROUP_ID,
        message_thread_id=THREADS["welcome"],
        text=(
            "――――――――――――――――――\n"
            "*Question 2 of 4*\n\n"
            "🐦 What is your *Twitter/X username?*\n"
            "_(e.g. @elonmusk — include the @ symbol)_\n\n"
            "_Type_ `none` _if you don't have one._"
        ),
        parse_mode="Markdown"
    )
    track_message(context, sent.message_id)

    return ASK_TWITTER


# ── Step 5: Save Twitter → Ask Telegram ───────────────────────────
async def ask_telegram(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["twitter"] = update.message.text.strip()
    print(f"📝 Twitter saved: {context.user_data['twitter']}")

    # ✅ Track user answer + bot question
    track_message(context, update.message.message_id)

    sent = await context.bot.send_message(
        chat_id=SUPERGROUP_ID,
        message_thread_id=THREADS["welcome"],
        text=(
            "――――――――――――――――――\n"
            "*Question 3 of 4*\n\n"
            "✈️ What is your *Telegram username?*\n"
            "_(e.g. @username — this is how members will reach you)_\n\n"
            "_Type_ `none` _if you haven't set one yet._"
        ),
        parse_mode="Markdown"
    )
    track_message(context, sent.message_id)

    return ASK_TELEGRAM


# ── Step 6: Save Telegram → Ask Interests ─────────────────────────
async def ask_interests(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["telegram"] = update.message.text.strip()
    print(f"📝 Telegram saved: {context.user_data['telegram']}")

    # ✅ Track user answer + bot question
    track_message(context, update.message.message_id)

    sent = await context.bot.send_message(
        chat_id=SUPERGROUP_ID,
        message_thread_id=THREADS["welcome"],
        text=(
            "――――――――――――――――――\n"
            "*Question 4 of 4*\n\n"
            "🎯 What are your *interests?*\n\n"
            "Choose from the list below or type your own — "
            "separate multiple with commas:\n\n"
            "• Entrepreneurship\n"
            "• Technology\n"
            "• Social Media & Content\n"
            "• Finance & Investing\n"
            "• Creative Arts\n"
            "• Health & Wellness\n"
            "• Real Estate\n"
            "• Marketing & Branding\n\n"
            "_(e.g. Technology, Finance & Investing, Marketing)_"
        ),
        parse_mode="Markdown"
    )
    track_message(context, sent.message_id)

    return ASK_INTERESTS


# ── Step 7: Save Interests → Show Confirmation ────────────────────
async def confirm_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["interests"] = update.message.text.strip()
    print(f"📝 Interests saved: {context.user_data['interests']}")
    print(f"📋 All details: {context.user_data}")

    # ✅ Track user's last answer
    track_message(context, update.message.message_id)

    name      = context.user_data.get("name", "N/A")
    twitter   = context.user_data.get("twitter", "N/A")
    telegram  = context.user_data.get("telegram", "N/A")
    interests = context.user_data.get("interests", "N/A")

    user_id = update.effective_user.id

    keyboard = [
        [InlineKeyboardButton(
            "✅ Submit", callback_data=f"confirm_submit_{user_id}"
        )],
        [InlineKeyboardButton(
            "✏️ Start Over", callback_data=f"show_form_{user_id}"
        )]
    ]

    # ✅ Track the confirmation message
    sent = await context.bot.send_message(
        chat_id=SUPERGROUP_ID,
        message_thread_id=THREADS["welcome"],
        text=(
            "――――――――――――――――――\n"
            "📋 *Please confirm your details:*\n\n"
            f"*Name:* {name}\n"
            f"*Twitter/X:* {twitter}\n"
            f"*Telegram:* {telegram}\n"
            f"*Interests:* {interests}\n\n"
            "――――――――――――――――――\n"
            "Click *Submit* to complete your registration\n"
            "or *Start Over* to correct your details 👇"
        ),
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    track_message(context, sent.message_id)

    return ConversationHandler.END


# ── Step 8: Final Submit ───────────────────────────────────────────
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

    print(f"🚀 Final submit for user {user_id}")
    print(f"   Details: {name}, {twitter}, {telegram}, {interests}")

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
        print("✅ Profile posted to Networking topic")
    except Exception as e:
        print(f"❌ Networking post failed: {e}")

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
        print("✅ Entry announced in General topic")
    except Exception as e:
        print(f"❌ General post failed: {e}")

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
        print(f"✅ Full access granted to user {user_id}")
    except Exception as e:
        print(f"❌ Access grant failed: {e}")

    # 4. Mark complete
    set_state(user_id, "complete")
    clear_temp_details(user_id)

    # 10: Wipe BEFORE clearing user_data so message IDs are still available
    await wipe_welcome_messages(context, [query.message.message_id])
    print("✅ Welcome topic wiped clean")

    # 5. Clear data AFTER wipe
    context.user_data.clear()

    
