import asyncio
import logging
from contextlib import suppress

from aiogram import Bot, Dispatcher, F
from aiogram.enums import ChatAction
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from config import BOT_TOKEN, MAX_CONTEXT_MESSAGES, OPENAI_MODEL
from context_manager import ContextManager
from api_client import APIClient

logging.basicConfig(
  format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
  level=logging.INFO,
)
logger = logging.getLogger(__name__)

context_manager = ContextManager()
api_client = APIClient()

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


def get_welcome_text(username: str) -> str:
  return (
    f"Привет, {username}! 👋\n\n"
    "Я AI-ассистент, который может помочь тебе с различными вопросами.\n"
    "Я помню контекст нашего разговора, так что можешь задавать уточняющие вопросы.\n\n"
    "Доступные команды:\n"
    "/start - начать диалог\n"
    "/help - показать справку\n"
    "/clear - очистить контекст диалога\n"
    "/reset - очистить контекст диалога\n"
    "/stats - показать статистику\n\n"
    "Просто напиши мне что-нибудь, и я отвечу! 😊"
  )


def get_username(message: Message) -> str:
  user = message.from_user
  if user.username:
    return user.username
  if user.first_name:
    return user.first_name
  return "друг"


async def send_typing(chat_id: int) -> None:
  """Показывает статус «печатает...» пока бот думает."""
  while True:
    await bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
    await asyncio.sleep(4)


@dp.message(CommandStart())
async def start(message: Message) -> None:
  await message.answer(get_welcome_text(get_username(message)))


@dp.message(Command("help"))
async def help_command(message: Message) -> None:
  await message.answer(get_welcome_text(get_username(message)))


@dp.message(Command("clear", "reset"))
async def clear_command(message: Message) -> None:
  user_id = message.from_user.id
  context_manager.clear(user_id)
  await message.answer("✅ Контекст диалога очищен.")
  logger.info("Контекст очищен для пользователя %s", user_id)


@dp.message(Command("stats"))
async def stats_command(message: Message) -> None:
  user_id = message.from_user.id
  messages_count = context_manager.get_messages_count(user_id)
  model_name = OPENAI_MODEL.replace("gpt", "GPT", 1)

  await message.answer(
    "📊 Статистика использования\n\n"
    f"👤 Ваш ID: {user_id}\n"
    f"💬 Сообщений в контексте: {messages_count}\n"
    f"🤖 Модель AI: {model_name}\n"
    f"📝 Максимум сообщений в контексте: {MAX_CONTEXT_MESSAGES}\n\n"
    "Используйте /clear для очистки контекста."
  )


@dp.message(F.text.func(lambda text: text and text.strip().lower() == "очистить контекст"))
async def clear_context_text(message: Message) -> None:
  user_id = message.from_user.id
  context_manager.clear(user_id)
  await message.answer("✅ Контекст диалога очищен.")
  logger.info("Контекст очищен для пользователя %s", user_id)


@dp.message(F.text)
async def handle_message(message: Message) -> None:
  user_id = message.from_user.id
  user_text = message.text.strip()

  typing_task = asyncio.create_task(send_typing(message.chat.id))

  try:
    messages = context_manager.get_messages(user_id) + [
      {"role": "user", "content": user_text}
    ]
    reply = await asyncio.to_thread(api_client.get_reply, messages)

    context_manager.add_user_message(user_id, user_text)
    context_manager.add_assistant_message(user_id, reply)

    await message.answer(reply)
    logger.info("Ответ отправлен пользователю %s", user_id)
  except Exception as error:
    logger.exception("Ошибка при обработке сообщения: %s", error)
    await message.answer("Произошла ошибка при генерации ответа. Попробуйте позже.")
  finally:
    typing_task.cancel()
    with suppress(asyncio.CancelledError):
      await typing_task


async def main() -> None:
  logger.info("Бот запущен")
  await dp.start_polling(bot)


if __name__ == "__main__":
  asyncio.run(main())
