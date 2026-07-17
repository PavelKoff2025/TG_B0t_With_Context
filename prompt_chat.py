#!/usr/bin/env python3
"""
Скрипт для проверки работы промптов из папки prompts/.
Интерфейс и сценарий — как у преподавателя.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"


def truncate(text: str, limit: int = 90) -> str:
  text = " ".join(text.split())
  if len(text) <= limit:
    return text
  return text[: limit - 1] + "…"


def load_prompt_files() -> list[tuple[Path, dict]]:
  items: list[tuple[Path, dict]] = []
  for path in sorted(PROMPTS_DIR.glob("*.json")):
    try:
      data = json.loads(path.read_text(encoding="utf-8"))
      items.append((path, data))
    except json.JSONDecodeError:
      print(f"❌ Неверный JSON: {path.name}")
  if not items:
    print(f"❌ В папке {PROMPTS_DIR} нет JSON-файлов")
  return items


def display_prompts(items: list[tuple[Path, dict]]) -> None:
  print("\n" + "=" * 70)
  print("📋 Доступные промпты")
  print("=" * 70)
  for index, (_path, prompt) in enumerate(items, start=1):
    print(f"\n{index}. {prompt.get('name', 'Без названия')}")
    print(f"   📌 ID: {prompt.get('prompt_id', '—')}")
    print(f"   📁 Категория: {prompt.get('category', '—')}")
    print(f"   ℹ️  Описание: {truncate(prompt.get('description', '—'))}")
    print(f"   🤖 Роль: {truncate(prompt.get('role', '—'))}")
    print(f"   📄 Контекст: {truncate(prompt.get('context', '—'))}")
    if prompt.get("test_input"):
      print("   ✨ Есть тестовый пример")
  print("\n" + "=" * 70)


def build_messages(prompt: dict, user_input: str) -> list[dict]:
  system = prompt.get("role", "Ты полезный ассистент.")
  parts = [
    f"Контекст: {prompt.get('context', '')}",
    f"Задача: {prompt.get('description', '')}",
  ]
  if "structure" in prompt:
    parts.append(
      "Структура ответа:\n"
      + json.dumps(prompt["structure"], ensure_ascii=False, indent=2)
    )
  if "format" in prompt:
    parts.append(
      "Требования к формату:\n"
      + json.dumps(prompt["format"], ensure_ascii=False, indent=2)
    )
    template = prompt["format"].get("template")
    if template:
      fence_note = (
        "Дерево директорий обязательно оборачивай в блок ```text ... ```, "
        "чтобы оно отображалось столбиком на GitHub."
        if prompt.get("prompt_id") == "code_structure"
        else "Не используй JSON. Не оборачивай весь ответ в ```json."
      )
      parts.append(
        "Обязательный шаблон ответа (соблюдай строго):\n"
        f"{template}\n\n"
        f"{fence_note}"
      )
  parts.append(f"Входные данные:\n{user_input}")
  return [
    {"role": "system", "content": system},
    {"role": "user", "content": "\n\n".join(parts)},
  ]


def ask_user_input(prompt: dict) -> str | None:
  if prompt.get("test_input"):
    print("\n💡 Доступен тестовый вопрос:")
    print(prompt["test_input"])
    use_test = input(
      "\n🤔 Использовать тестовый вопрос? (y/n, по умолчанию n): "
    ).strip().lower()
    if use_test in ["y", "yes", "да", "д"]:
      print("✅ Используем тестовый вопрос")
      return prompt["test_input"]

  user_input = input("\n💬 Введите ваш текст: ").strip()
  if not user_input:
    print("❌ Ввод не может быть пустым")
    return None
  return user_input


def ask_model_settings() -> tuple[float, int, str] | None:
  print("\n⚙️  Настройки модели:")
  try:
    temperature = float(
      input("🌡️  Введите temperature (0.0-1.0, по умолчанию 0.7): ") or "0.7"
    )
    if not 0.0 <= temperature <= 1.0:
      print("❌ temperature должен быть от 0.0 до 1.0")
      return None

    max_tokens = int(input("📊 Введите max_tokens (по умолчанию 2000): ") or "2000")
    if max_tokens <= 0:
      print("❌ max_tokens должен быть больше 0")
      return None

    model = input("🤖 Введите модель (по умолчанию gpt-4o-mini): ").strip() or "gpt-4o-mini"
    return temperature, max_tokens, model
  except ValueError:
    print("❌ Некорректное число")
    return None


def send_request(
  client: OpenAI,
  messages: list[dict],
  temperature: float,
  max_tokens: int,
  model: str,
):
  print("\n⏳ Отправляем запрос к OpenAI...")
  return client.chat.completions.create(
    model=model,
    messages=messages,
    temperature=temperature,
    max_tokens=max_tokens,
  )


def display_result(response, prompt_name: str) -> None:
  print("\n" + "=" * 70)
  print(f"✅ Ответ от OpenAI - {prompt_name}")
  print("=" * 70)
  print(response.choices[0].message.content)
  print("=" * 70)
  print("\n📊 Информация о запросе:")
  print(f"   • Модель: {response.model}")
  print(f"   • Всего токенов: {response.usage.total_tokens}")
  print(f"   • Промпт: {response.usage.prompt_tokens}")
  print(f"   • Ответ: {response.usage.completion_tokens}")


def main() -> None:
  load_dotenv()
  api_key = os.getenv("OPENAI_API_KEY")
  if not api_key:
    print("❌ Не найден OPENAI_API_KEY в .env")
    return

  client = OpenAI(api_key=api_key)
  print("🤖 Prompt Chat — проверка промптов из папки prompts/")

  items = load_prompt_files()
  if not items:
    return

  try:
    while True:
      display_prompts(items)
      choice = input(
        f"\n🔢 Выберите промпт (1-{len(items)}) или 'выход' для завершения: "
      ).strip().lower()

      if choice in ["выход", "exit", "quit", "q"]:
        print("\n👋 До свидания!")
        break

      if not choice.isdigit() or not (1 <= int(choice) <= len(items)):
        print(f"❌ Введите число от 1 до {len(items)} или 'выход'")
        continue

      _path, prompt = items[int(choice) - 1]
      prompt_name = prompt.get("name", _path.stem)
      print(f"\n✅ Выбран промпт: {prompt_name}")

      user_input = ask_user_input(prompt)
      if user_input is None:
        continue

      settings = ask_model_settings()
      if settings is None:
        continue
      temperature, max_tokens, model = settings

      messages = build_messages(prompt, user_input)
      response = send_request(client, messages, temperature, max_tokens, model)
      display_result(response, prompt_name)

  except KeyboardInterrupt:
    print("\n\n👋 Программа прервана")
  except Exception as error:
    print(f"❌ Ошибка: {error}")


if __name__ == "__main__":
  main()
