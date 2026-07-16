#!/usr/bin/env python3
"""Мини-скрипт: показывает итоговый образ стилиста из JSON-артефакта."""

import json
from pathlib import Path

ARTIFACT = Path(__file__).resolve().parent / "docs" / "stylist_run2.json"


def main() -> None:
  if not ARTIFACT.exists():
    print(f"Файл не найден: {ARTIFACT}")
    return

  data = json.loads(ARTIFACT.read_text(encoding="utf-8"))
  response = data["response"]

  print("=" * 50)
  print(f"  {response['title']}")
  print("=" * 50)
  print(f"Погода/планы: {data.get('user_input', '—')}")
  print()
  print("Образы (выбери один):")
  for index, step in enumerate(response["steps"], start=1):
    print(f"  {index}. {step}")
  print()
  print("Заметки:")
  for note in response["notes"]:
    print(f"  • {note}")
  print()
  print(f"Источник: {ARTIFACT.name} | модель: {data.get('model', '—')}")
  print("=" * 50)


if __name__ == "__main__":
  main()
