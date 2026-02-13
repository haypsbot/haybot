import asyncio
import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, ChatMemberUpdatedFilter, MEMBER
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ChatMemberUpdated
from aiogram.fsm.storage.memory import MemoryStorage


TOKEN = os.getenv("TOKEN")

# Используем MemoryStorage для FSM (быстрее чем дефолтный)
storage = MemoryStorage()
bot = Bot(TOKEN, parse_mode="HTML")
dp = Dispatcher(storage=storage)


# ==============================
# ⚙️ КОНФИГУРАЦИЯ
# ==============================

@dataclass
class Config:
    """Конфигурация бота"""
    CHAT_ID: int = -1003257278638
    CHECK_EVERY: int = 3600
    FB_POST_EVERY_DAYS: int = 2
    BOT_REMINDER_EVERY_DAYS: int = 4
    SAVE_INTERVAL: int = 60
    MAX_TOP_USERS: int = 10
    POINTS_PER_10_MESSAGES: int = 1
    POINTS_PER_COMMAND: int = 2
    
    STATE_FILE: str = "bot_state.json"
    USERS_FILE: str = "users.json"
    
    UK_MANAGERS: str = "@BE4HOCT6 @ash_avanesyan @VARDAN_XACHATRYAN"
    TR_MANAGERS: str = "@Hovo120193"
    SUPPORT_MANAGER: str = "@BE4HOCT6 @Hovo120193 @ash_avanesyan"


config = Config()


# ==============================
# 💾 ОПТИМИЗИРОВАННЫЙ DATA MANAGER
# ==============================

class FastDataManager:
    """Супер быстрый менеджер данных с кэшированием"""
    
    __slots__ = ('state', 'users', '_dirty', '_user_cache', '_top_cache', '_top_cache_time')
    
    def __init__(self):
        self.state: Dict = {}
        self.users: Dict = {}
        self._dirty: bool = False
        self._user_cache: Dict = {}  # Кэш для частых запросов
        self._top_cache: Optional[list] = None  # Кэш топа
        self._top_cache_time: datetime = datetime.min
        
        self._load_all()
    
    def _load_all(self):
        """Загружает все данные один раз"""
        self.state = self._load_json(config.STATE_FILE, {
            'last_fb_post': datetime.min.isoformat(),
            'last_bot_reminder': datetime.min.isoformat(),
            'total_messages': 0,
            'new_members': 0,
            'bot_started': datetime.now().isoformat()
        })
        
        # Парсим даты сразу
        for key in ['last_fb_post', 'last_bot_reminder', 'bot_started']:
            self.state[key] = datetime.fromisoformat(self.state[key])
        
        self.users = self._load_json(config.USERS_FILE, {})
    
    @staticmethod
    def _load_json(filename: str, default: dict) -> dict:
        """Быстрая загрузка JSON"""
        path = Path(filename)
        if not path.exists():
            return default
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return default
    
    def save_all(self):
        """Батчевое сохранение"""
        if not self._dirty:
            return
        
        try:
            # Сохраняем state
            state_to_save = {
                'last_fb_post': self.state['last_fb_post'].isoformat(),
                'last_bot_reminder': self.state['last_bot_reminder'].isoformat(),
                'total_messages': self.state['total_messages'],
                'new_members': self.state['new_members'],
                'bot_started': self.state['bot_started'].isoformat()
            }
            
            with open(config.STATE_FILE, 'w', encoding='utf-8') as f:
                json.dump(state_to_save, f, ensure_ascii=False, indent=2)
            
            # Сохраняем users
            with open(config.USERS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.users, f, ensure_ascii=False, indent=2)
            
            self._dirty = False
        except Exception as e:
            print(f"❌ Ошибка сохранения: {e}")
    
    def get_user(self, user_id: int) -> dict:
        """Получает пользователя с кэшированием"""
        uid = str(user_id)
        
        # Проверяем кэш
        if uid in self._user_cache:
            return self._user_cache[uid]
        
        # Создаем нового пользователя если нет
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
        
        # Кэшируем
        self._user_cache[uid] = self.users[uid]
        return self.users[uid]
    
    def track_message(self, user_id: int, username: str = "", first_name: str = ""):
        """Быстрое отслеживание сообщения"""
        user = self.get_user(user_id)
        user['messages'] += 1
        user['last_active'] = datetime.now().isoformat()
        
        # Обновляем имя только если пусто
        if username and not user['username']:
            user['username'] = username
        if first_name and not user['name']:
            user['name'] = first_name
        
        # Начисляем очки
        if user['messages'] % 10 == 0:
            user['points'] += config.POINTS_PER_10_MESSAGES
        
        self.state['total_messages'] += 1
        self._dirty = True
        self._invalidate_top_cache()
    
    def track_command(self, user_id: int):
        """Быстрое отслеживание команды"""
        user = self.get_user(user_id)
        user['commands'] += 1
        user['points'] += config.POINTS_PER_COMMAND
        self._dirty = True
        self._invalidate_top_cache()
    
    def track_new_member(self):
        """Отслеживание нового участника"""
        self.state['new_members'] += 1
        self._dirty = True
    
    def _invalidate_top_cache(self):
        """Инвалидирует кэш топа"""
        self._top_cache = None
    
    def get_top_users(self, limit: int = 10) -> list:
        """Получает топ с кэшированием"""
        now = datetime.now()
        
        # Кэш действителен 60 секунд
        if self._top_cache and (now - self._top_cache_time).seconds < 60:
            return self._top_cache[:limit]
        
        # Пересчитываем топ
        sorted_users = sorted(
            self.users.items(),
            key=lambda x: x[1]['points'],
            reverse=True
        )
        
        self._top_cache = sorted_users
        self._top_cache_time = now
        
        return sorted_users[:limit]
    
    def get_user_rank(self, user_id: int) -> Optional[int]:
        """Получает ранг пользователя"""
        top = self.get_top_users(len(self.users))
        uid = str(user_id)
        
        for i, (user_id_str, _) in enumerate(top, 1):
            if user_id_str == uid:
                return i
        return None
    
    @property
    def total_users(self) -> int:
        """Всего пользователей"""
        return len(self.users)
    
    def get_active_count(self, days: int = 7) -> int:
        """Активные за N дней с кэшированием"""
        threshold = datetime.now() - timedelta(days=days)
        
        count = 0
        for user_data in self.users.values():
            try:
                last_active = datetime.fromisoformat(user_data['last_active'])
                if last_active >= threshold:
                    count += 1
            except:
                pass
        
        return count


# Создаем глобальный инстанс
db = FastDataManager()


# ==============================
# 📊 ГЕНЕРАТОРЫ ТЕКСТА (ОПТИМИЗИРОВАННЫЕ)
# ==============================

def get_stats_text() -> str:
    """Генерирует статистику"""
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
    """Генерирует топ"""
    top = db.get_top_users(config.MAX_TOP_USERS)
    
    if not top:
        return "❌ Տվյալներ դեռ չկան"
    
    lines = ["🏆 Ամենաակտիվ օգտատերերը\n"]
    medals = ["🥇", "🥈", "🥉"]
    
    for i, (uid, u) in enumerate(top, 1):
        medal = medals[i-1] if i <= 3 else f"{i}."
        name = u.get('name') or u.get('username') or f"User{uid[:6]}"
        lines.append(f"{medal} {name}\n   💎 {u['points']} | 💬 {u['messages']}\n")
    
    lines.append("\n💡 Միավորներ՝\n├ 10 հաղորդագրություն = 1 միավոր\n└ 1 հրաման = 2 միավոր")
    
    return "".join(lines)


def get_profile_text(user_id: int) -> str:
    """Генерирует профиль"""
    user = db.get_user(user_id)
    rank = db.get_user_rank(user_id)
    
    name = user.get('name') or user.get('username') or "Օգտատեր"
    days = (datetime.now() - datetime.fromisoformat(user['joined'])).days + 1
    
    return f"""👤 {name}

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
📌 Խաղային հաշիվներ
📌 Օգտակար խորհուրդներ
📌 Ակտիվ community

👥 Արդեն ավելի քան 2000 հետևորդ!

🔗 https://www.facebook.com/share/g/17foQWxCyZ/

Մենք սպասում ենք քեզ! 🎯"""

REMINDER_MSG = """💡 Հիշեցում՝ 

Մեր խմբում աշխատում է HayBot! 🤖

/start - Սկսել բոտը
/top - Ամենաակտիվները 🏆
/profile - Իմ պրոֆիլը 👤
/stats - Բոտի ստատիստիկա 📊
/buy - Գնել PS Plus
/support - Կապվել ադմինների հետ

Պարզապես գրիր հրամանը այստեղ! 👇"""

WELCOME_MSG = """👋 Բարի գալուստ, {name}! 

Ուրախ ենք տեսնել քեզ Հայ🇦🇲PS խմբում! 🎮

✅ Էժան PS Plus բաժանորդագրություններ
✅ Հուսալի խաղային հաշիվներ
✅ Օգտակար խորհուրդներ

🤖 Հրամաններ՝
/start - Սկսել | /top - Տոպ 🏆
/profile - Պրոֆիլ | /buy - Գնել

📱 Facebook՝ https://www.facebook.com/share/g/17foQWxCyZ/

Հաջող խաղ! 🎯"""

START_MSG = """🤖 Բարև, ես HayBot-ն եմ

Քո խելացի PlayStation օգնականը 🚀

✅ Օգնել բաժանորդագրությամբ
✅ Կապել ադմինների հետ
✅ Ցույց տալ ակտիվ օգտատերերին

Ընտրիր ստորև 👇"""


# ==============================
# UI (ОПТИМИЗИРОВАНО)
# ==============================

# Кэшируем клавиатуры
_KEYBOARDS = {}

def get_keyboard(key: str) -> InlineKeyboardMarkup:
    """Получает закэшированную клавиатуру"""
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
    
    # Добавляем refresh клавиатуры
    for name in ['top', 'stats', 'profile']:
        keyboards[f'refresh_{name}'] = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Թարմացնել", callback_data=name)],
            [InlineKeyboardButton(text="⬅️ Հետ", callback_data="back")]
        ])
    
    _KEYBOARDS.update(keyboards)
    return _KEYBOARDS.get(key, keyboards['back'])


# ==============================
# 👋 ОБРАБОТЧИКИ (ОПТИМИЗИРОВАННЫЕ)
# ==============================

@dp.chat_member(ChatMemberUpdatedFilter(member_status_changed=MEMBER))
async def on_user_join(event: ChatMemberUpdated):
    """Приветствие нового участника"""
    user = event.new_chat_member.user
    name = user.first_name or user.username or "Ընկեր"
    
    db.track_new_member()
    db.get_user(user.id)
    
    try:
        await bot.send_message(event.chat.id, WELCOME_MSG.format(name=name))
    except:
        pass


@dp.message(F.new_chat_members)
async def on_new_members(m: types.Message):
    """Резервный обработчик новых участников"""
    for user in m.new_chat_members:
        name = user.first_name or user.username or "Ընկեր"
        db.track_new_member()
        db.get_user(user.id)
        
        try:
            await m.answer(WELCOME_MSG.format(name=name))
        except:
            pass


# ==============================
# КОМАНДЫ
# ==============================

@dp.message(Command("start"))
async def cmd_start(m: types.Message):
    db.track_command(m.from_user.id)
    db.track_message(m.from_user.id, m.from_user.username, m.from_user.first_name)
    await m.answer(START_MSG, reply_markup=get_keyboard('main'))


@dp.message(Command("buy"))
async def cmd_buy(m: types.Message):
    db.track_command(m.from_user.id)
    db.track_message(m.from_user.id, m.from_user.username, m.from_user.first_name)
    await m.answer("Ընտրիր տարածաշրջանը 👇", reply_markup=get_keyboard('country'))


@dp.message(Command("support"))
async def cmd_support(m: types.Message):
    db.track_command(m.from_user.id)
    db.track_message(m.from_user.id, m.from_user.username, m.from_user.first_name)
    await m.answer(f"🆘 {config.SUPPORT_MANAGER}", reply_markup=get_keyboard('back'))


@dp.message(Command("top"))
async def cmd_top(m: types.Message):
    db.track_command(m.from_user.id)
    db.track_message(m.from_user.id, m.from_user.username, m.from_user.first_name)
    await m.answer(get_top_text(), reply_markup=get_keyboard('refresh_top'))


@dp.message(Command("stats"))
async def cmd_stats(m: types.Message):
    db.track_command(m.from_user.id)
    db.track_message(m.from_user.id, m.from_user.username, m.from_user.first_name)
    await m.answer(get_stats_text(), reply_markup=get_keyboard('refresh_stats'))


@dp.message(Command("profile"))
async def cmd_profile(m: types.Message):
    db.track_command(m.from_user.id)
    db.track_message(m.from_user.id, m.from_user.username, m.from_user.first_name)
    await m.answer(get_profile_text(m.from_user.id), reply_markup=get_keyboard('refresh_profile'))


# ==============================
# КЛЮЧЕВЫЕ СЛОВА
# ==============================

# Предкомпилируем множества для быстрого поиска
KEYWORDS = {
    'buy': {'գնել', 'купить', 'ps plus', 'подписка', 'բաժանորդ', 'subscription', 'padpiska', 'psplus', 'ukraina', 'ukrainakan', 'turqakan'},
    'bot': {'բոտ', 'бот', 'bot', 'հայբոտ', 'haybot'},
    'top': {'топ', 'տոպ', 'рейтинг', 'ամենաակտիվ'}
}

@dp.message(F.text)
async def handle_text(m: types.Message):
    """Обработка текстовых сообщений"""
    if m.chat.type == "private":
        db.track_message(m.from_user.id, m.from_user.username, m.from_user.first_name)
        return
    
    text = m.text.lower()
    
    if text.startswith('/'):
        return
    
    db.track_message(m.from_user.id, m.from_user.username, m.from_user.first_name)
    
    try:
        # Используем множества для О(1) поиска
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
    except:
        pass


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
    """Автосохранение"""
    while True:
        await asyncio.sleep(config.SAVE_INTERVAL)
        db.save_all()


async def scheduler():
    """Планировщик"""
    while True:
        try:
            now = datetime.now()
            
            # Facebook
            if (now - db.state['last_fb_post']).days >= config.FB_POST_EVERY_DAYS:
                await bot.send_message(config.CHAT_ID, FB_MSG)
                db.state['last_fb_post'] = now
                db._dirty = True

            # Напоминание
            if (now - db.state['last_bot_reminder']).days >= config.BOT_REMINDER_EVERY_DAYS:
                await bot.send_message(config.CHAT_ID, REMINDER_MSG)
                db.state['last_bot_reminder'] = now
                db._dirty = True
        except:
            pass
        
        await asyncio.sleep(config.CHECK_EVERY)


# ==============================
# ЗАПУСК
# ==============================

async def main():
    print("🚀 Бот запускается...")
    print(f"👥 {db.total_users} | 💬 {db.state['total_messages']}")
    
    # Запускаем фоновые задачи
    asyncio.create_task(auto_save())
    asyncio.create_task(scheduler())
    
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot, allowed_updates=["message", "callback_query", "chat_member"])
    finally:
        db.save_all()
        print("✅ Данные сохранены")


if __name__ == "__main__":
    asyncio.run(main())
