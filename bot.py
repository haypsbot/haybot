import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

TOKEN = os.getenv("TOKEN")

bot = Bot(TOKEN)
dp = Dispatcher()

kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="💰 Գներ"), KeyboardButton(text="🛒 Գնել")],
        [KeyboardButton(text="🆘 Աջակցություն")]
    ],
    resize_keyboard=True
)

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "🤖 Բարև, ես HayBot-ն եմ\nԸնտրիր գործողությունը 👇",
        reply_markup=kb
    )

@dp.message(lambda m: m.text == "💰 Գներ")
async def prices(message: types.Message):
    await message.answer("🎮 PS Plus 1 ամիս — ****֏")

@dp.message(lambda m: m.text == "🛒 Գնել")
async def buy(message: types.Message):
    await message.answer("Գրիր 👉 @your_username")

@dp.message(lambda m: m.text == "🆘 Աջակցություն")
async def support(message: types.Message):
    await message.answer("Աջակցություն 👉 @your_username")

async def main():
    await dp.start_polling(bot)

asyncio.run(main())