import asyncio
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

TOKEN = os.getenv("TOKEN")

bot = Bot(TOKEN)
dp = Dispatcher()


# =========================
# ⚙️ НАСТРОЙКИ (измени только это)
# =========================

#CHAT_ID = -100XXXXXXXXXX  # <-- ВСТАВЬ ID своей группы

UK_MANAGERS = "@BE4HOCT6 @ash_avanesyan"
TR_MANAGERS = "@Hovo120193"
SUPPORT_MANAGER = "@BE4HOCT6"


# =========================
# 📋 КЛАВИАТУРЫ
# =========================

main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="💳 Գնել / Գներ")],
        [KeyboardButton(text="🆘 Աջակցություն")]
    ],
    resize_keyboard=True
)

country_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🇺🇦 Ուկրաինա"), KeyboardButton(text="🇹🇷 Թուրքիա")],
        [KeyboardButton(text="⬅️ Հետ")]
    ],
    resize_keyboard=True
)


# =========================
# 🚀 START
# =========================

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "🤖 Բարև, ես HayBot-ն եմ\n\nԸնտրիր գործողությունը 👇",
        reply_markup=main_kb
    )


# =========================
# ⬅️ НАЗАД
# =========================

@dp.message(lambda m: m.text == "⬅️ Հետ")
async def back(message: types.Message):
    await message.answer("Վերադարձ գլխավոր մենյու 👇", reply_markup=main_kb)


# =========================
# 💳 ПОКУПКА/ЦЕНЫ (объединено)
# =========================

@dp.message(lambda m: m.text == "💳 Գնել / Գներ")
async def buy_prices(message: types.Message):
    await message.answer(
        "💳 Ընտրիր տարածաշրջանը 👇",
        reply_markup=country_kb
    )


# =========================
# 🇺🇦 УКРАИНА
# =========================

@dp.message(lambda m: m.text == "🇺🇦 Ուկրաինա")
async def ukraine(message: types.Message):
    await message.answer(
        f"🇺🇦 Ուկրաինական PS Plus\n\n"
        f"Գրիր 👉 {UK_MANAGERS}"
    )


# =========================
# 🇹🇷 ТУРЦИЯ
# =========================

@dp.message(lambda m: m.text == "🇹🇷 Թուրքիա")
async def turkey(message: types.Message):
    await message.answer(
        f"🇹🇷 Թուրքական PS Plus\n\n"
        f"Գրիր 👉 {TR_MANAGERS}"
    )


# =========================
# 🆘 ПОДДЕРЖКА
# =========================

@dp.message(lambda m: m.text == "🆘 Աջակցություն")
async def support(message: types.Message):
    await message.answer(
        f"🆘 Աջակցություն\n\nԳրիր 👉 {SUPPORT_MANAGER}"
    )


# =========================
# 👋 ПРИВЕТСТВИЕ В ГРУППЕ
# =========================

@dp.message(F.new_chat_members)
async def welcome(message: types.Message):
    for user in message.new_chat_members:
        await message.answer(
            f"👋 Բարի գալուստ, {user.full_name}!\n\n"
            "🤖 HayBot-ը կօգնի քեզ գնել PS Plus\n"
            "Գրիր /start կամ օգտագործիր մենյուն 🎮"
        )


# =========================
# 📢 АВТОПОСТ КАЖДЫЕ 3 ЧАСА
# =========================

async def auto_post():
    while True:
        await bot.send_message(
            CHAT_ID,
            "🔥 PS Plus բաժանորդագրություններ հասանելի են\n\n"
            f"🇺🇦 Ուկրաինա → {UK_MANAGERS}\n"
            f"🇹🇷 Թուրքիա → {TR_MANAGERS}\n\n"
            "Գրիր /start 🤖"
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