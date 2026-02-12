import asyncio
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = os.getenv("TOKEN")

bot = Bot(TOKEN)
dp = Dispatcher()


#CHAT_ID = -100XXXXXXXXXX

UK_MANAGERS = "@BE4HOCT6 @ash_avanesyan"
TR_MANAGERS = "@Hovo120193"
SUPPORT_MANAGER = "@BE4HOCT6"


# =========================
# КНОПКИ INLINE
# =========================

main_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🎮 PS Plus բաժանորդագրություն", callback_data="ps")],
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
# START
# =========================

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "🤖 Բարև, ես HayBot-ն եմ\n\nԸնտրիր գործողությունը 👇",
        reply_markup=main_kb
    )


# =========================
# CALLBACKS
# =========================

@dp.callback_query(F.data == "ps")
async def ps(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "🎮 Ընտրիր տարածաշրջանը 👇",
        reply_markup=country_kb
    )


@dp.callback_query(F.data == "support")
async def support(callback: types.CallbackQuery):
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
    await callback.message.edit_text(
        "Գլխավոր մենյու 👇",
        reply_markup=main_kb
    )


# =========================
# ПРИВЕТ НОВЫМ
# =========================

@dp.message(F.new_chat_members)
async def welcome(message: types.Message):
    for user in message.new_chat_members:
        await message.answer(
            f"👋 Բարի գալուստ, {user.full_name}!\nՕգտագործիր բոտը 👇",
            reply_markup=main_kb
        )


# =========================
# АВТОПОСТ
# =========================

async def auto_post():
    while True:
        await bot.send_message(
            CHAT_ID,
            "🔥 PS Plus բաժանորդագրություններ հասանելի են\nՍեղմիր կոճակը 👇",
            reply_markup=main_kb
        )
        await asyncio.sleep(10800)


# =========================
# ЗАПУСК
# =========================

async def main():
    asyncio.create_task(auto_post())
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())