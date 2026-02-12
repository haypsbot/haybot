import asyncio
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = os.getenv("TOKEN")

bot = Bot(TOKEN)
dp = Dispatcher()


# =========================
# ⚙️ НАСТРОЙКИ
# =========================

CHAT_ID = -100XXXXXXXXXX  # <-- вставь id группы

UK_MANAGERS = "@BE4HOCT6 @ash_avanesyan"
TR_MANAGERS = "@Hovo120193"
SUPPORT_MANAGER = "@BE4HOCT6"


# =========================
# 🧠 ТЕКСТ ПРИВЕТСТВИЯ
# =========================

WELCOME_TEXT = """🤖 Բարև, ես HayBot-ն եմ

Քո խելացի PlayStation օգնականը 🚀

Ես կարող եմ՝
✅ Ցույց տալ գները
✅ Ակտիվացնել PS Plus
✅ Օգնել գնումների հարցում
✅ Կապել քեզ ադմինի հետ

Գրիր /start և ես պատրաստ եմ աշխատել ⚡
"""


# =========================
# 🔘 INLINE КНОПКИ
# =========================

main_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🎮 Գնել բաժանորդագրություն", callback_data="buy")],
    [InlineKeyboardButton(text="🆘 Աջակցություն", callback_data="support")]
])

country_kb = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text="🇺🇦 Ուկրաինա", callback_data="uk"),
        InlineKeyboardButton(text="🇹🇷 Թուրքիա", callback_data="tr")
    ],
    [InlineKeyboardButton(text="⬅️ Հետ", callback_data="back")]
])


# =========================
# 🚀 /start
# =========================

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(WELCOME_TEXT, reply_markup=main_kb)


# =========================
# 🛒 /buy
# =========================

@dp.message(Command("buy"))
async def buy_command(message: types.Message):
    await message.answer(
        "🎮 Ընտրիր տարածաշրջանը 👇",
        reply_markup=country_kb
    )


# =========================
# 🆘 /support
# =========================

@dp.message(Command("support"))
async def support_command(message: types.Message):
    await message.answer(
        f"🆘 Աջակցություն\n\nԳրիր 👉 {SUPPORT_MANAGER}"
    )


# =========================
# 🔘 CALLBACK КНОПКИ
# =========================

@dp.callback_query(F.data == "buy")
async def buy_btn(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "🎮 Ընտրիր տարածաշրջանը 👇",
        reply_markup=country_kb
    )


@dp.callback_query(F.data == "support")
async def support_btn(callback: types.CallbackQuery):
    await callback.message.edit_text(
        f"🆘 Աջակցություն\n\nԳրիր 👉 {SUPPORT_MANAGER}",
        reply_markup=main_kb
    )


@dp.callback_query(F.data == "uk")
async def uk(callback: types.CallbackQuery):
    await callback.message.edit_text(
        f"🇺🇦 Ուկրաինական PS Plus\n\nԳրիր 👉 {UK_MANAGERS}",
        reply_markup=main_kb
    )


@dp.callback_query(F.data == "tr")
async def tr(callback: types.CallbackQuery):
    await callback.message.edit_text(
        f"🇹🇷 Թուրքական PS Plus\n\nԳրիր 👉 {TR_MANAGERS}",
        reply_markup=main_kb
    )


@dp.callback_query(F.data == "back")
async def back(callback: types.CallbackQuery):
    await callback.message.edit_text(WELCOME_TEXT, reply_markup=main_kb)


# =========================
# 👋 ПРИВЕТ НОВЫМ В ГРУППЕ
# =========================

@dp.message(F.new_chat_members)
async def welcome_new_users(message: types.Message):
    for user in message.new_chat_members:
        await message.answer(
            f"👋 Բարի գալուստ, {user.full_name}!\n\n{WELCOME_TEXT}",
            reply_markup=main_kb
        )


# =========================
# 📢 АВТОПОСТ
# =========================

async def auto_post():
    while True:
        await bot.send_message(
            CHAT_ID,
            "🔥 PS Plus բաժանորդագրություններ հասանելի են\nՍեղմիր ստորև 👇",
            reply_markup=main_kb
        )
        await asyncio.sleep(10800)  # 3 часа


# =========================
# ▶️ ЗАПУСК
# =========================

async def main():
    asyncio.create_task(auto_post())
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())