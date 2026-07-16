import json
import os
from pathlib import Path

from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

# Токены и настройки
BOT_TOKEN = os.getenv("BOT_TOKEN")
API_PROVIDER = os.getenv("API_PROVIDER", "openai").strip().lower()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PROXYAPI_KEY = os.getenv("PROXYAPI_KEY") or os.getenv("PROXYAPI_API_KEY")
GENAPI_KEY = os.getenv("GENAPI_KEY")

PROXYAPI_BASE_URL = os.getenv(
  "PROXYAPI_BASE_URL",
  "https://api.proxyapi.ru/openai/v1",
)
GENAPI_BASE_URL = os.getenv(
  "GENAPI_BASE_URL",
  "https://proxy.gen-api.ru/v1",
)

# Настройки модели
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "1000"))

# Настройки контекста
MAX_CONTEXT_MESSAGES = int(os.getenv("MAX_CONTEXT_MESSAGES", "20"))

# Промпты из prompts.json
_PROMPTS_PATH = Path(__file__).resolve().parent / "prompts.json"
with _PROMPTS_PATH.open(encoding="utf-8") as prompts_file:
  PROMPTS_DATA = json.load(prompts_file)

SYSTEM_PROMPT = PROMPTS_DATA.get(
  "system",
  "Ты полезный AI-ассистент в Telegram-боте.",
)
if "markdown" not in SYSTEM_PROMPT.lower() and "разметк" not in SYSTEM_PROMPT.lower():
  SYSTEM_PROMPT = (
    f"{SYSTEM_PROMPT} "
    "Отвечай обычным текстом без Markdown: без **, __, #, ``` и других служебных символов."
  )
WELCOME_TEXT = PROMPTS_DATA.get(
  "welcome",
  "Я AI-ассистент. Напиши сообщение — я отвечу с учётом контекста.",
)
PROMPT_TEMPLATES = PROMPTS_DATA.get("prompts", [])


def get_prompt_by_id(prompt_id: int) -> dict | None:
  for prompt in PROMPT_TEMPLATES:
    if prompt.get("id") == prompt_id:
      return prompt
  return None


def build_system_prompt(prompt: dict | None = None) -> str:
  if not prompt:
    return SYSTEM_PROMPT
  return (
    f"{prompt['role']}.\n"
    f"Контекст: {prompt['context']}.\n"
    f"Задача: {prompt['question']}.\n"
    f"Формат ответа: {prompt['format']}.\n"
    "Отвечай обычным текстом без Markdown: без **, __, #, ``` и других служебных символов."
  )


# Проверяем наличие обязательных переменных
if not BOT_TOKEN:
  raise ValueError("BOT_TOKEN не найден в переменных окружения")

if API_PROVIDER == "openai":
  if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY не найден в переменных окружения")
  if not OPENAI_API_KEY.isascii():
    raise ValueError(
      "OPENAI_API_KEY содержит недопустимые символы. "
      "Скопируйте ключ заново с platform.openai.com/api-keys"
    )
elif API_PROVIDER == "proxyapi":
  if not PROXYAPI_KEY:
    raise ValueError("PROXYAPI_KEY не найден в переменных окружения")
elif API_PROVIDER == "genapi":
  if not GENAPI_KEY:
    raise ValueError("GENAPI_KEY не найден в переменных окружения")
else:
  raise ValueError(
    f"Неизвестный API_PROVIDER={API_PROVIDER!r}. "
    "Допустимо: openai, proxyapi, genapi"
  )
