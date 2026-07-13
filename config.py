import os
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

# Токены и настройки
BOT_TOKEN = os.getenv('BOT_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Настройки OpenAI
OPENAI_MODEL = "gpt-4o-mini"  # Используем доступную модель вместо gpt-5-mini-2025-08-07
TEMPERATURE = 1.0
MAX_TOKENS = 1000

# Настройки контекста
MAX_CONTEXT_MESSAGES = 20  # Максимальное количество сообщений в контексте

# Проверяем наличие обязательных переменных
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден в переменных окружения")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY не найден в переменных окружения")
if not OPENAI_API_KEY.isascii():
    raise ValueError(
        "OPENAI_API_KEY содержит недопустимые символы. "
        "Скопируйте ключ заново с platform.openai.com/api-keys"
    )
