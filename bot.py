import asyncio
import os
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

CHECK_EVERY = 3600
FB_POST_EVERY_DAYS = 2
BOT_REMINDER_EVERY_DAYS = 4

# Файлы для хранения данных
STATE_FILE = "bot_state.json"
USERS_FILE = "users.json"


UK_MANAGERS = "@BE4HOCT6 @ash_avanesyan @VARDAN_XACHATRYAN"
TR_MANAGERS = "@Hovo120193"
SUPPORT_MANAGER = "@BE4HOCT6 @Hovo120193 @ash_avanesyan @VARDAN_XACHATRYAN"


# ==============================
# 💾 РАБОТА С ДАННЫМИ
# ==============================

def load_json(filename, default=None):
    """Загружает JSON файл"""
    if Path(filename).exists():
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ Ошибка загрузки {filename}: {e}")
    return default or {}


def save_json(filename, data):
    """Сохраняет в JSON файл"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ Ошибка сохранения {filename}: {e}")


def load_state():
    data = load_json(STATE_FILE, {
        'last_fb_post': datetime.min.isoformat(),
        'last_bot_reminder': datetime.min.isoformat(),
        'total_users': 0,
        'total_messages': 0,
        'new_members': 0,
        'bot_started': datetime.now().isoformat()
    })
    return {
        'last_fb_post': datetime.fromisoformat(data.get('last_fb_post', datetime.min.isoformat())),
        'last_bot_reminder': datetime.fromisoformat(data.get('last_bot_reminder', datetime.min.isoformat())),
        'total_users': data.get('total_users', 0),
        'total_messages': data.get('total_messages', 0),
        'new_members': data.get('new_members', 0),
        'bot_started': datetime.fromisoformat(data.get('bot_started', datetime.now().isoformat()))
    }


def save_state(last_fb_post, last_bot_reminder, total_users, total_messages, new_members, bot_started):
    save_json(STATE_FILE, {
        'last_fb_post': last_fb_post.isoformat(),
        'last_bot_reminder': last_bot_reminder.isoformat(),
        'total_users': total_users,
        'total_messages': total_messages,
        'new_members': new_members,
        'bot_started': bot_started.isoformat()
    })


# Загружаем данные
state = load_state()
LAST_FB_POST = state['last_fb_post']
LAST_BOT_REMINDER = state['last_bot_reminder']
TOTAL_USERS = state['total_users']
TOTAL_MESSAGES = state['total_messages']
NEW_MEMBERS = state['new_members']
BOT_STARTED = state['bot_started']

USERS = load_json(USERS_FILE, {})


def get_user(user_id):
    """Получает данные пользователя"""
    uid = str(user_id)
    if uid not in USERS:
        USERS[uid] = {
            'name': '',
            'username': '',
            'points': 0,
            'messages': 0,
            'commands': 0,
            'joined': datetime.now().isoformat(),
            'last_active': datetime.now().isoformat()
        }
        save_json(USERS_FILE, USERS)
    return USERS[uid]


def add_points(user_id, points, reason=""):
    """Добавляет очки пользователю"""
    user = get_user(user_id)
    user['points'] += points
    save_json(USERS_FILE, USERS)
    print(f"✅ {user.get('name', user_id)} получил {points} очков за {reason}")


def track_message(user_id, username="", first_name=""):
    """Отслеживает сообщение пользователя"""
    global TOTAL_MESSAGES, TOTAL_USERS
    
    user = get_user(user_id)
    user['messages'] += 1
    user['last_active'] = datetime.now().isoformat()
    
    if username and not user.get('username'):
        user['username'] = username
    if first_name and not user.get('name'):
        user['name'] = first_name
    
    # +1 очко за каждые 10 сообщений
    if user['messages'] % 10 == 0:
        add_points(user_id, 1, "активность")
    
    TOTAL_MESSAGES += 1
    
    # Считаем уникальных пользователей
    TOTAL_USERS = len(USERS)
    
    save_json(USERS_FILE, USERS)
    save_state(LAST_FB_POST, LAST_BOT_REMINDER, TOTAL_USERS, TOTAL_MESSAGES, NEW_MEMBERS, BOT_STARTED)


def track_command(user_id):
    """Отслеживает использование команды"""
    user = get_user(user_id)
    user['commands'] += 1
    add_points(user_id, 2, "команду")
    save_json(USERS_FILE, USERS)


def track_new_member():
    """Отслеживает нового участника группы"""
    global NEW_MEMBERS
    NEW_MEMBERS += 1
    save_state(LAST_FB_POST, LAST_BOT_REMINDER, TOTAL_USERS, TOTAL_MESSAGES, NEW_MEMBERS, BOT_STARTED)


# ==============================
# 📊 СТАТИСТИКА И РЕЙТИНГ
# ==============================

def get_top_users(limit=10):
    """Возвращает топ пользователей по очкам"""
    sorted_users = sorted(
        USERS.items(),
        key=lambda x: x[1].get('points', 0),
        reverse=True
    )
    return sorted_users[:limit]


def get_user_rank(user_id):
    """Возвращает позицию пользователя в рейтинге"""
    sorted_users = sorted(
        USERS.items(),
        key=lambda x: x[1].get('points', 0),
        reverse=True
    )
    for i, (uid, _) in enumerate(sorted_users, 1):
        if uid == str(user_id):
            return i
    return None


def get_stats_text():
    """Статистика бота"""
    days_running = (datetime.now() - BOT_STARTED).days + 1
    
    # Активные за последние 7 дней
    week_ago = datetime.now() - timedelta(days=7)
    active_week = 0
    for user_data in USERS.values():
        last_active = datetime.fromisoformat(user_data.get('last_active', datetime.min.isoformat()))
        if last_active >= week_ago:
            active_week += 1
    
    # Активные сегодня
    today = datetime.now().date()
    active_today = 0
    for user_data in USERS.values():
        last_active = datetime.fromisoformat(user_data.get('last_active', datetime.min.isoformat()))
        if last_active.date() == today:
            active_today += 1
    
    text = f"""📊 Բոտի ստատիստիկա

🚀 Աշխատում է՝ {days_running} օր

👥 Օգտատերեր՝
├ Ընդամենը՝ {TOTAL_USERS}
├ Ակտիվ այսօր՝ {active_today}
└ Ակտիվ այս շաբաթ՝ {active_week}

💬 Հաղորդագրություններ՝
└ Ընդամենը՝ {TOTAL_MESSAGES:,}

🆕 Նոր անդամներ խմբում՝ {NEW_MEMBERS}

⏰ Թարմացված՝ {datetime.now().strftime('%d.%m.%Y %H:%M')}"""
    
    return text


def get_top_text():
    """Топ активных пользователей"""
    top_users = get_top_users(10)
    
    if not top_users:
        return "❌ Տվյալներ դեռ չկան"
    
    text = "🏆 Ամենաակտիվ օգտատերերը\n\n"
    
    medals = ["🥇", "🥈", "🥉"]
    
    for i, (user_id, user_data) in enumerate(top_users, 1):
        medal = medals[i-1] if i <= 3 else f"{i}."
        name = user_data.get('name') or user_data.get('username') or f"User{user_id[:6]}"
        points = user_data.get('points', 0)
        messages = user_data.get('messages', 0)
        
        text += f"{medal} {name}\n"
        text += f"   💎 {points} միավոր | 💬 {messages} հաղորդագրություն\n\n"
    
    text += "\n💡 Ինչպես վաստակել միավորներ՝\n"
    text += "├ Յուրաքանչյուր 10 հաղորդագրություն = 1 միավոր\n"
    text += "└ Յուրաքանչյուր հրաման = 2 միավոր"
    
    return text


def get_profile_text(user_id):
    """Профиль пользователя"""
    user = get_user(user_id)
    rank = get_user_rank(user_id)
    
    name = user.get('name') or user.get('username') or "Օգտատեր"
    points = user.get('points', 0)
    messages = user.get('messages', 0)
    commands = user.get('commands', 0)
    
    joined_date = datetime.fromisoformat(user.get('joined', datetime.now().isoformat()))
    days_member = (datetime.now() - joined_date).days + 1
    
    text = f"""👤 {name}

🏆 Տեղը՝ #{rank if rank else '—'}
💎 Միավորներ՝ {points}

📊 Ակտիվություն՝
├ Հաղորդագրություններ՝ {messages}
├ Հրամաններ՝ {commands}
└ Խմբում՝ {days_member} օր

💡 Մինչև հաջորդ միավորը՝ {10 - (messages % 10)} հաղորդագրություն"""
    
    return text


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
/top - Ամենաակտիվները 🏆
/profile - Իմ պրոֆիլը 👤
/stats - Բոտի ստատիստիկա 📊
/buy - Գնել PS Plus բաժանորդագրություն
/support - Կապվել ադմինների հետ

Պարզապես գրիր հրամանը այստեղ՝ չատում! 👇"""


WELCOME_NEW_MEMBER = """👋 Բարի գալուստ, {name}! 

Ուրախ ենք տեսնել քեզ Հայ🇦🇲PS խմբում! 🎮

Այստեղ դու կգտնես՝
✅ Էժան PS Plus բաժանորդագրություններ
✅ Հուսալի խաղային հաշիվներ
✅ Օգտակար խորհուրդներ և նորություններ

🤖 Մեր բոտը օգտագործելու համար գրիր՝
/start - Սկսել բոտը
/top - Ամենաակտիվները 🏆
/profile - Իմ պրոֆիլը 👤
/buy - Գնել բաժանորդագրություն

📱 Միացիր նաև մեր Facebook խմբում՝
🔗 https://www.facebook.com/share/g/17foQWxCyZ/

Հաջող խաղ! 🎯"""


WELCOME = """🤖 Բարև, ես HayBot-ն եմ

Քո խելացի PlayStation օգնականը 🚀

Ես կարող եմ՝
✅ Օգնել բաժանորդագրությամբ
✅ Կապել ադմինների հետ
✅ Ցույց տալ ակտիվ օգտատերերին

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
        [
            InlineKeyboardButton(text="🏆 Ամենաակտիվները", callback_data="top"),
            InlineKeyboardButton(text="📊 Ստատիստիկա", callback_data="stats")
        ],
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


def refresh_menu(callback_data):
    """Меню с кнопкой обновления"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Թարմացնել", callback_data=callback_data)],
        *back_btn()
    ])


# ==============================
# 👋 ПРИВЕТСТВИЕ НОВЫХ УЧАСТНИКОВ
# ==============================

@dp.chat_member(ChatMemberUpdatedFilter(member_status_changed=MEMBER))
async def on_user_join(event: ChatMemberUpdated):
    user = event.new_chat_member.user
    name = user.first_name or user.username or "Ընկեր"
    
    track_new_member()
    get_user(user.id)  # Создаем профиль
    
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
        
        track_new_member()
        get_user(user.id)  # Создаем профиль
        
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
    track_command(m.from_user.id)
    track_message(m.from_user.id, m.from_user.username, m.from_user.first_name)
    await m.answer(WELCOME, reply_markup=main_menu())


@dp.message(Command("buy"))
async def buy(m: types.Message):
    track_command(m.from_user.id)
    track_message(m.from_user.id, m.from_user.username, m.from_user.first_name)
    await m.answer("Ընտրիր տարածաշրջանը 👇", reply_markup=country_menu())


@dp.message(Command("support"))
async def support(m: types.Message):
    track_command(m.from_user.id)
    track_message(m.from_user.id, m.from_user.username, m.from_user.first_name)
    await m.answer(f"🆘 {SUPPORT_MANAGER}", reply_markup=only_back())


@dp.message(Command("top"))
async def top_cmd(m: types.Message):
    track_command(m.from_user.id)
    track_message(m.from_user.id, m.from_user.username, m.from_user.first_name)
    await m.answer(get_top_text(), reply_markup=refresh_menu("top"))


@dp.message(Command("stats"))
async def stats_cmd(m: types.Message):
    track_command(m.from_user.id)
    track_message(m.from_user.id, m.from_user.username, m.from_user.first_name)
    await m.answer(get_stats_text(), reply_markup=refresh_menu("stats"))


@dp.message(Command("profile"))
async def profile_cmd(m: types.Message):
    track_command(m.from_user.id)
    track_message(m.from_user.id, m.from_user.username, m.from_user.first_name)
    await m.answer(get_profile_text(m.from_user.id), reply_markup=refresh_menu("profile"))


# ==============================
# 🔑 РЕАКЦИЯ НА КЛЮЧЕВЫЕ СЛОВА
# ==============================

@dp.message(F.text)
async def handle_keywords(message: types.Message):
    if message.chat.type == "private":
        track_message(message.from_user.id, message.from_user.username, message.from_user.first_name)
        return
        
    text = message.text.lower()
    
    if text.startswith('/'):
        return
    
    track_message(message.from_user.id, message.from_user.username, message.from_user.first_name)
    
    keywords_buy = ['գնել', 'купить', 'ps plus', 'подписка', 'բաժանորդ', 'subscription', 'padpiska', 'psplus', 'ukraina', 'ukrainakan', 'turqakan']
    keywords_bot = ['բոտ', 'бот', 'bot', 'հայբոտ', 'haybot']
    keywords_top = ['топ', 'տոպ', 'рейтинг', 'ամենաակտիվ']
    
    if any(word in text for word in keywords_top):
        await message.reply(
            "🏆 Ուզում ես տեսնել ամենաակտիվները?\n\n"
            "Օգտագործիր՝ /top",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🏆 Ցույց տալ", callback_data="top")]
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


@dp.callback_query(F.data == "top")
async def top_btn(c: types.CallbackQuery):
    await c.message.edit_text(get_top_text(), reply_markup=refresh_menu("top"))


@dp.callback_query(F.data == "stats")
async def stats_btn(c: types.CallbackQuery):
    await c.message.edit_text(get_stats_text(), reply_markup=refresh_menu("stats"))


@dp.callback_query(F.data == "profile")
async def profile_btn(c: types.CallbackQuery):
    await c.message.edit_text(get_profile_text(c.from_user.id), reply_markup=refresh_menu("profile"))


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
    global LAST_FB_POST, LAST_BOT_REMINDER

    while True:
        # Отправка приглашения в Facebook группу
        if datetime.now() - LAST_FB_POST >= timedelta(days=FB_POST_EVERY_DAYS):
            await bot.send_message(CHAT_ID, FB_GROUP_MESSAGE)
            LAST_FB_POST = datetime.now()
            save_state(LAST_FB_POST, LAST_BOT_REMINDER, TOTAL_USERS, TOTAL_MESSAGES, NEW_MEMBERS, BOT_STARTED)
            print("✅ Приглашение в Facebook группу отправлено")

        # Напоминание о боте
        if datetime.now() - LAST_BOT_REMINDER >= timedelta(days=BOT_REMINDER_EVERY_DAYS):
            await bot.send_message(CHAT_ID, BOT_REMINDER_MESSAGE)
            LAST_BOT_REMINDER = datetime.now()
            save_state(LAST_FB_POST, LAST_BOT_REMINDER, TOTAL_USERS, TOTAL_MESSAGES, NEW_MEMBERS, BOT_STARTED)
            print("✅ Напоминание о боте отправлено")

        await asyncio.sleep(CHECK_EVERY)


# ==============================
# ЗАПУСК
# ==============================

async def main():
    print("🤖 Бот запускается...")
    print("👋 Приветствие новых участников включено")
    print(f"📱 Facebook посты каждые {FB_POST_EVERY_DAYS} дня")
    print(f"💡 Напоминания о боте каждые {BOT_REMINDER_EVERY_DAYS} дня")
    print("🏆 Рейтинг активных пользователей включен")
    print("📊 Статистика бота включена")
    print(f"👥 Пользователей: {TOTAL_USERS}")
    print(f"💬 Сообщений: {TOTAL_MESSAGES}")
    
    asyncio.create_task(scheduler())
    
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=["message", "callback_query", "chat_member"])


if __name__ == "__main__":
    asyncio.run(main())
