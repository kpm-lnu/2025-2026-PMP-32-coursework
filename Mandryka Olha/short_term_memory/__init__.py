
from .short_term import ShortTermMemory

__all__ = ["ShortTermMemory", "Memory"]

class Memory:

	def __init__(self) -> None:
		self._store = {}

	def set(self, key: str, value):
		self._store[key] = value

	def get(self, key: str, default=None):
		return self._store.get(key, default)

	def delete(self, key: str):
		self._store.pop(key, None)

	def clear(self):
		self._store.clear()
