# main.py
import os
import sys
import asyncio
import threading
import traceback

from flask import Flask

app = Flask(__name__)
bot_name = "FX_LIKES_BOT"


@app.route('/')
def home():
    return f"Bot {bot_name} is active — FX LIKES"


def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)


flask_thread = threading.Thread(target=run_flask, daemon=True)
flask_thread.start()

from dotenv import load_dotenv
if os.path.exists(".env"):
    load_dotenv()

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

try:
    from accounts import GUEST_ACCOUNTS, DEFAULT_REGION, CREDITS, LOGO_TEXT
except ImportError:
    GUEST_ACCOUNTS = []
    DEFAULT_REGION = "IND"
    CREDITS = ["@FX_RAJXMODS"]
    LOGO_TEXT = "FX LIKES"

try:
    import like_body
    LIKE_AVAILABLE = True
except ImportError:
    LIKE_AVAILABLE = False
    print("⚠️ like_body.py not found — likes will not work")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")


# ============================================================
# LIKES SEND FUNCTION
# ============================================================
def send_likes_to_uid(target_uid: str, amount: int = 100):
    if not LIKE_AVAILABLE:
        return 0

    if amount > 100:
        amount = 100
    if amount > len(GUEST_ACCOUNTS):
        amount = len(GUEST_ACCOUNTS)

    accounts_to_use = GUEST_ACCOUNTS[:amount]
    total_likes = 0

    for acc in accounts_to_use:
        try:
            result = like_body.send_like(
                acc["uid"], acc["password"], target_uid, DEFAULT_REGION
            )
            if result:
                total_likes += 1
        except Exception as e:
            print(f"❌ Error with {acc['uid']}: {e}")

    return total_likes


# ============================================================
# MENU (Inline Buttons)
# ============================================================
def get_main_menu():
    keyboard = [
        [InlineKeyboardButton("🎯 Send 50 Likes", callback_data="like_50")],
        [InlineKeyboardButton("🔥 Send 100 Likes", callback_data="like_100")],
        [InlineKeyboardButton("💎 Send 220 Likes", callback_data="like_220")],
        [InlineKeyboardButton("👑 Owner", callback_data="owner")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_back_menu():
    keyboard = [
        [InlineKeyboardButton("🔙 Back to Menu", callback_data="back_menu")],
    ]
    return InlineKeyboardMarkup(keyboard)


# ============================================================
# /start COMMAND
# ============================================================
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        f"👋 Welcome to {LOGO_TEXT}\n\n"
        f"I am a Free Fire Likes Sender Bot.\n"
        f"Choose an option below:\n\n"
        f"👑 Owner: {' '.join(CREDITS)}"
    )
    await update.message.reply_text(text, reply_markup=get_main_menu())


# ============================================================
# /help COMMAND
# ============================================================
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        f"📖 Help Menu\n\n"
        f"1️⃣ /start — Start the bot\n"
        f"2️⃣ /like — Likes menu\n"
        f"3️⃣ /owner — Owner details\n"
        f"4️⃣ /help — This menu\n\n"
        f"How to send likes:\n"
        f"• Press /start\n"
        f"• Choose a button (50/100/220)\n"
        f"• Send your UID\n"
        f"• Likes will be delivered"
    )
    await update.message.reply_text(text)


# ============================================================
# /owner COMMAND
# ============================================================
async def owner_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        f"🎯 {LOGO_TEXT}\n\n"
        f"👑 Owner: {' '.join(CREDITS)}\n"
        f"🤖 Bot: Free Fire Likes Sender\n"
        f"⚡ Version: 1.0"
    )
    await update.message.reply_text(text)


# ============================================================
# /like COMMAND
# ============================================================
async def like_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        f"🎯 Likes Sender\n\n"
        f"How many likes do you want to send? Choose below:"
    )
    await update.message.reply_text(text, reply_markup=get_main_menu())


# ============================================================
# BUTTON HANDLER
# ============================================================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "back_menu":
        text = (
            f"👋 Welcome to {LOGO_TEXT}\n\n"
            f"I am a Free Fire Likes Sender Bot.\n"
            f"Choose an option below:\n\n"
            f"👑 Owner: {' '.join(CREDITS)}"
        )
        await query.edit_message_text(text, reply_markup=get_main_menu())
        return

    if data == "owner":
        text = (
            f"🎯 {LOGO_TEXT}\n\n"
            f"👑 Owner: {' '.join(CREDITS)}\n"
            f"🤖 Bot: Free Fire Likes Sender\n"
            f"⚡ Version: 1.0"
        )
        await query.edit_message_text(text, reply_markup=get_back_menu())
        return

    if data.startswith("like_"):
        amount = int(data.split("_")[1])
        context.user_data["amount"] = amount
        context.user_data["awaiting_uid"] = True
        await query.edit_message_text(
            f"✅ You selected {amount} likes.\n\n"
            f"Now send your Free Fire UID:",
            reply_markup=get_back_menu()
        )


# ============================================================
# MESSAGE HANDLER (takes UID)
# ============================================================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("awaiting_uid"):
        await update.message.reply_text(
            "❌ Please press /start and choose an option first."
        )
        return

    target_uid = update.message.text.strip()

    if not target_uid.isdigit():
        await update.message.reply_text("❌ UID must contain numbers only.")
        return

    amount = context.user_data.get("amount", 100)
    context.user_data["awaiting_uid"] = False

    msg = await update.message.reply_text(
        f"⏳ Sending {amount} likes to UID {target_uid}...\nPlease wait..."
    )

    loop = asyncio.get_event_loop()
    total_likes = await loop.run_in_executor(
        None, send_likes_to_uid, target_uid, amount
    )

    result_text = (
        f"✅ Likes Sent Successfully!\n\n"
        f"🎯 Target UID: {target_uid}\n"
        f"📤 Requested: {amount}\n"
        f"💎 Total Likes Sent: {total_likes}\n\n"
        f"👑 Owner: {' '.join(CREDITS)}"
    )

    await msg.edit_text(result_text, reply_markup=get_back_menu())


# ============================================================
# MAIN
# ============================================================
async def main():
    if not TELEGRAM_TOKEN:
        print("❌ TELEGRAM_TOKEN not found — bot cannot start")
        return

    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("owner", owner_command))
    application.add_handler(CommandHandler("like", like_command))

    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🚀 Telegram bot starting...")
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    print("✅ Telegram bot is running")

    while True:
        await asyncio.sleep(3600)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Stopping bot...")
        sys.exit(0)
    except Exception as e:
        print(f"⚠️ Unexpected error: {e}")
        traceback.print_exc()
        sys.exit(1)