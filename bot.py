import asyncio
import os
import aiohttp
from bs4 import BeautifulSoup
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

CHAT_ID = -100XXXXXXXXXX

MIN_DISCOUNT = 30
TOP_COUNT = 5
POST_EVERY_DAYS = 3
CHECK_EVERY = 86400

REGIONS = ["ukraine", "turkey"]


POPULAR_GAMES = [
    "gta", "fc", "fifa", "call of duty",
    "god of war", "spider", "last of us",
    "hogwarts", "red dead", "cyberpunk",
    "mortal kombat", "tekken", "elden ring"
]


UK_MANAGERS = "@BE4HOCT6 @ash_avanesyan"
TR_MANAGERS = "@Hovo120193"
SUPPORT_MANAGER = "@BE4HOCT6 @Hovo120193 @ash_avanesyan"


LAST_POST_TIME = datetime.min
CACHE = []


# ===================================
# UI
# ===================================

WELCOME_TEXT = """🤖 Բարև, ես HayBot-ն եմ

Քո խելացի PlayStation օգնականը 🚀

Ես կարող եմ՝
✅ Օգնել բաժանորդագրությամբ
✅ Ցույց տալ լավագույն զեղչերը
✅ Կապել ադմինների հետ

Ընտրիր ստորև 👇
"""


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
        [InlineKeyboardButton(text="⬅️ Հետ", callback_data="back")]
    ])


# ===================================
# UTILS
# ===================================

def is_popular(title):
    t = title.lower()
    return any(x in t for x in POPULAR_GAMES)


def build_text(games):
    text = "🔥 PlayStation Store Top զեղչեր\n\n"

    for title, discount, link in games:
        text += f"🎮 {title} — -{discount}%\n🔗 {link}\n\n"

    return text


# ===================================
# 🔥 DEKUDEALS PARSER
# ===================================

async def fetch_dekudeals(region):

    url = f"https://www.dekudeals.com/items?filter[store]=playstation&filter[region]={region}&filter[discount_min]={MIN_DISCOUNT}"

    timeout = aiohttp.ClientTimeout(total=10)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(url) as r:
            html = await r.text()

    soup = BeautifulSoup(html, "html.parser")

    games = []

    cards = soup.select(".main-list-item")

    for c in cards:
        try:
            title = c.select_one(".item-name").text.strip()
            discount_text = c.select_one(".discount-badge").text.strip()

            discount = int(discount_text.replace("-", "").replace("%", ""))

            link = "https://www.dekudeals.com" + c.select_one("a")["href"]

            if discount >= MIN_DISCOUNT and is_popular(title):
                games.append((title, discount, link))
        except:
            pass

    return games


async def update_cache():
    global CACHE

    all_games = []

    for region in REGIONS:
        region_games = await fetch_dekudeals(region)
        all_games.extend(region_games)

    all_games = sorted(all_games, key=lambda x: x[1], reverse=True)

    CACHE = all_games[:TOP_COUNT]


# ===================================
# COMMANDS
# ===================================

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(WELCOME_TEXT, reply_markup=main_menu())


@dp.message(Command("buy"))
async def buy(message: types.Message):
    await message.answer("🎮 Ընտրիր տարածաշրջանը 👇", reply_markup=country_menu())


@dp.message(Command("support"))
async def support(message: types.Message):
    await message.answer(f"🆘 Աջակցություն 👉 {SUPPORT_MANAGER}")


@dp.message(Command("discounts"))
async def discounts(message: types.Message):

    if not CACHE:
        await message.answer("🔍 Զեղչեր դեռ բեռնվում են, փորձիր մի քիչ հետո")
        return

    await message.answer(build_text(CACHE))


# ===================================
# CALLBACKS
# ===================================

@dp.callback_query(F.data == "discounts")
async def discounts_btn(callback: types.CallbackQuery):
    await callback.message.edit_text(build_text(CACHE), reply_markup=main_menu())


@dp.callback_query(F.data == "buy")
async def buy_btn(callback: types.CallbackQuery):
    await callback.message.edit_text("🎮 Ընտրիր տարածաշրջանը 👇", reply_markup=country_menu())


@dp.callback_query(F.data == "support")
async def support_btn(callback: types.CallbackQuery):
    await callback.message.edit_text(f"🆘 Աջակցություն 👉 {SUPPORT_MANAGER}", reply_markup=main_menu())


@dp.callback_query(F.data == "back")
async def back(callback: types.CallbackQuery):
    await callback.message.edit_text(WELCOME_TEXT, reply_markup=main_menu())


@dp.callback_query(F.data == "uk")
async def uk(callback: types.CallbackQuery):
    await callback.message.edit_text(f"🇺🇦 Գրիր 👉 {UK_MANAGERS}", reply_markup=main_menu())


@dp.callback_query(F.data == "tr")
async def tr(callback: types.CallbackQuery):
    await callback.message.edit_text(f"🇹🇷 Գրիր 👉 {TR_MANAGERS}", reply_markup=main_menu())


# ===================================
# WELCOME
# ===================================

@dp.message(F.new_chat_members)
async def welcome(message: types.Message):
    for user in message.new_chat_members:
        name = f"@{user.username}" if user.username else user.full_name

        await message.answer(
            f"👋 Բարի գալուստ, {name}!\n\n{WELCOME_TEXT}",
            reply_markup=main_menu()
        )


# ===================================
# BACKGROUND TASKS
# ===================================

async def scheduler():
    global LAST_POST_TIME

    while True:

        await update_cache()

        now = datetime.now()

        if now - LAST_POST_TIME >= timedelta(days=POST_EVERY_DAYS) and CACHE:
            await bot.send_message(CHAT_ID, build_text(CACHE))
            LAST_POST_TIME = now

        await asyncio.sleep(CHECK_EVERY)


# ===================================
# START
# ===================================

async def main():
    asyncio.create_task(scheduler())
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())