from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery
)
from aiogram.exceptions import TelegramBadRequest

import asyncio
import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo

TOKEN = "8786703693:AAEh2ackTINmlXaeo7FuTlce4U9mCMijj3E"

MAIN_ADMIN = 6696030788
ADMIN_IDS = [6696030788, 1269188869]

CHANNEL_USERNAME = "@laminox"
CHANNEL_LINK = "https://t.me/laminox"

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

subscribe_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="📢 Kanalga obuna bo‘lish", url=CHANNEL_LINK)],
        [InlineKeyboardButton(text="✅ Obunani tekshirish", callback_data="check_sub")]
    ]
)

user_modes = {}


def tashkent_time():
    return datetime.now(ZoneInfo("Asia/Tashkent"))


async def is_subscribed(user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["member", "administrator", "creator"]
    except TelegramBadRequest:
        return False


async def require_subscribe(message: Message) -> bool:
    if not await is_subscribed(message.from_user.id):
        await message.answer(
            "🔒 Murojaat yuborish uchun avval kanalimizga obuna bo‘ling.",
            reply_markup=subscribe_menu
        )
        return False
    return True


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
    if not await require_subscribe(message):
        return

    await message.answer(
        "Assalomu alaykum!\n\n"
        "🏢 LAMINOX Murojaat Markaziga xush kelibsiz.\n\n"
        "Quyidagilardan birini tanlang:",
        reply_markup=menu
    )


@dp.callback_query(F.data == "check_sub")
async def check_sub(callback: CallbackQuery):
    if not await is_subscribed(callback.from_user.id):
        await callback.answer(
            "❌ Siz hali kanalga obuna bo‘lmagansiz.",
            show_alert=True
        )
        return

    await callback.message.answer(
        "✅ Obuna tasdiqlandi.\n\n"
        "Endi murojaat turini tanlang:",
        reply_markup=menu
    )
    await callback.answer()


@dp.message(F.text == "🏢 LAMINOX haqida")
async def about(message: Message):
    if not await require_subscribe(message):
        return

    await message.answer(
        "🏢 LAMINOX Murojaat Markazi\n\n"
        "Bu yerda siz shikoyat, taklif yoki fikringizni yuborishingiz mumkin."
    )


@dp.message(F.text.in_(["📌 Shikoyat", "💡 Taklif", "🔒 Anonim murojaat"]))
async def choose_type(message: Message):
    if not await require_subscribe(message):
        return

    if message.text == "📌 Shikoyat":
        user_modes[message.from_user.id] = "Shikoyat"
        await message.answer("📌 Shikoyatingizni yuboring.")

    elif message.text == "💡 Taklif":
        user_modes[message.from_user.id] = "Taklif"
        await message.answer("💡 Taklifingizni yuboring.")

    elif message.text == "🔒 Anonim murojaat":
        user_modes[message.from_user.id] = "Anonim"
        await message.answer("🔒 Anonim murojaatingizni yuboring.")


@dp.message()
async def handle_appeal(message: Message):
    if not await require_subscribe(message):
        return

    user_id = message.from_user.id
    mode = user_modes.get(user_id, "Oddiy murojaat")
    appeal_id = next_appeal_id()
    is_anonymous = mode == "Anonim"

    text_content = message.text or message.caption or "Media yuborildi"

    save_appeal({
        "id": appeal_id,
        "type": mode,
        "user": None if is_anonymous else message.from_user.full_name,
        "text": text_content,
        "time": tashkent_time().strftime("%Y-%m-%d %H:%M:%S")
    })

    for admin_id in ADMIN_IDS:

        if is_anonymous:
            if admin_id == MAIN_ADMIN:
                user_info = (
                    "🔒 Anonim murojaat\n"
                    f"🕵️ Hidden ID: {message.from_user.id}\n"
                    f"👤 Hidden Name: {message.from_user.full_name}\n"
                    f"🔗 Hidden Username: @{message.from_user.username if message.from_user.username else 'yoq'}"
                )
            else:
                user_info = "🔒 Anonim murojaat"
        else:
            user_info = (
                f"👤 Ism: {message.from_user.full_name}\n"
                f"🆔 ID: {message.from_user.id}\n"
                f"🔗 Username: @{message.from_user.username if message.from_user.username else 'yoq'}"
            )

        caption = (
            f"📩 Yangi murojaat #{appeal_id}\n\n"
            f"📌 Turi: {mode}\n"
            f"{user_info}\n\n"
            f"🕒 Vaqt: {tashkent_time().strftime('%Y-%m-%d %H:%M')}"
        )

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
