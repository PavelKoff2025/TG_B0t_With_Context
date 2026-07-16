import logging

from openai import OpenAI

from config import (
  GENAPI_BASE_URL,
  GENAPI_KEY,
  MAX_TOKENS,
  OPENAI_MODEL,
  TEMPERATURE,
)

logger = logging.getLogger(__name__)


class GenAPIClient:
  """Клиент GenAPI (OpenAI-совместимый прокси)."""

  def __init__(self) -> None:
    if not GENAPI_KEY:
      raise ValueError("GENAPI_KEY не задан в .env")
    self._client = OpenAI(api_key=GENAPI_KEY, base_url=GENAPI_BASE_URL)

  def get_reply(self, messages: list[dict]) -> str:
    logger.info(
      "genapi: base_url=%s, model=%s, temperature=%s, max_tokens=%s, messages_count=%s",
      GENAPI_BASE_URL,
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
      logger.info("Ответ genapi получен, длина=%s", len(reply))
      return reply
    except Exception as error:
      logger.exception("Ошибка genapi: %s", error)
      raise
