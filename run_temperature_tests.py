#!/usr/bin/env python3
"""Тест трёх промптов при temperature 0.2 и 0.8."""

from __future__ import annotations

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from prompt_chat import build_messages, load_prompt_files

TEMPS = [0.2, 0.8]
MAX_TOKENS = 2000
MODEL = "gpt-4o-mini"
OUT_DIR = Path("docs/prompt_tests")


def main() -> None:
  load_dotenv()
  api_key = os.getenv("OPENAI_API_KEY")
  if not api_key:
    print("Нет OPENAI_API_KEY")
    return

  client = OpenAI(api_key=api_key)
  OUT_DIR.mkdir(parents=True, exist_ok=True)
  index = []

  for path, prompt in load_prompt_files():
    pid = prompt.get("prompt_id", path.stem)
    name = prompt.get("name", path.stem)
    print(f"\n=== {name} ({pid}) ===", flush=True)

    for temperature in TEMPS:
      print(f"  temperature={temperature} ...", flush=True)
      response = client.chat.completions.create(
        model=MODEL,
        messages=build_messages(prompt, prompt["test_input"]),
        temperature=temperature,
        max_tokens=MAX_TOKENS,
      )
      text = response.choices[0].message.content or ""
      usage = response.usage
      stem = f"{pid}_temp_{str(temperature).replace('.', '_')}"
      entry = {
        "prompt_id": pid,
        "prompt_name": name,
        "prompt_file": path.name,
        "model": response.model,
        "temperature": temperature,
        "max_tokens": MAX_TOKENS,
        "usage": {
          "prompt_tokens": usage.prompt_tokens,
          "completion_tokens": usage.completion_tokens,
          "total_tokens": usage.total_tokens,
        },
        "response_length_chars": len(text),
        "is_markdown": (
          text.strip().startswith("#")
          or text.strip().startswith("Для ")
          or "###" in text[:300]
        ),
        "is_json": text.strip().startswith("{") or text.strip().startswith("```json"),
        "has_tree": "├──" in text,
        "response": text,
      }
      (OUT_DIR / f"{stem}.json").write_text(
        json.dumps(entry, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
      )
      (OUT_DIR / f"{stem}.md").write_text(text + "\n", encoding="utf-8")
      index.append({k: v for k, v in entry.items() if k != "response"})
      print(
        f"    tokens={usage.total_tokens}, chars={len(text)}, "
        f"md={entry['is_markdown']}, json={entry['is_json']}",
        flush=True,
      )

  (OUT_DIR / "summary_index.json").write_text(
    json.dumps(index, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
  )
  print(f"\nГотово: {len(index)} прогонов → {OUT_DIR}/", flush=True)


if __name__ == "__main__":
  main()
