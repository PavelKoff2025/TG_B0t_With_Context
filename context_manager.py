from config import MAX_CONTEXT_MESSAGES


class ContextManager:
  """Хранит контекст диалога каждого пользователя в памяти (dict)."""

  def __init__(self) -> None:
    self._context: dict[int, list[dict]] = {}

  def _trim_context(self, user_id: int) -> None:
    history = self._context.get(user_id, [])
    if len(history) > MAX_CONTEXT_MESSAGES:
      self._context[user_id] = history[-MAX_CONTEXT_MESSAGES:]

  def add_user_message(self, user_id: int, text: str) -> None:
    if user_id not in self._context:
      self._context[user_id] = []
    self._context[user_id].append({"role": "user", "content": text})
    self._trim_context(user_id)

  def add_assistant_message(self, user_id: int, text: str) -> None:
    if user_id not in self._context:
      self._context[user_id] = []
    self._context[user_id].append({"role": "assistant", "content": text})
    self._trim_context(user_id)

  def get_messages(self, user_id: int) -> list[dict]:
    return list(self._context.get(user_id, []))

  def get_messages_count(self, user_id: int) -> int:
    return len(self._context.get(user_id, []))

  def clear(self, user_id: int) -> None:
    self._context.pop(user_id, None)
