import asyncio
import os
import aiohttp
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, ChatMemberUpdatedFilter, MEMBER
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ChatMemberUpdated


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
CHECK_EVERY = 3600

# Facebook խմբի հրապարակում
FB_POST_EVERY_DAYS = 2
LAST_FB_POST = datetime.min

# Напоминание о боте
BOT_REMINDER_EVERY_DAYS = 4
LAST_BOT_REMINDER = datetime.min


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
# 📱 СООБЩЕНИЯ
# ==============================

FB_GROUP_MESSAGE = """🎮 Միացիր մեր Հայ🇦🇲PS խմբին Facebook-ում! 🔥

📌 PS Plus բաժանորդագրություններ
📌 Խաղային հաշիվներ
📌 Օգտակար խորհուրդներ
📌 Ակտիվ community

👥 Արդեն ավելի քան 2000 հետևորդ!

🔗 Միացիր հիմա՝ https://www.facebook.com/share/g/17foQWxCyZ/

Մենք սպասում ենք քեզ! 🎯"""


BOT_REMINDER_MESSAGE = """💡 Հիշեցում՝ 

Մեր խմբում աշխատում է HayBot! 🤖

Կարող ես օգտագործել հետևյալ հրամանները՝

/start - Սկսել բոտը
/discounts - Տեսնել PlayStation զեղչերը 🔥
/buy - Գնել PS Plus բաժանորդագրություն
/support - Կապվել ադմինների հետ

Պարզապես գրիր հրամանը այստեղ՝ չատում! 👇"""


WELCOME_NEW_MEMBER = """👋 Բարի գալուստ, {name}! 

Ուրախ ենք տեսնել քեզ Հայ🇦🇲PS ալիքում! 🎮

Այստեղ դու կգտնես՝
✅ Լավագույն PlayStation զեղչեր
✅ Էժան PS Plus բաժանորդագրություններ
✅ Հուսալի խաղային հաշիվներ
✅ Օգտակար խորհուրդներ և նորություններ

🤖 Մեր բոտը օգտագործելու համար գրիր՝
/start - Սկսել բոտը
/discounts - Տեսնել զեղչերը 🔥
/buy - Գնել բաժանորդագրություն

📱 Միացիր նաև մեր Facebook խմբում՝
🔗 https://www.facebook.com/share/g/17foQWxCyZ/

Հաջող խաղ! 🎯"""


WELCOME = """🤖 Բարև, ես HayBot-ն եմ

Քո խելացի PlayStation օգնականը 🚀

Ես կարող եմ՝
✅ Օգնել բաժանորդագրությամբ
✅ Կապել ադմինների հետ
✅ Ցույց տալ լավագույն զեղչերը

Ընտրիր ստորև 👇
"""


# ==============================
# UI
# ==============================

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
# 🔥 СКИДКИ
# ==============================

def popular(title):
    t = title.lower()
    return any(x in t for x in POPULAR)


async def fetch_deals():
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
        print("⚠️ Данные не получены, использую резервные данные...")
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
# 👋 ПРИВЕТСТВИЕ НОВЫХ УЧАСТНИКОВ
# ==============================

@dp.chat_member(ChatMemberUpdatedFilter(member_status_changed=MEMBER))
async def on_user_join(event: ChatMemberUpdated):
    user = event.new_chat_member.user
    name = user.first_name or user.username or "Ընկեր"
    
    welcome_text = WELCOME_NEW_MEMBER.format(name=name)
    
    try:
        await bot.send_message(
            chat_id=event.chat.id,
            text=welcome_text
        )
        print(f"✅ Приветствие отправлено для {name}")
    except Exception as e:
        print(f"❌ Ошибка отправки приветствия: {e}")


@dp.message(F.new_chat_members)
async def on_new_chat_members(message: types.Message):
    for user in message.new_chat_members:
        name = user.first_name or user.username or "Ընկեր"
        
        welcome_text = WELCOME_NEW_MEMBER.format(name=name)
        
        try:
            await message.answer(welcome_text)
            print(f"✅ Приветствие отправлено для {name} (резервный метод)")
        except Exception as e:
            print(f"❌ Ошибка отправки приветствия: {e}")


# ==============================
# КОМАНДЫ (В ПРАВИЛЬНОМ ПОРЯДКЕ!)
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
# 🔑 РЕАКЦИЯ НА КЛЮЧЕВЫЕ СЛОВА
# ==============================

@dp.message(F.text)
async def handle_keywords(message: types.Message):
    """
    Реагирует на ключевые слова в чате
    """
    # Только в группе/канале (не в личке)
    if message.chat.type == "private":
        return
        
    text = message.text.lower()
    
    # Игнорируем команды
    if text.startswith('/'):
        return
    
    keywords_discounts = ['զեղչ', 'скидка', 'discount', 'акция', 'sale', 'zexj']
    keywords_buy = ['գնել', 'купить', 'ps plus', 'подписка', 'բաժանորդ', 'subscription', 'padpiska', 'psplus', 'ukraina', 'ukrainakan', 'turqakan']
    keywords_bot = ['բոտ', 'бот', 'bot', 'հայբոտ', 'haybot']
    
    # Если упомянули скидки
    if any(word in text for word in keywords_discounts):
        await message.reply(
            "🔥 Ուզում ես տեսնել զեղչերը?\n\n"
            "Օգտագործիր՝ /discounts",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔥 Ցույց տալ զեղչերը", callback_data="discounts")]
            ])
        )
        return
    
    # Если упомянули покупку
    if any(word in text for word in keywords_buy):
        await message.reply(
            "🎮 Ուզում ես գնել PS Plus?\n\n"
            "Օգտագործիր՝ /buy",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🎮 Գնել բաժանորդագրություն", callback_data="buy")]
            ])
        )
        return
    
    # Если упомянули бота
    if any(word in text for word in keywords_bot):
        await message.reply(
            "👋 Այո, ես այստեղ եմ!\n\n"
            "Օգտագործիր՝ /start տեսնելու ինչ կարող եմ անել 🤖"
        )
        return


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
    global LAST_POST, LAST_FB_POST, LAST_BOT_REMINDER
    
    await update_cache()

    while True:
        await update_cache()

        # Отправка скидок
        if datetime.now() - LAST_POST >= timedelta(days=POST_EVERY_DAYS) and CACHE:
            await bot.send_message(CHAT_ID, format_games())
            LAST_POST = datetime.now()
            print("✅ Скидки отправлены в канал")

        # Отправка приглашения в Facebook группу
        if datetime.now() - LAST_FB_POST >= timedelta(days=FB_POST_EVERY_DAYS):
            await bot.send_message(CHAT_ID, FB_GROUP_MESSAGE)
            LAST_FB_POST = datetime.now()
            print("✅ Приглашение в Facebook группу отправлено")

        # Напоминание о боте
        if datetime.now() - LAST_BOT_REMINDER >= timedelta(days=BOT_REMINDER_EVERY_DAYS):
            await bot.send_message(CHAT_ID, BOT_REMINDER_MESSAGE)
            LAST_BOT_REMINDER = datetime.now()
            print("✅ Напоминание о боте отправлено")

        await asyncio.sleep(CHECK_EVERY)


# ==============================
# ЗАПУСК
# ==============================

async def main():
    print("🤖 Бот запускается...")
    print("👋 Приветствие новых участников включено")
    print(f"📱 Facebook посты каждые {FB_POST_EVERY_DAYS} дня")
    print(f"🔥 Скидки каждые {POST_EVERY_DAYS} дня")
    print(f"💡 Напоминания о боте каждые {BOT_REMINDER_EVERY_DAYS} дня")
    print("🔑 Реакция на ключевые слова включена")
    
    asyncio.create_task(scheduler())
    
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=["message", "callback_query", "chat_member"])


if __name__ == "__main__":
    asyncio.run(main())
