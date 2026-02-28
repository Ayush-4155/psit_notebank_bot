from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)
import os

# ---------------- BOT CONFIG ----------------
TOKEN = "8689919670:AAFBCUA7KrWzG5eCPdxeEXvqNQyRfeRRaJo"
ADMIN_ID = 7111408119
APPROVED_FILE = "approved_users.txt"

# ---------------- FILE STORAGE ----------------
FILES = {
    "Data Structure": {
        "Unit 1": "BQACAgUAAxkBAAMLaaHgBwLySjdAwLOY_UnM26WPD9EAAykAAg6tEFXXl4o2VT2WUToE",
        "Unit 2": "",
        "Unit 3": "",
        "Unit 4": "",
        "Unit 5": "",
    },
    "Maths 2nd": {
        "Unit 1": "",
        "Unit 2": "",
        "Unit 3": "",
        "Unit 4": "",
        "Unit 5": "",
    },
    "EVS": {
        "Unit 1": "",
        "Unit 2": "",
        "Unit 3": "",
        "Unit 4": "",
        "Unit 5": "",
    },
    "Discrete Mathematics": {
        "Unit 1": "",
        "Unit 2": "",
        "Unit 3": "",
        "Unit 4": "",
        "Unit 5": "",
    },
    "DLD": {
        "Unit 1": "",
        "Unit 2": "",
        "Unit 3": "",
        "Unit 4": "",
        "Unit 5": "",
    }
}

SUBJECTS = list(FILES.keys())
PAGE_SIZE = 3


# ---------------- APPROVAL SYSTEM ----------------
def load_approved_users():
    if not os.path.exists(APPROVED_FILE):
        return set()
    with open(APPROVED_FILE, "r") as f:
        return set(line.strip() for line in f.readlines())


def save_approved_user(user_id):
    with open(APPROVED_FILE, "a") as f:
        f.write(str(user_id) + "\n")


def remove_approved_user(user_id):
    if not os.path.exists(APPROVED_FILE):
        return
    with open(APPROVED_FILE, "r") as f:
        users = f.readlines()
    with open(APPROVED_FILE, "w") as f:
        for u in users:
            if u.strip() != str(user_id):
                f.write(u)


APPROVED_USERS = load_approved_users()


async def check_approval(update: Update):
    user_id = str(update.effective_user.id)

    if user_id in APPROVED_USERS:
        return True

    text = (
        f"👤 *New User Request*\n"
        f"Name: {update.effective_user.first_name}\n"
        f"Username: @{update.effective_user.username}\n"
        f"User ID: `{user_id}`"
    )

    keyboard = [
        [
            InlineKeyboardButton("✅ Approve", callback_data=f"approve|{user_id}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"reject|{user_id}")
        ]
    ]

    await update.get_bot().send_message(
        chat_id=ADMIN_ID,
        text=text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    await update.message.reply_text("⏳ Your request has been sent to the admin. Please wait.")
    return False


# ---------------- START ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_approval(update):
        return

    keyboard = [
        [InlineKeyboardButton("📂 Browse Files", callback_data="browse|0")],
        [InlineKeyboardButton("ℹ️ About", callback_data="about")]
    ]

    await update.message.reply_text(
        "📁 College Notes\nSelect an option:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ---------------- BUTTONS ----------------
def get_subject_buttons(start):
    buttons = []
    for subj in SUBJECTS[start:start + PAGE_SIZE]:
        buttons.append([InlineKeyboardButton(subj, callback_data=f"subject|{subj}")])

    if start + PAGE_SIZE < len(SUBJECTS):
        buttons.append([InlineKeyboardButton("➕ More Options", callback_data=f"browse|{start + PAGE_SIZE}")])

    buttons.append([InlineKeyboardButton("🔙 Back", callback_data="main")])
    return InlineKeyboardMarkup(buttons)


def get_unit_buttons(subject):
    buttons = []
    for unit in FILES[subject].keys():
        buttons.append([InlineKeyboardButton(unit, callback_data=f"unit|{subject}|{unit}")])
    buttons.append([InlineKeyboardButton("🔙 Back", callback_data="browse|0")])
    return InlineKeyboardMarkup(buttons)


# ---------------- CALLBACK HANDLER ----------------
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.split("|")

    # ADMIN APPROVAL
    if data[0] == "approve":
        user_id = data[1]
        APPROVED_USERS.add(user_id)
        save_approved_user(user_id)

        await query.edit_message_text("✅ User Approved")
        await query.bot.send_message(user_id, "🎉 You are approved! Use /start to continue.")
        return

    if data[0] == "reject":
        user_id = data[1]
        await query.edit_message_text("❌ User Rejected")
        await query.bot.send_message(user_id, "❌ Your access was not approved.")
        return

    # REQUIRE APPROVAL
    user_id = str(query.from_user.id)
    if user_id not in APPROVED_USERS:
        await query.message.reply_text("⏳ Waiting for admin approval…")
        return

    # BROWSE SUBJECT LIST
    if data[0] == "browse":
        start = int(data[1])
        await query.edit_message_text("📂 Browse Files:", reply_markup=get_subject_buttons(start))

    # SUBJECT SELECTED
    elif data[0] == "subject":
        subject = data[1]
        await query.edit_message_text(
            f"📘 {subject}\nSelect a Unit:",
            reply_markup=get_unit_buttons(subject)
        )

    # UNIT SELECTED → SEND FILE
    elif data[0] == "unit":
        subject = data[1]
        unit = data[2]

        file_id = FILES.get(subject, {}).get(unit)

        if not file_id:
            await query.message.reply_text("❌ File is unavailable !!")
            return

        await query.message.reply_document(file_id)

        APPROVED_USERS.discard(user_id)
        remove_approved_user(user_id)

        await query.message.reply_text(
            "✔️ You used your 1-time access.\n"
            "🔄 Request approval again to download another file."
        )

    # ABOUT SECTION
    elif data[0] == "about":
        await query.edit_message_text("ℹ️ College Notes Bot\nCreated to share notes easily.\nBy ._.A Y U S H._.")

    # MAIN MENU
    elif data[0] == "main":
        keyboard = [
            [InlineKeyboardButton("📂 Browse Files", callback_data="browse|0")],
            [InlineKeyboardButton("ℹ️ About", callback_data="about")]
        ]
        await query.edit_message_text("📁 College Notes\nSelect an option:", reply_markup=InlineKeyboardMarkup(keyboard))


# ---------------- ADMIN FILE-ID HELPER ----------------
async def get_file_id(update: Update, context):
    if update.effective_user.id != ADMIN_ID:
        return
    if update.message.document:
        await update.message.reply_text(f"FILE ID:\n{update.message.document.file_id}")


# ---------------- RUN BOT ----------------
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button))
app.add_handler(MessageHandler(filters.Document.ALL, get_file_id))

print("Bot is running...")
app.run_polling()