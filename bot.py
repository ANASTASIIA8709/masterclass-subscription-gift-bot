"""
Бот проверки подписки на канал и выдачи подарка.

Логика:
1. Пользователь нажимает /start → видит кнопку "Подписаться на канал"
2. После подписки пишет /check или нажимает кнопку
3. Бот проверяет подписку через getChatMember
4. Если подписан → получает подарок (PDF-файл или текст)
5. Если не подписан → напоминание с кнопкой

Переменные окружения:
  BOT_TOKEN       - токен бота от @BotFather
  CHANNEL_ID      - ID или @username вашего канала (TODO: замените)
  GIFT_TEXT       - текст подарка, если нет файла
  GIFT_FILE_PATH  - путь к PDF-файлу подарка (если есть)
"""
import os
from aiogram import Bot, Dispatcher, F, Router
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart, Command
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
import asyncio

BOT_TOKEN = os.environ["BOT_TOKEN"]
# TODO: замените на @username или числовой ID вашего канала
CHANNEL_ID = os.environ.get("CHANNEL_ID", "@your_channel")
GIFT_TEXT = os.environ.get("GIFT_TEXT", "🎁 Ваш подарок!\n\nСпасибо за подписку. Вот ваш бонус: ...")
GIFT_FILE_PATH = os.environ.get("GIFT_FILE_PATH", "")

router = Router()

def subscribe_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Подписаться на канал", url=f"https://t.me/{CHANNEL_ID.lstrip('@')}")],
        [InlineKeyboardButton(text="✅ Я подписался(ась)", callback_data="check_sub")]
    ])

@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        f"👋 Привет, {message.from_user.first_name}!\n\n"
        f"Чтобы получить подарок - подпишись на наш канал {CHANNEL_ID}",
        reply_markup=subscribe_keyboard()
    )

@router.callback_query(F.data == "check_sub")
async def check_subscription(call: CallbackQuery):
    try:
        member = await call.bot.get_chat_member(CHANNEL_ID, call.from_user.id)
        if member.status in ("member", "administrator", "creator"):
            await call.message.edit_reply_markup()
            if GIFT_FILE_PATH and os.path.exists(GIFT_FILE_PATH):
                await call.message.answer_document(
                    document=open(GIFT_FILE_PATH, "rb"),
                    caption="🎁 Ваш подарок!"
                )
            else:
                await call.message.answer(GIFT_TEXT)
        else:
            await call.answer("Подписка не найдена. Подпишись и попробуй снова.", show_alert=True)
    except Exception:
        await call.answer("Не могу проверить подписку - убедись что подписался.", show_alert=True)

@router.message(Command("check"))
async def cmd_check(message: Message):
    cb_data = type("FakeCall", (), {"bot": message.bot, "from_user": message.from_user,
                                     "message": message, "answer": lambda *a, **k: None})()
    await check_subscription(cb_data)

async def main():
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    dp.include_router(router)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
