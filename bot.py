import asyncio
import os
import aiohttp
import json
from datetime import datetime, timedelta
from pathlib import Path

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

# Напоминание о боте
BOT_REMINDER_EVERY_DAYS = 4

# Файл для хранения состояния
STATE_FILE = "bot_state.json"


POPULAR = [
    "gta", "fc", "fifa", "call of duty",
    "god of war", "spider", "last of us",
    "hogwarts", "red dead", "cyberpunk",
    "tekken", "mortal kombat", "elden ring",
    "uncharted", "horizon", "assassin",
    "batman", "witcher", "fallout", "elder scrolls"
]


UK_MANAGERS = "@BE4HOCT6 @ash_avanesyan"
TR_MANAGERS = "@Hovo120193"
SUPPORT_MANAGER = "@BE4HOCT6 @Hovo120193 @ash_avanesyan"


CACHE = []


# ==============================
# 💾 СОХРАНЕНИЕ И ЗАГРУЗКА СОСТОЯНИЯ
# ==============================

def load_state():
    """
    Загружает даты последних постов из файла
    """
    if Path(STATE_FILE).exists():
        try:
            with open(STATE_FILE, 'r') as f:
                data = json.load(f)
                return {
                    'last_post': datetime.fromisoformat(data.get('last_post', datetime.min.isoformat())),
                    'last_fb_post': datetime.fromisoformat(data.get('last_fb_post', datetime.min.isoformat())),
                    'last_bot_reminder': datetime.fromisoformat(data.get('last_bot_reminder', datetime.min.isoformat()))
                }
        except Exception as e:
            print(f"⚠️ Ошибка загрузки состояния: {e}")
    
    return {
        'last_post': datetime.min,
        'last_fb_post': datetime.min,
        'last_bot_reminder': datetime.min
    }


def save_state(last_post, last_fb_post, last_bot_reminder):
    """
    Сохраняет даты последних постов в файл
    """
    try:
        data = {
            'last_post': last_post.isoformat(),
            'last_fb_post': last_fb_post.isoformat(),
            'last_bot_reminder': last_bot_reminder.isoformat()
        }
        with open(STATE_FILE, 'w') as f:
            json.dump(data, f)
        print("💾 Состояние сохранено")
    except Exception as e:
        print(f"⚠️ Ошибка сохранения состояния: {e}")


# Загружаем состояние при старте
state = load_state()
LAST_POST = state['last_post']
LAST_FB_POST = state['last_fb_post']
LAST_BOT_REMINDER = state['last_bot_reminder']


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
    try:
        url = "https://www.cheapshark.com/api/1.0/deals"
        params = {
            'storeID': '1',
            'upperPrice': '30',
            'onSale': '1',
            'pageSize': '50'
        }
        
        timeout = aiohttp.ClientTimeout(total=10)
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url, params=params) as r:
                if r.status == 200:
                    data = await r.json()
                    print(f"✅ CheapShark вернул {len(data)} результатов")
                    
                    games = []
                    for item in data:
                        title = item.get('title', '')
                        normal_price = float(item.get('normalPrice', 0))
                        sale_price = float(item.get('salePrice', 0))
                        
                        if normal_price > 0:
                            discount = int(((normal_price - sale_price) / normal_price) * 100)
                            if discount >= MIN_DISCOUNT and popular(title):
                                link = f"https://www.cheapshark.com/redirect?dealID={item.get('dealID', '')}"
                                games.append((title, discount, link))
                    
                    return games
    except Exception as e:
        print(f"❌ CheapShark ошибка: {e}")
    
    return []


async def update_cache():
    global CACHE

    print("🔄 Обновляю кэш скидок...")
    games = await fetch_deals()

    if games:
        games.sort(key=lambda x: x[1], reverse=True)
        CACHE = games[:TOP_COUNT]
        print(f"✅ Найдено {len(CACHE)} реальных игр со скидками")
    else:
        print("⚠️ Реальные скидки не найдены")
        CACHE = []


def format_games():
    if not CACHE:
        return """❌ Ներկայումս մեծ զեղչեր չկան

🔍 Խնդրում ենք ստուգել մի փոքր ավելի ուշ կամ այցելել՝
🌐 https://store.playstation.com/en-us/pages/latest

📱 Կամ կապվել մեր մենեջերների հետ՝
{support}

Մենք միշտ տեղեկացնում ենք լավագույն զեղչերի մասին! 🔥""".format(support=SUPPORT_MANAGER)

    text = "🔥 Top PlayStation զեղչեր\n\n"

    for t, d, l in CACHE:
        text += f"🎮 {t} — -{d}%\n🔗 {l}\n\n"
    
    text += "\n💡 Ավելի շատ զեղչեր՝ https://store.playstation.com/"

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
    msg = await m.answer("🔄 Թարմացնում եմ զեղչերը...")
    await update_cache()
    await msg.edit_text(format_games(), reply_markup=only_back())


# ==============================
# 🔑 РЕАКЦИЯ НА КЛЮЧЕВЫЕ СЛОВА
# ==============================

@dp.message(F.text)
async def handle_keywords(message: types.Message):
    if message.chat.type == "private":
        return
        
    text = message.text.lower()
    
    if text.startswith('/'):
        return
    
    keywords_discounts = ['զեղչ', 'скидка', 'discount', 'акция', 'sale', 'zexj']
    keywords_buy = ['գնել', 'купить', 'ps plus', 'подписка', 'բաժանորդ', 'subscription', 'padpiska', 'psplus', 'ukraina', 'ukrainakan', 'turqakan']
    keywords_bot = ['բոտ', 'бот', 'bot', 'հայբոտ', 'haybot']
    
    if any(word in text for word in keywords_discounts):
        await message.reply(
            "🔥 Ուզում ես տեսնել զեղչերը?\n\n"
            "Օգտագործիր՝ /discounts",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔥 Ցույց տալ զեղչերը", callback_data="discounts")]
            ])
        )
        return
    
    if any(word in text for word in keywords_buy):
        await message.reply(
            "🎮 Ուզում ես գնել PS Plus?\n\n"
            "Օգտագործիր՝ /buy",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🎮 Գնել բաժանորդագրություն", callback_data="buy")]
            ])
        )
        return
    
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
    await c.message.edit_text("🔄 Թարմացնում եմ զեղչերը...")
    await update_cache()
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

        # Отправка скидок ТОЛЬКО если они есть
        if datetime.now() - LAST_POST >= timedelta(days=POST_EVERY_DAYS):
            if CACHE:
                await bot.send_message(CHAT_ID, format_games())
                print("✅ Скидки отправлены в канал")
            else:
                print("⏭️ Скидок нет, пропускаем отправку")
            
            LAST_POST = datetime.now()
            save_state(LAST_POST, LAST_FB_POST, LAST_BOT_REMINDER)

        # Отправка приглашения в Facebook группу
        if datetime.now() - LAST_FB_POST >= timedelta(days=FB_POST_EVERY_DAYS):
            await bot.send_message(CHAT_ID, FB_GROUP_MESSAGE)
            LAST_FB_POST = datetime.now()
            save_state(LAST_POST, LAST_FB_POST, LAST_BOT_REMINDER)
            print("✅ Приглашение в Facebook группу отправлено")

        # Напоминание о боте
        if datetime.now() - LAST_BOT_REMINDER >= timedelta(days=BOT_REMINDER_EVERY_DAYS):
            await bot.send_message(CHAT_ID, BOT_REMINDER_MESSAGE)
            LAST_BOT_REMINDER = datetime.now()
            save_state(LAST_POST, LAST_FB_POST, LAST_BOT_REMINDER)
            print("✅ Напоминание о боте отправлено")

        await asyncio.sleep(CHECK_EVERY)


# ==============================
# ЗАПУСК
# ==============================

async def main():
    print("🤖 Бот запускается...")
    print("👋 Приветствие новых участников включено")
    print(f"📱 Facebook посты каждые {FB_POST_EVERY_DAYS} дня")
    print(f"🔥 Скидки каждые {POST_EVERY_DAYS} дня (только реальные)")
    print(f"💡 Напоминания о боте каждые {BOT_REMINDER_EVERY_DAYS} дня")
    print("🔑 Реакция на ключевые слова включена")
    print(f"📅 Последний пост со скидками: {LAST_POST}")
    print(f"📅 Последний Facebook пост: {LAST_FB_POST}")
    print(f"📅 Последнее напоминание: {LAST_BOT_REMINDER}")
    
    asyncio.create_task(scheduler())
    
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=["message", "callback_query", "chat_member"])


if __name__ == "__main__":
    asyncio.run(main())