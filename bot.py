import asyncio
import os
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional
from functools import wraps
from time import time

from aiogram import Bot, Dispatcher, types, F, BaseMiddleware
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, TelegramObject
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from dotenv import load_dotenv

# ==============================
# 📝 ЛОГИРОВАНИЕ
# ==============================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==============================
# 🔑 ЗАГРУЗКА ТОКЕНА
# ==============================

load_dotenv()
TOKEN = os.getenv("TOKEN")

if not TOKEN:
    logger.error("❌ Токен не найден! Создай файл .env с TOKEN=твой_токен")
    exit()

storage = MemoryStorage()
bot = Bot(TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=storage)


# ==============================
# ⚙️ КОНФИГУРАЦИЯ
# ==============================

class Config:
    CHAT_ID: int = -1003257278638
    CHECK_EVERY: int = 3600
    FB_POST_EVERY_DAYS: int = 2
    BOT_REMINDER_EVERY_DAYS: int = 4
    SAVE_INTERVAL: int = 60
    MAX_TOP_USERS: int = 10
    POINTS_PER_10_MESSAGES: int = 1
    POINTS_PER_COMMAND: int = 2
    CACHE_TTL: int = 60
    THROTTLE_TIME: int = 3
    
    STATE_FILE: str = "bot_state.json"
    USERS_FILE: str = "users.json"
    
    UK_MANAGERS: str = "@BE4HOCT6 @ash_avanesyan @VARDAN_XACHATRYAN"
    TR_MANAGERS: str = "@Hovo120193"
    SUPPORT_MANAGER: str = "@BE4HOCT6 @Hovo120193 @ash_avanesyan @VARDAN_XACHATRYAN"


config = Config()


# ==============================
# 🛡️ АНТИФЛУД ДЕКОРАТОР
# ==============================

def throttle(limit: int = config.THROTTLE_TIME):
    """Антифлуд декоратор"""
    def decorator(func):
        last_call = {}
        
        @wraps(func)
        async def wrapper(message: types.Message, *args, **kwargs):
            user_id = message.from_user.id
            now = time()
            
            if user_id in last_call:
                if now - last_call[user_id] < limit:
                    logger.debug(f"Throttled user {user_id}")
                    return
            
            last_call[user_id] = now
            return await func(message, *args, **kwargs)
        
        return wrapper
    return decorator


# ==============================
# 🎯 MIDDLEWARE ДЛЯ АВТОТРЕКИНГА
# ==============================

class TrackingMiddleware(BaseMiddleware):
    """Middleware для автоматического трекинга сообщений"""
    
    async def __call__(
        self,
        handler,
        event: TelegramObject,
        data: dict
    ):
        if isinstance(event, types.Message):
            if event.chat.type in ["group", "supergroup"]:
                if event.text and not event.text.startswith('/'):
                    db.track_message(
                        event.from_user.id,
                        event.from_user.username or "",
                        event.from_user.first_name or ""
                    )
        
        return await handler(event, data)


# ==============================
# 💾 DATA MANAGER
# ==============================

class FastDataManager:
    """Менеджер данных с кэшированием"""
    
    __slots__ = ('state', 'users', '_dirty', '_user_cache', '_top_cache', 
                 '_top_cache_time', '_active_cache', '_active_cache_time', '_lock')
    
    def __init__(self):
        self.state: Dict = {}
        self.users: Dict = {}
        self._dirty: bool = False
        self._user_cache: Dict = {}
        self._top_cache: Optional[list] = None
        self._top_cache_time: datetime = datetime.min
        self._active_cache: Dict = {}
        self._active_cache_time: datetime = datetime.min
        self._lock = asyncio.Lock()
        
        self._load_all()
    
    def _load_all(self):
        """Загружает все данные"""
        state_data = self._load_json(config.STATE_FILE, {})
        
        now_iso = datetime.now().isoformat()
        
        self.state = {
            'last_fb_post': state_data.get('last_fb_post', now_iso),
            'last_bot_reminder': state_data.get('last_bot_reminder', now_iso),
            'total_messages': state_data.get('total_messages', 0),
            'new_members': state_data.get('new_members', 0),
            'bot_started': state_data.get('bot_started', now_iso)
        }
        
        for key in ['last_fb_post', 'last_bot_reminder', 'bot_started']:
            self.state[key] = datetime.fromisoformat(self.state[key])
        
        self.users = self._load_json(config.USERS_FILE, {})
        
        logger.info(f"📅 Последний FB пост: {self.state['last_fb_post'].strftime('%d.%m.%Y %H:%M')}")
        logger.info(f"📅 Последнее напоминание: {self.state['last_bot_reminder'].strftime('%d.%m.%Y %H:%M')}")
    
    @staticmethod
    def _load_json(filename: str, default: dict) -> dict:
        path = Path(filename)
        if not path.exists():
            return default
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Ошибка загрузки {filename}: {e}")
            return default
    
    async def save_all(self):
        """Безопасное сохранение с Lock"""
        async with self._lock:
            if not self._dirty:
                return
            
            try:
                state_to_save = {
                    'last_fb_post': self.state['last_fb_post'].isoformat(),
                    'last_bot_reminder': self.state['last_bot_reminder'].isoformat(),
                    'total_messages': self.state['total_messages'],
                    'new_members': self.state['new_members'],
                    'bot_started': self.state['bot_started'].isoformat()
                }
                
                with open(config.STATE_FILE, 'w', encoding='utf-8') as f:
                    json.dump(state_to_save, f, ensure_ascii=False, indent=2)
                
                with open(config.USERS_FILE, 'w', encoding='utf-8') as f:
                    json.dump(self.users, f, ensure_ascii=False, indent=2)
                
                self._dirty = False
                logger.debug("💾 Данные сохранены")
            except Exception as e:
                logger.error(f"Ошибка сохранения: {e}")
    
    def get_user(self, user_id: int) -> dict:
        uid = str(user_id)
        
        if uid in self._user_cache:
            return self._user_cache[uid]
        
        if uid not in self.users:
            self.users[uid] = {
                'name': '',
                'username': '',
                'points': 0,
                'messages': 0,
                'commands': 0,
                'joined': datetime.now().isoformat(),
                'last_active': datetime.now().isoformat()
            }
            self._dirty = True
        
        self._user_cache[uid] = self.users[uid]
        return self.users[uid]
    
    def track_message(self, user_id: int, username: str = "", first_name: str = ""):
        """Отслеживание обычного сообщения"""
        user = self.get_user(user_id)
        user['messages'] += 1
        user['last_active'] = datetime.now().isoformat()
        
        if username and not user['username']:
            user['username'] = username
        if first_name and not user['name']:
            user['name'] = first_name
        
        if user['messages'] % 10 == 0:
            user['points'] += config.POINTS_PER_10_MESSAGES
        
        self.state['total_messages'] += 1
        self._dirty = True
        self._invalidate_caches()
    
    def track_command(self, user_id: int):
        """Отслеживание команды"""
        user = self.get_user(user_id)
        user['commands'] += 1
        user['points'] += config.POINTS_PER_COMMAND
        user['last_active'] = datetime.now().isoformat()
        self._dirty = True
        self._invalidate_caches()
    
    def track_new_member(self):
        self.state['new_members'] += 1
        self._dirty = True
    
    def _invalidate_caches(self):
        """Инвалидирует кэши"""
        self._top_cache = None
        self._active_cache = {}
    
    def get_top_users(self, limit: int = 10) -> list:
        now = datetime.now()
        
        if self._top_cache and (now - self._top_cache_time).seconds < config.CACHE_TTL:
            return self._top_cache[:limit]
        
        sorted_users = sorted(
            self.users.items(),
            key=lambda x: x[1]['points'],
            reverse=True
        )
        
        self._top_cache = sorted_users
        self._top_cache_time = now
        
        return sorted_users[:limit]
    
    def get_user_rank(self, user_id: int) -> Optional[int]:
        top = self.get_top_users(len(self.users))
        uid = str(user_id)
        
        for i, (user_id_str, _) in enumerate(top, 1):
            if user_id_str == uid:
                return i
        return None
    
    @property
    def total_users(self) -> int:
        return len(self.users)
    
    def get_active_count(self, days: int = 7) -> int:
        """Активные за N дней с кэшированием"""
        now = datetime.now()
        cache_key = f"active_{days}"
        
        if cache_key in self._active_cache:
            if (now - self._active_cache_time).seconds < config.CACHE_TTL:
                return self._active_cache[cache_key]
        
        threshold = now - timedelta(days=days)
        count = 0
        
        for user_data in self.users.values():
            try:
                last_active = datetime.fromisoformat(user_data['last_active'])
                if last_active >= threshold:
                    count += 1
            except:
                pass
        
        self._active_cache[cache_key] = count
        self._active_cache_time = now
        
        return count


db = FastDataManager()


# ==============================
# 📊 ГЕНЕРАТОРЫ ТЕКСТА
# ==============================

def get_stats_text() -> str:
    days = (datetime.now() - db.state['bot_started']).days + 1
    
    return f"""📊 Բոտի ստատիստիկա

🚀 Աշխատում է՝ {days} օր

👥 Օգտատերեր՝
├ Ընդամենը՝ {db.total_users}
├ Ակտիվ այսօր՝ {db.get_active_count(0)}
└ Ակտիվ այս շաբաթ՝ {db.get_active_count(7)}

💬 Հաղորդագրություններ՝ {db.state['total_messages']:,}
🆕 Նոր անդամներ՝ {db.state['new_members']}

⏰ {datetime.now().strftime('%d.%m %H:%M')}"""


def get_top_text() -> str:
    """Генерирует топ с кликабельными именами"""
    top = db.get_top_users(config.MAX_TOP_USERS)
    
    if not top:
        return "❌ Տվյալներ դեռ չկան"
    
    lines = ["🏆 Ամենաակտիվ օգտատերերը\n\n"]
    medals = ["🥇", "🥈", "🥉"]
    
    for i, (uid, u) in enumerate(top, 1):
        medal = medals[i-1] if i <= 3 else f"{i}."
        
        # Получаем имя
        name = u.get('name') or u.get('username')
        
        # Пропускаем пользователей без имени
        if not name:
            continue
        
        # Делаем кликабельным
        if u.get('username'):
            clickable_name = f"<a href='tg://user?id={uid}'>@{u['username']}</a>"
        else:
            clickable_name = f"<a href='tg://user?id={uid}'>{name}</a>"
        
        lines.append(f"{medal} {clickable_name}\n   💎 {u['points']} | 💬 {u['messages']}\n\n")
    
    lines.append("💡 Միավորներ՝\n├ 10 հաղորդագրություն = 1 միավոր\n└ 1 հրաման = 2 միավոր")
    
    return "".join(lines)


def get_profile_text(user_id: int) -> str:
    """Генерирует профиль с кликабельным именем"""
    user = db.get_user(user_id)
    rank = db.get_user_rank(user_id)
    
    # Получаем имя
    name = user.get('name') or user.get('username') or "Օգտատեր"
    
    # Делаем кликабельным
    if user.get('username'):
        clickable_name = f"<a href='tg://user?id={user_id}'>@{user['username']}</a>"
    else:
        clickable_name = f"<a href='tg://user?id={user_id}'>{name}</a>"
    
    days = (datetime.now() - datetime.fromisoformat(user['joined'])).days + 1
    
    return f"""👤 {clickable_name}

🏆 Տեղը՝ #{rank or '—'}
💎 Միավորներ՝ {user['points']}

📊 Ակտիվություն՝
├ Հաղորդագրություններ՝ {user['messages']}
├ Հրամաններ՝ {user['commands']}
└ Խմբում՝ {days} օր

💡 Մինչև հաջորդ միավորը՝ {10 - (user['messages'] % 10)} հաղորդագրություն"""


# ==============================
# 📱 КОНСТАНТЫ
# ==============================

FB_MSG = """🎮 Միացիր մեր Հայ🇦🇲PS խմբին Facebook-ում! 🔥

📌 PS Plus բաժանորդագրություններ
📌 Ուկրաինական և թուրքական րեգիոններով account-ներ
📌 Օգտակար խորհուրդներ
📌 Ակտիվ community

👥 Արդեն ավելի քան 2000 հետևորդ!

🔗 https://www.facebook.com/share/g/17foQWxCyZ/

Մենք սպասում ենք քեզ! 🎯"""

REMINDER_MSG = """💡 Հիշեցում՝ 

Մեր խմբում աշխատում է Հայ🇦🇲PS Bot! 🤖

/start - Սկսել բոտը
/top - Ամենաակտիվները 🏆
/profile - Իմ պրոֆիլը 👤
/stats - Բոտի ստատիստիկա 📊
/buy - Գնել PS Plus
/support - Կապվել ադմինների հետ

Պարզապես գրիր հրամանը այստեղ! 👇"""

WELCOME_MSG = """👋 Բարի գալուստ, {name}! 

Ուրախ ենք տեսնել քեզ Հայ🇦🇲PS խմբում! 🎮

✅ PS Plus բաժանորդագրություններ
✅ Ուկրաինական և թուրքական րեգիոններով account-ներ
✅ Օգտակար խորհուրդներ

🤖 Հրամաններ՝
/start - Սկսել | /top - Տոպ 🏆
/profile - Պրոֆիլ | /buy - Գնել

📱 Facebook՝ https://www.facebook.com/share/g/17foQWxCyZ/

Հաջող խաղ! 🎯"""

START_MSG = """🤖 Բարև, ես Հայ🇦🇲PS Bot-ն եմ։

Քո վստահելի PlayStation օգնականը 🚀

Ես այստեղ եմ, որպեսզի օգնեմ քեզ՝
🎮 Գնել PS Plus բաժանորդագրություն
👥 Արագ կապ հաստատել ադմինների հետ
🏆 Տեսնել ամենաակտիվ օգտատերերին

Ընտրիր ստորև և սկսենք 👇"""


# ==============================
# UI
# ==============================

_KEYBOARDS = {}

def get_keyboard(key: str) -> InlineKeyboardMarkup:
    if key in _KEYBOARDS:
        return _KEYBOARDS[key]
    
    keyboards = {
        'main': InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎮 Գնել բաժանորդագրություն", callback_data="buy")],
            [
                InlineKeyboardButton(text="🏆 Ամենաակտիվները", callback_data="top"),
                InlineKeyboardButton(text="📊 Ստատիստիկա", callback_data="stats")
            ],
            [InlineKeyboardButton(text="🆘 Աջակցություն", callback_data="support")]
        ]),
        'country': InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🇺🇦 Ուկրաինա", callback_data="uk"),
                InlineKeyboardButton(text="🇹🇷 Թուրքիա", callback_data="tr")
            ],
            [InlineKeyboardButton(text="⬅️ Հետ", callback_data="back")]
        ]),
        'back': InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Հետ", callback_data="back")]
        ])
    }
    
    for name in ['top', 'stats', 'profile']:
        keyboards[f'refresh_{name}'] = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Թարմացնել", callback_data=name)],
            [InlineKeyboardButton(text="⬅️ Հետ", callback_data="back")]
        ])
    
    _KEYBOARDS.update(keyboards)
    return _KEYBOARDS.get(key, keyboards['back'])


# ==============================
# 👋 ОБРАБОТЧИКИ
# ==============================

@dp.message(F.new_chat_members)
async def on_new_members(m: types.Message):
    for user in m.new_chat_members:
        name = user.first_name or user.username or "Ընկեր"
        db.track_new_member()
        db.get_user(user.id)
        
        try:
            await m.answer(WELCOME_MSG.format(name=name))
            logger.info(f"✅ Приветствие: {name}")
        except Exception as e:
            logger.error(f"Ошибка приветствия: {e}")


# ==============================
# КОМАНДЫ
# ==============================

@dp.message(Command("start"))
async def cmd_start(m: types.Message):
    db.track_command(m.from_user.id)
    await m.answer(START_MSG, reply_markup=get_keyboard('main'))


@dp.message(Command("buy"))
async def cmd_buy(m: types.Message):
    db.track_command(m.from_user.id)
    await m.answer("Ընտրիր տարածաշրջանը 👇", reply_markup=get_keyboard('country'))


@dp.message(Command("support"))
async def cmd_support(m: types.Message):
    db.track_command(m.from_user.id)
    await m.answer(f"🆘 {config.SUPPORT_MANAGER}", reply_markup=get_keyboard('back'))


@dp.message(Command("top"))
async def cmd_top(m: types.Message):
    db.track_command(m.from_user.id)
    await m.answer(get_top_text(), reply_markup=get_keyboard('refresh_top'))


@dp.message(Command("stats"))
async def cmd_stats(m: types.Message):
    db.track_command(m.from_user.id)
    await m.answer(get_stats_text(), reply_markup=get_keyboard('refresh_stats'))


@dp.message(Command("profile"))
async def cmd_profile(m: types.Message):
    db.track_command(m.from_user.id)
    await m.answer(get_profile_text(m.from_user.id), reply_markup=get_keyboard('refresh_profile'))


# ==============================
# КЛЮЧЕВЫЕ СЛОВА
# ==============================

KEYWORDS = {
    'buy': {'գնել', 'купить', 'ps plus', 'подписка', 'բաժանորդ', 'subscription', 'padpiska', 'psplus', 'ukraina', 'ukrainakan', 'turqakan'},
    'bot': {'բոտ', 'бот', 'bot', 'հայբոտ', 'haybot'},
    'top': {'топ', 'տոպ', 'рейтинг', 'ամենաակտիվ'}
}

@dp.message(F.text)
@throttle(3)
async def handle_text(m: types.Message):
    if m.chat.type == "private":
        return
    
    text = m.text.lower()
    
    if text.startswith('/'):
        return
    
    try:
        text_set = set(text.split())
        
        if KEYWORDS['top'] & text_set:
            await m.reply(
                "🏆 Ուզում ես տեսնել ամենաակտիվները?\n\nՕգտագործիր՝ /top",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🏆 Ցույց տալ", callback_data="top")]
                ])
            )
        elif KEYWORDS['buy'] & text_set:
            await m.reply(
                "🎮 Ուզում ես գնել PS Plus?\n\nՕգտագործիր՝ /buy",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🎮 Գնել բաժանորդագրություն", callback_data="buy")]
                ])
            )
        elif KEYWORDS['bot'] & text_set:
            await m.reply("👋 Այո, ես այստեղ եմ!\n\nՕգտագործիր՝ /start")
    except Exception as e:
        logger.error(f"Ошибка обработки ключевых слов: {e}")


# ==============================
# CALLBACKS
# ==============================

@dp.callback_query(F.data == "back")
async def cb_back(c: types.CallbackQuery):
    await c.message.edit_text(START_MSG, reply_markup=get_keyboard('main'))


@dp.callback_query(F.data == "buy")
async def cb_buy(c: types.CallbackQuery):
    await c.message.edit_text("Ընտրիր տարածաշրջանը 👇", reply_markup=get_keyboard('country'))


@dp.callback_query(F.data == "support")
async def cb_support(c: types.CallbackQuery):
    await c.message.edit_text(f"🆘 {config.SUPPORT_MANAGER}", reply_markup=get_keyboard('back'))


@dp.callback_query(F.data == "top")
async def cb_top(c: types.CallbackQuery):
    await c.message.edit_text(get_top_text(), reply_markup=get_keyboard('refresh_top'))


@dp.callback_query(F.data == "stats")
async def cb_stats(c: types.CallbackQuery):
    await c.message.edit_text(get_stats_text(), reply_markup=get_keyboard('refresh_stats'))


@dp.callback_query(F.data == "profile")
async def cb_profile(c: types.CallbackQuery):
    await c.message.edit_text(get_profile_text(c.from_user.id), reply_markup=get_keyboard('refresh_profile'))


@dp.callback_query(F.data == "uk")
async def cb_uk(c: types.CallbackQuery):
    await c.message.edit_text(f"🇺🇦 Գրիր 👉 {config.UK_MANAGERS}", reply_markup=get_keyboard('back'))


@dp.callback_query(F.data == "tr")
async def cb_tr(c: types.CallbackQuery):
    await c.message.edit_text(f"🇹🇷 Գրիր 👉 {config.TR_MANAGERS}", reply_markup=get_keyboard('back'))


# ==============================
# ФОНОВЫЕ ЗАДАЧИ
# ==============================

async def auto_save():
    """Автосохранение каждые 60 секунд"""
    while True:
        await asyncio.sleep(config.SAVE_INTERVAL)
        await db.save_all()


async def scheduler():
    """Планировщик с защитой от спама"""
    await asyncio.sleep(60)
    logger.info("✅ Планировщик запущен")
    
    while True:
        try:
            now = datetime.now()
            
            days_since_fb = (now - db.state['last_fb_post']).days
            if days_since_fb >= config.FB_POST_EVERY_DAYS:
                logger.info(f"📱 Отправляю FB пост (прошло {days_since_fb} дней)")
                await bot.send_message(config.CHAT_ID, FB_MSG)
                
                async with db._lock:
                    db.state['last_fb_post'] = now
                    db._dirty = True

            days_since_reminder = (now - db.state['last_bot_reminder']).days
            if days_since_reminder >= config.BOT_REMINDER_EVERY_DAYS:
                logger.info(f"💡 Отправляю напоминание (прошло {days_since_reminder} дней)")
                await bot.send_message(config.CHAT_ID, REMINDER_MSG)
                
                async with db._lock:
                    db.state['last_bot_reminder'] = now
                    db._dirty = True
                
        except Exception as e:
            logger.error(f"Ошибка scheduler: {e}")
        
        await asyncio.sleep(config.CHECK_EVERY)


# ==============================
# ЗАПУСК
# ==============================

async def main():
    logger.info("🚀 Бот запускается...")
    logger.info(f"👥 {db.total_users} | 💬 {db.state['total_messages']}")
    
    dp.message.middleware(TrackingMiddleware())
    
    asyncio.create_task(auto_save())
    asyncio.create_task(scheduler())
    
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot, allowed_updates=["message", "callback_query", "chat_member"])
    finally:
        await db.save_all()
        logger.info("✅ Данные сохранены")


if __name__ == "__main__":
    asyncio.run(main())
