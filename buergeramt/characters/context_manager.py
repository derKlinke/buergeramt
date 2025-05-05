class ContextManager:
    def __init__(self):
        self._history = []

    def add_exchange(self, user_message, assistant_message):
        self._history.append({"role": "user", "content": user_message})
        self._history.append({"role": "assistant", "content": assistant_message})

    def add_message(self, role, content):
        self._history.append({"role": role, "content": content})

    def get_recent(self, n=6):
        return self._history[-n:]

    def clear(self):
        self._history = []

    def all(self):
        return list(self._history)
