import logging

from openai import OpenAI

from config import MAX_TOKENS, OPENAI_API_KEY, OPENAI_MODEL, TEMPERATURE

logger = logging.getLogger(__name__)


class APIClient:
  def __init__(self) -> None:
    self._client = OpenAI(api_key=OPENAI_API_KEY)

  def get_reply(self, messages: list[dict]) -> str:
    logger.info(
      "Запрос к API: model=%s, temperature=%s, max_tokens=%s, messages_count=%s",
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
      logger.info("Ответ API получен, длина=%s", len(reply))
      return reply
    except Exception as error:
      logger.exception("Ошибка API: %s", error)
      raise
