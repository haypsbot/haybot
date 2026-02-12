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


# ==============================
# ⚙️ НАСТРОЙКИ
# ==============================

CHAT_ID = -1003257278638

MIN_DISCOUNT = 30
TOP_COUNT = 5
POST_EVERY_DAYS = 3
CHECK_EVERY = 3600  # проверка каждый час


POPULAR = [
    "gta", "fc", "fifa", "call of duty",
    "god of war", "spider", "last of us",
    "hogwarts", "red dead", "cyberpunk",
    "tekken", "mortal kombat", "elden ring"
]


UK_MANAGERS = "@BE4HOCT6 @ash_avanesyan"
TR_MANAGERS = "@Hovo120193"
SUPPORT_MANAGER = "@BE4HOCT6 @Hovo120193 @ash_avanesyan"


CACHE = []
LAST_POST = datetime.min


# ==============================
# UI
# ==============================

WELCOME = """🤖 Բարև, ես HayBot-ն եմ

Քո խելացի PlayStation օգնականը 🚀

Ես կարող եմ՝
✅ Օգնել բաժանորդագրությամբ
✅ Կապել ադմինների հետ
✅ Ցույց տալ լավագույն զեղչերը

Ընտրիր ստորև 👇
"""


def back_btn():
    return [[InlineKeyboardButton(text="⬅️ Հետ", callback_data="back")]]


def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎮 Գնել բաժանորդագրություն", callback_data="buy")],
        [InlineKeyboardButton(text="🔥 Զեղչեր", callback_data="discounts")],
        [InlineKeyboardButton(text="🆘 Աջակցություն", callback_data="support")]
    ])


def country_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🇺🇦 Ուկրաինա", callback_data="uk"),
            InlineKeyboardButton(text="🇹🇷 Թուրքիա", callback_data="tr")
        ],
        *back_btn()
    ])


def only_back():
    return InlineKeyboardMarkup(inline_keyboard=back_btn())


# ==============================
# 🔥 СКИДКИ (НОВАЯ СТАБИЛЬНАЯ ВЕРСИЯ)
# ==============================

def popular(title):
    t = title.lower()
    return any(x in t for x in POPULAR)


async def fetch_deals():
    """
    Берём ВСЕ PlayStation скидки (без региона).
    Это стабильнее и не возвращает пусто.
    """

    url = "https://www.dekudeals.com/api/v1/discounts?store=playstation"

    timeout = aiohttp.ClientTimeout(total=8)

    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as r:
                return await r.json()
    except:
        return []


async def update_cache():
    global CACHE

    data = await fetch_deals()

    if not data:
        CACHE = []
        return

    games = []

    for g in data:
        title = g.get("name", "")
        discount = int(g.get("discount_percent", 0))
        link = g.get("url", "")

        if discount >= MIN_DISCOUNT and popular(title):
            games.append((title, discount, link))

    games.sort(key=lambda x: x[1], reverse=True)
    CACHE = games[:TOP_COUNT]


def format_games():
    if not CACHE:
        return "❌ Զեղչեր չեն գտնվել"

    text = "🔥 Top PlayStation զեղչեր\n\n"

    for t, d, l in CACHE:
        text += f"🎮 {t} — -{d}%\n🔗 {l}\n\n"

    return text


# ==============================
# КОМАНДЫ
# ==============================

@dp.message(Command("start"))
async def start(m: types.Message):
    await m.answer(WELCOME, reply_markup=main_menu())


@dp.message(Command("buy"))
async def buy(m: types.Message):
    await m.answer("Ընտրիր տարածաշրջանը 👇", reply_markup=country_menu())


@dp.message(Command("support"))
async def support(m: types.Message):
    await m.answer(f"🆘 {SUPPORT_MANAGER}", reply_markup=only_back())


@dp.message(Command("discounts"))
async def discounts(m: types.Message):

    if not CACHE:
        await m.answer("🔄 Թարմացնում եմ զեղչերը, փորձիր մի քանի վայրկյանից...")
        return

    await m.answer(format_games(), reply_markup=only_back())


# ==============================
# CALLBACKS
# ==============================

@dp.callback_query(F.data == "back")
async def back(c: types.CallbackQuery):
    await c.message.edit_text(WELCOME, reply_markup=main_menu())


@dp.callback_query(F.data == "buy")
async def buy_btn(c: types.CallbackQuery):
    await c.message.edit_text("Ընտրիր տարածաշրջանը 👇", reply_markup=country_menu())


@dp.callback_query(F.data == "support")
async def support_btn(c: types.CallbackQuery):
    await c.message.edit_text(f"🆘 {SUPPORT_MANAGER}", reply_markup=only_back())


@dp.callback_query(F.data == "discounts")
async def discounts_btn(c: types.CallbackQuery):

    if not CACHE:
        await c.message.edit_text("🔄 Թարմացնում եմ զեղչերը...", reply_markup=only_back())
        return

    await c.message.edit_text(format_games(), reply_markup=only_back())


@dp.callback_query(F.data == "uk")
async def uk(c: types.CallbackQuery):
    await c.message.edit_text(f"🇺🇦 Գրիր 👉 {UK_MANAGERS}", reply_markup=only_back())


@dp.callback_query(F.data == "tr")
async def tr(c: types.CallbackQuery):
    await c.message.edit_text(f"🇹🇷 Գրիր 👉 {TR_MANAGERS}", reply_markup=only_back())


# ==============================
# ФОН
# ==============================

async def scheduler():
    global LAST_POST

    while True:

        await update_cache()

        if datetime.now() - LAST_POST >= timedelta(days=POST_EVERY_DAYS) and CACHE:
            await bot.send_message(CHAT_ID, format_games())
            LAST_POST = datetime.now()

        await asyncio.sleep(CHECK_EVERY)


# ==============================
# ЗАПУСК
# ==============================

async def main():
    asyncio.create_task(scheduler())
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())