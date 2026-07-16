import asyncio
import logging
import re
from contextlib import suppress

from aiogram import Bot, Dispatcher, F
from aiogram.enums import ChatAction
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.types import Message

from config import (
  API_PROVIDER,
  BOT_TOKEN,
  MAX_CONTEXT_MESSAGES,
  OPENAI_MODEL,
  PROMPT_TEMPLATES,
  WELCOME_TEXT,
  build_system_prompt,
  get_prompt_by_id,
)
from context_manager import ContextManager

logging.basicConfig(
  format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
  level=logging.INFO,
)
logger = logging.getLogger(__name__)


def strip_markdown(text: str) -> str:
  """Убирает Markdown-разметку из ответа для обычного текста в Telegram."""
  text = re.sub(r"```[\s\S]*?```", lambda m: m.group(0).strip("`").strip(), text)
  text = re.sub(r"`([^`]+)`", r"\1", text)
  text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
  text = re.sub(r"__(.+?)__", r"\1", text)
  text = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"\1", text)
  text = re.sub(r"(?<!_)_(?!_)(.+?)(?<!_)_(?!_)", r"\1", text)
  text = re.sub(r"~~(.+?)~~", r"\1", text)
  text = re.sub(r"^#{1,6}\s*", "", text, flags=re.MULTILINE)
  text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
  return text.strip()


def create_api_client():
  if API_PROVIDER == "proxyapi":
    from proxyapi_client import ProxyAPIClient

    return ProxyAPIClient()
  if API_PROVIDER == "genapi":
    from genapi_client import GenAPIClient

    return GenAPIClient()
  from openai_direct import OpenAIDirectClient

  return OpenAIDirectClient()


context_manager = ContextManager()
api_client = create_api_client()
active_prompts: dict[int, int] = {}

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


def get_welcome_text(username: str) -> str:
  return (
    f"Привет, {username}! 👋\n\n"
    f"{WELCOME_TEXT}\n\n"
    "Доступные команды:\n"
    "/start - начать диалог\n"
    "/help - показать справку\n"
    "/prompts - список сценариев\n"
    "/prompt 1 - выбрать сценарий по номеру\n"
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


@dp.message(Command("prompts"))
async def prompts_list(message: Message) -> None:
  lines = ["📚 Доступные сценарии промптов:\n"]
  for prompt in PROMPT_TEMPLATES:
    lines.append(f"/{prompt['id']} — {prompt['name']}")
  lines.append("\nВыбор: /prompt 1")
  lines.append("Сброс сценария: /prompt 0")
  await message.answer("\n".join(lines))


@dp.message(Command("prompt"))
async def prompt_select(message: Message, command: CommandObject) -> None:
  user_id = message.from_user.id
  args = (command.args or "").strip()

  if not args:
    await message.answer("Укажи номер сценария, например: /prompt 2")
    return

  if not args.isdigit():
    await message.answer("Номер должен быть числом, например: /prompt 2")
    return

  prompt_id = int(args)
  if prompt_id == 0:
    active_prompts.pop(user_id, None)
    await message.answer("✅ Сценарий сброшен. Используется обычный ассистент.")
    return

  prompt = get_prompt_by_id(prompt_id)
  if not prompt:
    await message.answer("Сценарий не найден. Смотри список: /prompts")
    return

  active_prompts[user_id] = prompt_id
  await message.answer(
    f"✅ Выбран сценарий: {prompt['name']}\n\n"
    f"Контекст: {prompt['context']}\n\n"
    f"Пример запроса:\n{prompt['test_input']}"
  )
  logger.info("Пользователь %s выбрал промпт id=%s", user_id, prompt_id)


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
  prompt_id = active_prompts.get(user_id)
  prompt = get_prompt_by_id(prompt_id) if prompt_id else None
  prompt_name = prompt["name"] if prompt else "обычный ассистент"

  await message.answer(
    "📊 Статистика использования\n\n"
    f"👤 Ваш ID: {user_id}\n"
    f"💬 Сообщений в контексте: {messages_count}\n"
    f"🤖 Модель AI: {model_name}\n"
    f"🔌 Провайдер: {API_PROVIDER}\n"
    f"🎯 Сценарий: {prompt_name}\n"
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
    prompt_id = active_prompts.get(user_id)
    prompt = get_prompt_by_id(prompt_id) if prompt_id else None
    system_prompt = build_system_prompt(prompt)

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(context_manager.get_messages(user_id))
    messages.append({"role": "user", "content": user_text})

    reply = strip_markdown(await asyncio.to_thread(api_client.get_reply, messages))

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
  await bot.delete_webhook(drop_pending_updates=True)
  logger.info(
    "Бот запущен (провайдер: %s, модель: %s, сценариев: %s)",
    API_PROVIDER,
    OPENAI_MODEL,
    len(PROMPT_TEMPLATES),
  )
  await dp.start_polling(bot)


if __name__ == "__main__":
  asyncio.run(main())
