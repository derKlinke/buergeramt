import os


class Agent:
    """
    wrapper around pydantic-ai Agent for both free-form and structured output
    """
    def __init__(self, api_key=None, *, model: str = "gpt-4o-mini", deps_type=None, output_type=None, system_prompt=None):
        # defer import of pydantic-ai until agent instantiation
        try:
            from pydantic_ai import Agent as PydanticAgent
        except ImportError:
            raise RuntimeError(
                "pydantic-ai is required but not installed."
                " Please install pydantic-ai>=0.1.10"
            )
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.agent = PydanticAgent(
            model,
            api_key=self.api_key,
            deps_type=deps_type,
            output_type=output_type,
            system_prompt=system_prompt,
        )

    def get_model(self) -> str:
        return getattr(self.agent, "model", None) or getattr(self.agent, "model_name", None)

    def has_api_key(self) -> bool:
        return bool(self.api_key)

    def run(self, user_input: str, *, deps=None, output_type=None, system_prompt=None, **kwargs):
        """run a sync agent call with optional schema and deps"""
        return self.agent.run_sync(
            user_input,
            deps=deps,
            output_type=output_type,
            system_prompt=system_prompt,
            **kwargs,
        )
