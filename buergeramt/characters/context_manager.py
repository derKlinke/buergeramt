class ContextManager:
    def __init__(self):
        self._history = []
        self._system_notes = []

    def add_exchange(self, user_message, assistant_message):
        """Add a complete user-assistant exchange to history"""
        self._history.append({"role": "user", "content": user_message})
        self._history.append({"role": "assistant", "content": assistant_message})

    def add_message(self, role, content):
        """Add a single message to history with specified role"""
        self._history.append({"role": role, "content": content})
        
    def add_system_note(self, note):
        """Add a system note to provide additional context to the agent"""
        self._system_notes.append({"role": "system", "content": note})
        # Keep only the 3 most recent system notes to avoid clutter
        if len(self._system_notes) > 3:
            self._system_notes.pop(0)

    def get_recent(self, n=6):
        """Get recent conversation history plus any system notes"""
        # Always include system notes first, followed by recent conversation history
        return self._system_notes + self._history[-n:]

    def clear(self):
        """Clear all history"""
        self._history = []
        self._system_notes = []

    def all(self):
        """Get complete history including system notes"""
        return self._system_notes + self._history
