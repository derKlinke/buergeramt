import os

from openai import OpenAI


class OpenAIAgent:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.client = OpenAI(api_key=self.api_key)
        self.model = "gpt-3.5-turbo"
        try:
            self.client.chat.completions.create(model="gpt-4", messages=[{"role": "user", "content": "test"}], max_tokens=1)
            self.model = "gpt-4"
        except Exception:
            pass

    def get_model(self):
        return self.model

    def has_api_key(self):
        return bool(self.api_key)

    def chat(self, messages, max_tokens=200, temperature=0.7):
        return self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature
        )
