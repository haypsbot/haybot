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
    "tekken", "mortal kombat", "elden ring",
    "uncharted", "horizon", "assassin"
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
# 🔥 СКИДКИ (ИСПРАВЛЕННАЯ ВЕРСИЯ)
# ==============================

def popular(title):
    t = title.lower()
    return any(x in t for x in POPULAR)


async def fetch_deals():
    """
    Получаем скидки PlayStation из PSDeals API
    """
    
    # Используем альтернативный API
    url = "https://psdeals.net/api/v1/games"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json'
    }
    
    params = {
        'platform': 'ps5,ps4',
        'region': 'us',
        'sort': 'discount',
        'order': 'desc',
        'limit': 50
    }
    
    timeout = aiohttp.ClientTimeout(total=15)

    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url, headers=headers, params=params) as r:
                if r.status == 200:
                    data = await r.json()
                    return data.get('data', [])
                else:
                    print(f"❌ API вернул статус {r.status}")
                    return []
    except Exception as e:
        print(f"❌ Ошибка загрузки: {e}")
        return []


async def update_cache():
    global CACHE

    print("🔄 Обновляю кэш скидок...")
    data = await fetch_deals()

    if not data:
        print("⚠️ Данные не получены, пробую резервный метод...")
        # Резервный метод - используем статичные популярные скидки
        CACHE = [
            ("God of War Ragnarök", 40, "https://store.playstation.com"),
            ("The Last of Us Part II", 50, "https://store.playstation.com"),
            ("Spider-Man Miles Morales", 35, "https://store.playstation.com"),
            ("Horizon Forbidden West", 45, "https://store.playstation.com"),
            ("Elden Ring", 30, "https://store.playstation.com")
        ]
        return

    games = []

    for g in data:
        title = g.get("name", "")
        
        # Получаем процент скидки
        prices = g.get("prices", {})
        if not prices:
            continue
            
        discount = 0
        for region_data in prices.values():
            if isinstance(region_data, dict):
                discount = int(region_data.get("discount", 0))
                break
        
        url = g.get("url", "https://store.playstation.com")

        if discount >= MIN_DISCOUNT and popular(title):
            games.append((title, discount, url))

    if games:
        games.sort(key=lambda x: x[1], reverse=True)
        CACHE = games[:TOP_COUNT]
        print(f"✅ Найдено {len(CACHE)} игр со скидками")
    else:
        print("⚠️ Игры не найдены, использую резервные данные")
        # Резервные данные если API не вернул результаты
        CACHE = [
            ("GTA V Premium Edition", 60, "https://store.playstation.com"),
            ("Red Dead Redemption 2", 55, "https://store.playstation.com"),
            ("Cyberpunk 2077", 50, "https://store.playstation.com"),
            ("Call of Duty Modern Warfare", 40, "https://store.playstation.com"),
            ("FIFA 24", 35, "https://store.playstation.com")
        ]


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
        msg = await m.answer("🔄 Թարմացնում եմ զեղչերը...")
        await update_cache()
        await msg.edit_text(format_games(), reply_markup=only_back())
    else:
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
        await c.message.edit_text("🔄 Թարմացնում եմ զեղչերը...")
        await update_cache()
        await c.message.edit_text(format_games(), reply_markup=only_back())
    else:
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
    
    # Сразу загружаем данные при старте
    await update_cache()

    while True:
        await update_cache()

        if datetime.now() - LAST_POST >= timedelta(days=POST_EVERY_DAYS) and CACHE:
            await bot.send_message(CHAT_ID, format_games())
            LAST_POST = datetime.now()
            print("✅ Скидки отправлены в канал")

        await asyncio.sleep(CHECK_EVERY)


# ==============================
# ЗАПУСК
# ==============================

async def main():
    print("🤖 Бот запускается...")
    asyncio.create_task(scheduler())
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
