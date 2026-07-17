# TG Bot With Context

Telegram AI-ассистент на **aiogram** с памятью диалога для клиентских сценариев. Подключает OpenAI, ProxyAPI или GenAPI — можно выбрать провайдера под бюджет и доступность.

**Что уже готово для бизнеса:**
- диалог с контекстом (история в памяти, `/clear`, `/stats`);
- управляемые промпты под типовые задачи: резюме текста, структура кода, план работ;
- A/B-сравнение `temperature` (0.2 vs 0.8) с отчётом для куратора/заказчика;
- отдельный мини-кейс «стилист» (JSON-артефакт + few-shot).

| Артефакт | Путь |
|----------|------|
| Отчёт по промптам урока | [`docs/prompts_testing_report.md`](docs/prompts_testing_report.md) |
| Примеры ответов | [`docs/prompt_tests/`](docs/prompt_tests/) |
| Промпты урока | [`prompts/`](prompts/) |
| Гайд стилиста | [`docs/stylist_guide.md`](docs/stylist_guide.md) |

Диалоговые промпты бота — в `prompts.json`; интерактивный прогон урока — `prompt_chat.py`.

## Структура проекта

```text
TG_Bot_With_Contecst/
├── venv/                      # Виртуальное окружение Python
├── .env                       # Секреты (не коммитить)
├── env_example.txt            # Пример .env
├── bot.py                     # Telegram-бот, обработчики
├── config.py                  # Настройки из .env и prompts.json
├── context_manager.py         # История диалога (dict в памяти)
├── openai_direct.py           # Клиент OpenAI
├── proxyapi_client.py         # Клиент ProxyAPI
├── genapi_client.py           # Клиент GenAPI
├── prompts.json               # Системные промпты бота
├── prompts/                   # Промпты урока (Markdown-формат)
│   ├── 01_summary_prompt.json
│   ├── 02_code_structure_prompt.json
│   └── 03_task_planning_prompt.json
├── prompt_chat.py             # Интерактивный тест промптов
├── run_temperature_tests.py   # Сравнение temperature 0.2 / 0.8
├── stylist_show.py            # Демо артефакта «стилист»
├── docs/
│   ├── prompts_testing_report.md   # Отчёт для куратора
│   ├── prompt_tests/               # Ответы при разных temperature
│   └── stylist_guide.md
├── requirements.txt
└── run.sh                     # Запуск на macOS
```

## Установка (macOS)

1. Перейдите в папку проекта:

```bash
cd ~/Desktop/TG_Bot_With_Contecst
```

2. Создайте виртуальное окружение:

```bash
python3 -m venv venv
```

3. Активируйте его:

```bash
source venv/bin/activate
```

4. Установите зависимости:

```bash
pip install -r requirements.txt
```

5. Скопируйте `env_example.txt` в `.env` и укажите токены:

```bash
cp env_example.txt .env
```

Откройте `.env` и заполните:
- `BOT_TOKEN` — токен Telegram-бота
- `API_PROVIDER` — `openai`, `proxyapi` или `genapi`
- соответствующий ключ: `OPENAI_API_KEY` / `PROXYAPI_KEY` / `GENAPI_KEY`

## Запуск

```bash
source venv/bin/activate
python bot.py
```

Или одной командой:

```bash
chmod +x run.sh
./run.sh
```

## Команды бота

- `/start` — начать диалог
- `/help` — показать справку
- `/clear` — очистить контекст диалога
- `/reset` — очистить контекст диалога
- `/stats` — показать статистику
- `очистить контекст` — очистить историю (текстом)

---

## Короткий отчёт

### Тестирование параметров модели

Для каждого прогона меняйте `TEMPERATURE` и `MAX_TOKENS` в `config.py`, перезапускайте бота и задавайте один и тот же вопрос, например: *«Расскажи про Python в 3 предложениях»*.

Токены смотрите в логах или в [OpenAI Usage](https://platform.openai.com/usage).

**Ориентировочная стоимость gpt-4o-mini:**
- вход: ~$0.15 / 1M токенов
- выход: ~$0.60 / 1M токенов

| Модель | temperature | max_tokens | № прогона | Эффект (сжатость / креатив) | Токены (вход / выход) | ~Стоимость |
|--------|-------------|------------|-----------|-----------------------------|------------------------|------------|
| gpt-4o-mini | 0.3 | 100 | 1 | Сжато, обрезано на лимите 100 токенов | 17 / 100 | ~$0.000063 |
| gpt-4o-mini | 0.7 | 500 | 2 | Сбалансированно, полный ответ за 3 предложения | 17 / 103 | ~$0.000064 |
| gpt-4o-mini | 1.0 | 1000 | 3 | Чуть разнообразнее, длина ответа схожа | 17 / 104 | ~$0.000065 |

**Вопрос для всех прогонов:** «Расскажи про Python в 3 предложениях»

**Скрины логов прогонов:**

![Прогон 1 — temp 0.3](docs/run1_temp_0.3.png)
![Прогон 2 — temp 0.7](docs/run2_temp_0.7.png)
![Прогон 3 — temp 1.0](docs/run3_temp_1.0.png)

**Формула стоимости:**
```
стоимость ≈ (входные_токены × 0.15 + выходные_токены × 0.60) / 1_000_000
```

### Скрин Usage / ID запросов

Скриншот использования API из [OpenAI Usage](https://platform.openai.com/usage):

![Usage screenshot](docs/usage_screenshot.png)

**Итого за 13.07.2026:** 14 запросов, 4 744 токена, $0.00 (бесплатный лимит).

Экспорт данных: `docs/completions_usage_2026-06-13_2026-07-13.csv`

### Выводы

- При **temperature 0.3** и **max_tokens 100** ответ обрезается на лимите — самый сжатый вариант.
- При **temperature 0.7** ответ полный и сбалансированный — оптимально для бота.
- При **temperature 1.0** ответ чуть длиннее и разнообразнее, но на коротком вопросе разница минимальна.
- Расход токенов на один запрос: **117–121** (~$0.00006).

