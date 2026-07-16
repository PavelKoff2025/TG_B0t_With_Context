import logging

from openai import OpenAI

from config import (
  MAX_TOKENS,
  OPENAI_MODEL,
  PROXYAPI_BASE_URL,
  PROXYAPI_KEY,
  TEMPERATURE,
)

logger = logging.getLogger(__name__)


class ProxyAPIClient:
  """Клиент ProxyAPI (OpenAI-совместимый шлюз)."""

  def __init__(self) -> None:
    if not PROXYAPI_KEY:
      raise ValueError("PROXYAPI_KEY не задан в .env")
    self._client = OpenAI(api_key=PROXYAPI_KEY, base_url=PROXYAPI_BASE_URL)

  def get_reply(self, messages: list[dict]) -> str:
    logger.info(
      "proxyapi: base_url=%s, model=%s, temperature=%s, max_tokens=%s, messages_count=%s",
      PROXYAPI_BASE_URL,
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
      logger.info("Ответ proxyapi получен, длина=%s", len(reply))
      return reply
    except Exception as error:
      logger.exception("Ошибка proxyapi: %s", error)
      raise
