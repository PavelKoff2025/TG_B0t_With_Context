#!/usr/bin/env python3
"""
Скрипт для работы с заготовленными промптами через OpenAI API.
Использует JSON файл с предустановленными запросами.
Поддерживает последовательность запросов с контекстом диалога.
"""

import json
import logging
import os

from dotenv import load_dotenv
from openai import OpenAI

logger = logging.getLogger(__name__)


def load_prompts():
  """Загружает промпты из JSON файла"""
  try:
    with open("prompts.json", "r", encoding="utf-8") as f:
      data = json.load(f)
      return data["prompts"]
  except FileNotFoundError:
    print("❌ Ошибка: Файл prompts.json не найден")
    return None
  except json.JSONDecodeError:
    print("❌ Ошибка: Неверный формат JSON файла")
    return None


def display_prompts(prompts):
  """Отображает список доступных промптов"""
  print("\n📋 Доступные промпты:")
  print("=" * 60)
  for prompt in prompts:
    print(f"{prompt['id']:2d}. {prompt['name']}")
    print(f"    Роль: {prompt['role']}")
    print(f"    Контекст: {prompt['context']}")
    print(f"    Формат ответа: {prompt['format']}")
    if "test_input" in prompt:
      test_preview = prompt["test_input"][:100]
      suffix = "..." if len(prompt["test_input"]) > 100 else ""
      print(f"    📝 Тестовый вопрос: {test_preview}{suffix}")
    print("-" * 60)


def get_user_input(prompts):
  """Получает выбор пользователя и дополнительные параметры"""
  while True:
    try:
      choice = int(input(f"\n🔢 Выберите промпт (1-{len(prompts)}): "))
      if 1 <= choice <= len(prompts):
        selected_prompt = prompts[choice - 1]
        break
      print(f"❌ Пожалуйста, введите число от 1 до {len(prompts)}")
    except ValueError:
      print("❌ Пожалуйста, введите корректное число")

  temperature = float(input("🌡️  Введите temperature (0.0-1.0, по умолчанию 0.7): ") or "0.7")
  if not 0.0 <= temperature <= 1.0:
    print("❌ Temperature должен быть от 0.0 до 1.0")
    return None, None, None

  max_tokens = int(input("🔢 Введите max_tokens (по умолчанию 2000): ") or "2000")
  if max_tokens <= 0:
    print("❌ max_tokens должен быть больше 0")
    return None, None, None

  if "test_input" in selected_prompt:
    print("\n📝 Доступен тестовый вопрос:")
    print(f"   {selected_prompt['test_input']}")
    use_test = input("\n🤔 Использовать тестовый вопрос? (y/n, по умолчанию y): ").strip().lower()

    if use_test in ["", "y", "yes", "да", "д"]:
      user_input = selected_prompt["test_input"]
      print("✅ Используем тестовый вопрос")
    else:
      user_input = input(f"\n💬 {selected_prompt['question']}\nВведите ваш текст: ").strip()
  else:
    user_input = input(f"\n💬 {selected_prompt['question']}\nВведите ваш текст: ").strip()

  if not user_input:
    print("❌ Ввод не может быть пустым")
    return None, None, None

  return selected_prompt, user_input, {"temperature": temperature, "max_tokens": max_tokens}


def send_request(client, prompt, user_input, params, conversation_history=None):
  """Отправляет запрос к OpenAI API с поддержкой истории диалога"""
  full_question = (
    f"{prompt['question']}\n\n"
    f"Текст для обработки:\n{user_input}\n\n"
    f"Формат ответа: {prompt['format']}"
  )

  messages = [{"role": "system", "content": prompt["role"]}]

  if conversation_history:
    messages.extend(conversation_history)

  messages.append({"role": "user", "content": full_question})

  print("\n⏳ Отправляем запрос к OpenAI...")
  print(f"📝 Выбранный промпт: {prompt['name']}")

  response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=messages,
    temperature=params["temperature"],
    max_tokens=params["max_tokens"],
  )

  return response


def display_dialogue_stats(conversation_history):
  """Отображает статистику диалога"""
  user_messages = len([msg for msg in conversation_history if msg["role"] == "user"])
  assistant_messages = len([msg for msg in conversation_history if msg["role"] == "assistant"])

  print("\n💬 Статистика диалога:")
  print(f"   • Сообщений пользователя: {user_messages}")
  print(f"   • Ответов ассистента: {assistant_messages}")
  print(f"   • Всего сообщений: {len(conversation_history)}")


def display_result(response, prompt_name, conversation_history=None):
  """Отображает результат запроса"""
  print("\n" + "=" * 80)
  print(f"✅ Ответ от OpenAI - {prompt_name}")
  print("=" * 80)
  print(response.choices[0].message.content)
  print("=" * 80)

  print("\n📊 Информация о запросе:")
  print(f"   • Модель: {response.model}")
  print(f"   • Использовано токенов: {response.usage.total_tokens}")
  print(f"   • Промпт токены: {response.usage.prompt_tokens}")
  print(f"   • Ответ токены: {response.usage.completion_tokens}")

  if conversation_history:
    display_dialogue_stats(conversation_history)


def get_follow_up_question():
  """Получает дополнительный вопрос от пользователя"""
  print("\n" + "=" * 60)
  print("💬 Дополнительные вопросы")
  print("=" * 60)

  while True:
    follow_up = input("\n❓ Задайте дополнительный вопрос (или 'выход' для завершения): ").strip()

    if not follow_up:
      print("❌ Вопрос не может быть пустым")
      continue

    if follow_up.lower() in ["выход", "exit", "quit", "q", "стоп", "stop"]:
      return None

    return follow_up


class OpenAIDirectClient:
  """Клиент для Telegram-бота (совместимость с bot.py)."""

  def __init__(self) -> None:
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
      raise ValueError("OPENAI_API_KEY не задан в .env")
    self._client = OpenAI(api_key=api_key)

  def get_reply(self, messages: list[dict]) -> str:
    from config import MAX_TOKENS, OPENAI_MODEL, TEMPERATURE

    logger.info(
      "openai_direct: model=%s, temperature=%s, max_tokens=%s, messages_count=%s",
      OPENAI_MODEL,
      TEMPERATURE,
      MAX_TOKENS,
      len(messages),
    )
    logger.info("Параметры messages: %s", messages)

    try:
      response = self._client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=messages,
        temperature=TEMPERATURE,
        max_tokens=MAX_TOKENS,
      )
      reply = response.choices[0].message.content or "Не удалось получить ответ."
      usage = response.usage
      if usage:
        logger.info(
          "Использовано токенов: prompt=%s, completion=%s, total=%s",
          usage.prompt_tokens,
          usage.completion_tokens,
          usage.total_tokens,
        )
      return reply
    except Exception as error:
      logger.exception("Ошибка openai_direct: %s", error)
      raise


def main():
  # Загружаем переменные окружения из .env файла
  load_dotenv()

  # Получаем API ключ из переменных окружения
  api_key = os.getenv("OPENAI_API_KEY")
  if not api_key:
    print("❌ Ошибка: Не найден OPENAI_API_KEY в .env файле")
    return

  # Инициализируем клиент OpenAI
  client = OpenAI(api_key=api_key)

  print("🤖 OpenAI API - Диалог с заготовленными промптами")
  print("=" * 60)

  # Загружаем промпты
  prompts = load_prompts()
  if not prompts:
    return

  try:
    # Отображаем доступные промпты
    display_prompts(prompts)

    # Получаем выбор пользователя
    selected_prompt, user_input, params = get_user_input(prompts)
    if not selected_prompt:
      return

    # Инициализируем историю диалога
    conversation_history = []

    # Отправляем первый запрос
    response = send_request(client, selected_prompt, user_input, params, conversation_history)

    # Отображаем результат
    display_result(response, selected_prompt["name"], conversation_history)

    # Добавляем первый обмен в историю
    conversation_history.append(
      {
        "role": "user",
        "content": (
          f"{selected_prompt['question']}\n\n"
          f"Текст для обработки:\n{user_input}\n\n"
          f"Формат ответа: {selected_prompt['format']}"
        ),
      }
    )
    conversation_history.append(
      {"role": "assistant", "content": response.choices[0].message.content}
    )

    # Цикл для дополнительных вопросов
    while True:
      follow_up = get_follow_up_question()
      if follow_up is None:
        break

      # Отправляем дополнительный запрос
      response = send_request(client, selected_prompt, follow_up, params, conversation_history)

      # Отображаем результат
      display_result(response, selected_prompt["name"], conversation_history)

      # Добавляем обмен в историю
      conversation_history.append({"role": "user", "content": follow_up})
      conversation_history.append(
        {"role": "assistant", "content": response.choices[0].message.content}
      )

    print("\n👋 Диалог завершен. До свидания!")

  except KeyboardInterrupt:
    print("\n\n👋 Программа прервана пользователем")
  except Exception as e:
    print(f"❌ Ошибка при запросе к API: {e}")


if __name__ == "__main__":
  main()
