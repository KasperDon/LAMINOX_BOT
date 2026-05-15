from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton
)

import asyncio
import json
import os
from datetime import datetime

TOKEN = "8786703693:AAGZeTKd9HH6VwzqztIeEzATShmdyXS8rqI"

ADMIN_IDS = [6696030788]

bot = Bot(token=TOKEN)
dp = Dispatcher()

DATA_FILE = "appeals.json"

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

    with open(DATA_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def save_appeal(data):
    appeals = load_appeals()
    appeals.append(data)

    with open(DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(appeals, file, ensure_ascii=False, indent=4)


def next_appeal_id():
    appeals = load_appeals()
    return 1000 + len(appeals) + 1


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
        "Bu yerda siz shikoyat, taklif yoki fikringizni yuborishingiz mumkin."
    )


@dp.message(F.text.in_(["📌 Shikoyat", "💡 Taklif", "🔒 Anonim murojaat"]))
async def choose_type(message: Message):

    if message.text == "📌 Shikoyat":
        user_modes[message.from_user.id] = "Shikoyat"

        await message.answer(
            "📌 Shikoyatingizni yuboring."
        )

    elif message.text == "💡 Taklif":
        user_modes[message.from_user.id] = "Taklif"

        await message.answer(
            "💡 Taklifingizni yuboring."
        )

    elif message.text == "🔒 Anonim murojaat":
        user_modes[message.from_user.id] = "Anonim"

        await message.answer(
            "🔒 Anonim murojaatingizni yuboring."
        )


@dp.message()
async def handle_appeal(message: Message):

    user_id = message.from_user.id
    mode = user_modes.get(user_id, "Oddiy murojaat")
    appeal_id = next_appeal_id()

    is_anonymous = mode == "Anonim"

    if is_anonymous:
        user_info = "🔒 Anonim murojaat"

    else:
        user_info = (
            f"👤 Ism: {message.from_user.full_name}\n"
            f"🆔 ID: {message.from_user.id}\n"
            f"🔗 Username: @{message.from_user.username if message.from_user.username else 'yoq'}"
        )

    text_content = message.text or message.caption or "Media yuborildi"

    save_appeal({
        "id": appeal_id,
        "type": mode,
        "user": None if is_anonymous else message.from_user.full_name,
        "text": text_content,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

    caption = (
        f"📩 Yangi murojaat #{appeal_id}\n\n"
        f"📌 Turi: {mode}\n"
        f"{user_info}\n\n"
        f"🕒 Vaqt: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    )

    for admin_id in ADMIN_IDS:

        if message.text:
            await bot.send_message(
                admin_id,
                caption + f"\n\n📝 Xabar:\n{message.text}"
            )

        elif message.photo:
            await bot.send_photo(
                admin_id,
                message.photo[-1].file_id,
                caption=caption
            )

        elif message.video:
            await bot.send_video(
                admin_id,
                message.video.file_id,
                caption=caption
            )

        elif message.document:
            await bot.send_document(
                admin_id,
                message.document.file_id,
                caption=caption
            )

        elif message.voice:
            await bot.send_voice(
                admin_id,
                message.voice.file_id,
                caption=caption
            )

        else:
            await bot.send_message(
                admin_id,
                caption + "\n📎 Media yuborildi"
            )

    await message.answer(
        f"✅ Murojaatingiz qabul qilindi.\n"
        f"📞 Raqam: #{appeal_id}"
    )


async def main():
    print("Bot ishga tushdi...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
