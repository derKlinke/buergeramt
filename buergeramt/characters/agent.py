import os

from openai import OpenAI


class Agent:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.client = OpenAI(api_key=self.api_key)
        self.model = "gpt-4o"

        try:
            self.client.chat.completions.create(
                model="gpt-4o", messages=[{"role": "user", "content": "test"}], max_tokens=1
            )
        except Exception as e:
            raise RuntimeError("gpt-4o model is required but not available: " + str(e))

    def get_model(self):
        return self.model

    def has_api_key(self):
        return bool(self.api_key)

    def chat(self, messages, max_tokens=200, temperature=0.7):
        return self.client.chat.completions.create(
            model=self.model, messages=messages, max_tokens=max_tokens, temperature=temperature
        )

    def chat_structured(self, messages, response_format, max_tokens=200, temperature=0.7):
        """
        Call the OpenAI completions API with response_format (pydantic model) for structured output.
        Returns the parsed response (pydantic model instance) or raises.
        """
        return self.client.beta.chat.completions.parse(
            model=self.model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            response_format=response_format,
        )
