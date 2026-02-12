import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

TOKEN = os.getenv("TOKEN")

bot = Bot(TOKEN)
dp = Dispatcher()

# ---------- ГЛАВНОЕ МЕНЮ ----------
main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="💰 Գներ"), KeyboardButton(text="🛒 Գնել")],
        [KeyboardButton(text="🆘 Աջակցություն")]
    ],
    resize_keyboard=True
)

# ---------- ВЫБОР СТРАНЫ ----------
country_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🇺🇦 Ուկրաինա"), KeyboardButton(text="🇹🇷 Թուրքիա")],
        [KeyboardButton(text="⬅️ Հետ")]
    ],
    resize_keyboard=True
)


# ---------- START ----------
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "🤖 Բարև, ես HayBot-ն եմ\n\nԸնտրիր գործողությունը 👇",
        reply_markup=main_kb
    )


# ---------- КНОПКА НАЗАД ----------
@dp.message(lambda m: m.text == "⬅️ Հետ")
async def back(message: types.Message):
    await message.answer("Վերադարձ գլխավոր մենյու 👇", reply_markup=main_kb)


# ---------- ГНЕРЫ ----------
@dp.message(lambda m: m.text == "💰 Գներ")
async def prices_menu(message: types.Message):
    await message.answer(
        "💰 Ընտրիր տարածաշրջանը՝ գները ստանալու համար 👇",
        reply_markup=country_kb
    )


# ---------- ПОКУПКА ----------
@dp.message(lambda m: m.text == "🛒 Գնել")
async def buy_menu(message: types.Message):
    await message.answer(
        "🛒 Ընտրիր տարածաշրջանը գնման համար 👇",
        reply_markup=country_kb
    )


# ---------- УКРАИНА ----------
@dp.message(lambda m: m.text == "🇺🇦 Ուկրաինա")
async def ukraine(message: types.Message):
    await message.answer(
        "🇺🇦 Ուկրաինական բաժանորդագրություններ\n\n"
        "Գրիր 👉 @BE4HOCT6 կամ @ash_avanesyan"
    )


# ---------- ТУРЦИЯ ----------
@dp.message(lambda m: m.text == "🇹🇷 Թուրքիա")
async def turkey(message: types.Message):
    await message.answer(
        "🇹🇷 Թուրքական բաժանորդագրություններ\n\n"
        "Գրիր 👉 @Hovo120193"
    )


# ---------- ПОДДЕРЖКА ----------
@dp.message(lambda m: m.text == "🆘 Աջակցություն")
async def support(message: types.Message):
    await message.answer(
        "🆘 Աջակցություն\n\nԳրիր 👉 @BE4HOCT6"
    )


# ---------- ЗАПУСК ----------
async def main():
    await dp.start_polling(bot)

asyncio.run(main())