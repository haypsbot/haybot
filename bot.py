import asyncio
import os
import aiohttp
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


TOKEN = os.getenv("TOKEN")

bot = Bot(TOKEN)
dp = Dispatcher()


# ===================================
# ⚙️ НАСТРОЙКИ
# ===================================

CHAT_ID = -100XXXXXXXXXX   # <-- вставь id группы

MIN_DISCOUNT = 30          # >= 30%
POST_EVERY_DAYS = 3        # каждые 2-3 дня
CHECK_EVERY = 86400        # проверка раз в сутки


POPULAR_GAMES = [
    "gta", "fc", "fifa", "call of duty",
    "god of war", "spider", "last of us",
    "hogwarts", "red dead", "cyberpunk",
    "mortal kombat", "tekken", "elden ring"
]


UK_MANAGERS = "@BE4HOCT6 @ash_avanesyan"
TR_MANAGERS = "@Hovo120193"
SUPPORT_MANAGER = "@BE4HOCT6"


LAST_POST_TIME = datetime.min


# ===================================
# ТЕКСТЫ
# ===================================

WELCOME_TEXT = """🤖 Բարև, ես HayBot-ն եմ

Քո խելացի PlayStation օգնականը 🚀

Ես կարող եմ՝
✅ Օգնել բաժանորդագրությամբ
✅ Կապել ադմինների հետ
✅ Ցույց տալ լավագույն զեղչերը

Ընտրիր ստորև 👇
"""


# ===================================
# INLINE КНОПКИ
# ===================================

def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎮 Գնել բաժանորդագրություն", callback_data="buy")],
        [InlineKeyboardButton(text="🆘 Աջակցություն", callback_data="support")]
    ])


def country_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🇺🇦 Ուկրաինա", callback_data="uk"),
            InlineKeyboardButton(text="🇹🇷 Թուրքիա", callback_data="tr")
        ],
        [InlineKeyboardButton(text="⬅️ Հետ", callback_data="back")]
    ])


# ===================================
# КОМАНДЫ
# ===================================

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(WELCOME_TEXT, reply_markup=main_menu())


@dp.message(Command("buy"))
async def buy_cmd(message: types.Message):
    await message.answer("🎮 Ընտրիր տարածաշրջանը 👇", reply_markup=country_menu())


@dp.message(Command("support"))
async def support_cmd(message: types.Message):
    await message.answer(f"🆘 Աջակցություն 👉 {SUPPORT_MANAGER}")


# ===================================
# CALLBACK
# ===================================

@dp.callback_query(F.data == "buy")
async def buy_btn(callback: types.CallbackQuery):
    await callback.message.edit_text("🎮 Ընտրիր տարածաշրջանը 👇", reply_markup=country_menu())


@dp.callback_query(F.data == "support")
async def support_btn(callback: types.CallbackQuery):
    await callback.message.edit_text(f"🆘 Աջակցություն 👉 {SUPPORT_MANAGER}", reply_markup=main_menu())


@dp.callback_query(F.data == "uk")
async def uk(callback: types.CallbackQuery):
    await callback.message.edit_text(f"🇺🇦 Գրիր 👉 {UK_MANAGERS}", reply_markup=main_menu())


@dp.callback_query(F.data == "tr")
async def tr(callback: types.CallbackQuery):
    await callback.message.edit_text(f"🇹🇷 Գրիր 👉 {TR_MANAGERS}", reply_markup=main_menu())


@dp.callback_query(F.data == "back")
async def back(callback: types.CallbackQuery):
    await callback.message.edit_text(WELCOME_TEXT, reply_markup=main_menu())


# ===================================
# ПРИВЕТ НОВЫМ
# ===================================

@dp.message(F.new_chat_members)
async def welcome_new(message: types.Message):
    for user in message.new_chat_members:
        name = f"@{user.username}" if user.username else user.full_name

        await message.answer(
            f"👋 Բարի գալուստ, {name}!\n\n{WELCOME_TEXT}",
            reply_markup=main_menu()
        )


# ===================================
# 🔥 ДАЙДЖЕСТ СКИДОК
# ===================================

def is_popular(title: str):
    title = title.lower()
    return any(x in title for x in POPULAR_GAMES)


async def discounts_digest():
    global LAST_POST_TIME

    while True:
        try:
            now = datetime.now()

            if now - LAST_POST_TIME < timedelta(days=POST_EVERY_DAYS):
                await asyncio.sleep(CHECK_EVERY)
                continue

            async with aiohttp.ClientSession() as session:
                async with session.get("https://psprices.com/api/latest-deals") as r:
                    data = await r.json()

            games = []

            for game in data:
                title = game["title"]
                discount = game.get("discount", 0)

                if discount >= MIN_DISCOUNT and is_popular(title):
                    games.append((title, discount))

            if not games:
                await asyncio.sleep(CHECK_EVERY)
                continue

            games = sorted(games, key=lambda x: x[1], reverse=True)[:8]

            text = "🔥 PlayStation Store զեղչեր (Top deals)\n\n"

            for title, discount in games:
                text += f"🎮 {title} — -{discount}%\n"

            text += "\nՇտապիր մինչև զեղչի ավարտը 🚀\n👉 Օգտագործիր HayBot /start"

            await bot.send_message(CHAT_ID, text)

            LAST_POST_TIME = now

        except Exception as e:
            print("Digest error:", e)

        await asyncio.sleep(CHECK_EVERY)


# ===================================
# ЗАПУСК
# ===================================

async def main():
    asyncio.create_task(discounts_digest())
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())