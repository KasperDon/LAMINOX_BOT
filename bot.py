from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
import asyncio
import json
import os
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

TOKEN = "8786703693:AAGZeTKd9HH6VwzqztIeEzATShmdyXS8rqI"
ADMIN_IDS = [6696030788]

DATA_FILE = "appeals.json"
SHEET_NAME = "LAMINOX Murojaatlar Bazasi"

bot = Bot(token=TOKEN)
dp = Dispatcher()

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

google_credentials = json.loads(os.environ["GOOGLE_CREDENTIALS"])
creds = Credentials.from_service_account_info(google_credentials, scopes=SCOPES)
client = gspread.authorize(creds)
sheet = client.open(SHEET_NAME).sheet1

menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📌 Shikoyat"), KeyboardButton(text="💡 Taklif")],
        [KeyboardButton(text="🔒 Anonim murojaat"), KeyboardButton(text="🏢 LAMINOX haqida")]
    ],
    resize_keyboard=True
)

user_modes = {}


def load_appeals():
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception:
        return []


def save_appeal(data):
    appeals = load_appeals()
    appeals.append(data)
    with open(DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(appeals, file, ensure_ascii=False, indent=4)


def next_appeal_id():
    appeals = load_appeals()
    return 1024 + len(appeals) + 1


@dp.message(CommandStart())
async def start(message: Message):
    await message.answer(
        "Assalomu alaykum!\n\n"
        "🏢 LAMINOX Murojaat Markaziga xush kelibsiz.\n\n"
        "Quyidagilardan birini tanlang:",
        reply_markup=menu
    )


@dp.message(F.text == "🏢 LAMINOX haqida")
async def about(message: Message):
    await message.answer(
        "🏢 LAMINOX Murojaat Markazi\n\n"
        "Bu yerda siz shikoyat, taklif yoki fikringizni yuborishingiz mumkin.\n"
        "Murojaatingiz mas’ul adminlarga yetkaziladi."
    )


@dp.message(F.text.in_(["📌 Shikoyat", "💡 Taklif", "🔒 Anonim murojaat"]))
async def choose_type(message: Message):
    if message.text == "📌 Shikoyat":
        user_modes[message.from_user.id] = "Shikoyat"
        await message.answer("📌 Shikoyatingizni matn, rasm, ovozli xabar yoki fayl ko‘rinishida yuboring.")

    elif message.text == "💡 Taklif":
        user_modes[message.from_user.id] = "Taklif"
        await message.answer("💡 Taklifingizni matn, rasm, ovozli xabar yoki fayl ko‘rinishida yuboring.")

    elif message.text == "🔒 Anonim murojaat":
        user_modes[message.from_user.id] = "Anonim"
        await message.answer("🔒 Anonim murojaatingizni yuboring. Ismingiz adminlarga ko‘rsatilmaydi.")


@dp.message()
async def handle_appeal(message: Message):
    user_id = message.from_user.id
    mode = user_modes.get(user_id, "Oddiy murojaat")
    appeal_id = next_appeal_id()
    is_anonymous = mode == "Anonim"

    if is_anonymous:
        full_name = "Anonim"
        username = "Anonim"
        telegram_id = "Anonim"
        user_info = "🔒 Anonim murojaat"
    else:
        full_name = message.from_user.full_name
        username = f"@{message.from_user.username}" if message.from_user.username else "yo'q"
        telegram_id = str(message.from_user.id)
        user_info = (
            f"👤 Ism: {full_name}\n"
            f"🆔 ID: {telegram_id}\n"
            f"🔗 Username: {username}"
        )

    text_content = message.text or message.caption or "Media/fayl yuborildi"
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    sheet.append_row([
        appeal_id,
        now,
        mode,
        full_name,
        username,
        telegram_id,
        text_content,
        "Yangi"
    ])

    save_appeal({
        "id": appeal_id,
        "type": mode,
        "user_id": None if is_anonymous else user_id,
        "username": None if is_anonymous else message.from_user.username,
        "full_name": None if is_anonymous else message.from_user.full_name,
        "text": text_content,
        "time": now,
        "status": "Yangi"
    })

    caption = (
        f"📩 Yangi murojaat #{appeal_id}\n\n"
        f"📌 Turi: {mode}\n"
        f"{user_info}\n\n"
        f"🕒 Vaqt: {now}\n"
    )

    for admin_id in ADMIN_IDS:
        if message.text:
            await bot.send_message(admin_id, caption + f"\n📝 Xabar:\n{message.text}")

        elif message.photo:
            await bot.send_photo(
                admin_id,
                message.photo[-1].file_id,
                caption=caption + f"\n🖼 Rasm\n{message.caption or ''}"
            )

        elif message.voice:
            await bot.send_voice(
                admin_id,
                message.voice.file_id,
                caption=caption + "\n🎤 Ovozli murojaat"
            )

        elif message.document:
            await bot.send_document(
                admin_id,
                message.document.file_id,
                caption=caption + f"\n📁 Fayl\n{message.caption or ''}"
            )

        elif message.video:
            await bot.send_video(
                admin_id,
                message.video.file_id,
                caption=caption + f"\n🎥 Video\n{message.caption or ''}"
            )

        else:
            await bot.send_message(admin_id, caption + "\n📎 Boshqa turdagi xabar yuborildi.")

    await message.answer(
        f"✅ Murojaatingiz qabul qilindi.\n"
        f"📞 Murojaat raqami: #{appeal_id}"
    )


async def main():
    print("Bot ishga tushdi...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
