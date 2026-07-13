#!/bin/bash
cd "$(dirname "$0")"

if [ ! -f "venv/bin/activate" ]; then
  echo "Создаю виртуальное окружение..."
  python3 -m venv venv
fi

source venv/bin/activate
pip install -r requirements.txt
python bot.py
