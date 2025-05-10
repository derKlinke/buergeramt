import os

from dotenv import load_dotenv
from pydantic_ai import Agent
from pydantic_ai import Tool

from buergeramt.characters.agent_response import AgentResponse
from buergeramt.rules.game_state import (
    GameDeps,
    add_document,
    add_evidence,
    decrease_frustration,
    increase_frustration,
    switch_department,
)
from buergeramt.utils.game_logger import get_logger


class Bureaucrat:
    def __init__(self, name, title, department, system_prompt=None):
        self.name = name
        self.title = title
        self.department = department
        self.last_message = None

        if system_prompt is None:
            from buergeramt.rules.loader import get_config

            config = get_config()
            persona = None

            for p in config.personas.values():
                if p.name == name and p.role == title and p.department == department:
                    persona = p
                    break

            if persona is not None:
                personality_text = "\n".join(f"- {trait}" for trait in persona.personality)
                handled_docs = ", ".join(persona.handled_documents)
                required_evidence = ", ".join(persona.required_evidence)
                tool_instructions = (
                    "\n---\n"
                    "You have access to the following tools for updating the game state. Whenever the user provides a document or evidence, always use the appropriate tool. Do not just mention the action, always call the tool.\n"
                    "\n"
                    "Tool usage examples:\n"
                    "- If the user says 'Hier ist mein Personalausweis', call add_evidence with evidence_name='valid_id', evidence_form='Personalausweis'.\n"
                    "- If the user says 'Ich reiche die Schenkungsanmeldung ein', call add_document with document_name='Schenkungsanmeldung'.\n"
                    "- If the user expresses frustration (e.g., 'Das ist doch lächerlich!'), call increase_frustration.\n"
                    "- If the user calms down, call decrease_frustration.\n"
                    "\n"
                    "Tool reference:\n"
                    "- add_document(document_name: str)\n"
                    "- add_evidence(evidence_name: str, evidence_form: str)\n"
                    "- increase_frustration(amount: int = 1)\n"
                    "- decrease_frustration(amount: int = 1)\n"
                    "- switch_department(department: str)\n"
                    "---\n"
                )
                self.system_prompt = (
                    persona.system_prompt_template.format(
                        name=persona.name,
                        role=persona.role,
                        department=persona.department,
                        personality=personality_text,
                        handled_documents=handled_docs,
                        required_evidence=required_evidence,
                    )
                    + tool_instructions
                )
            else:
                self.system_prompt = "You are a helpful bureaucrat. Always use tools to update the game state."
        else:
            self.system_prompt = system_prompt

        tools = [
            Tool(
                add_document,
                name="add_document",
                description="Add a document to the player's collection",
            ),
            Tool(
                add_evidence,
                name="add_evidence",
                description="Add evidence to the player's collection",
            ),
            Tool(
                increase_frustration,
                name="increase_frustration",
                description="Increase the player's frustration level",
            ),
            Tool(
                decrease_frustration,
                name="decrease_frustration",
                description="Decrease the player's frustration level",
            ),
            Tool(
                switch_department,
                name="switch_department",
                description="Move the player to another department",
            ),
        ]

        self.logger = get_logger()

        load_dotenv()
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "OPENAI_API_KEY is not set in the environment. Please create a .env file or set the variable!"
            )

        self.agent = Agent(
            "openai:gpt-4o-mini",
            system_prompt=self.system_prompt,
            output_type=AgentResponse,
            tools=tools,
        )

        self.logger.logger.info(f"Initialized bureaucrat: {name}, {title} ({department})")
        print(f"Using {self.agent.model.model_name} for {name}")

    def introduce(self, game_state) -> str:
        deps = GameDeps(game_state=game_state)
        result = self.agent.run_sync(
            "The user has just entered your office. Introduce yourself and your role and ask what you can help them with.",
            deps=deps,
            message_history=self.last_message.all_messages() if self.last_message else None,
        )
        self.last_message = result
        return result.output.response_text

    def respond(self, query, game_state) -> str:
        """
        respond to user input and return only a text response for the game engine to process.
        all game state changes must be handled by tool calls from the model, not by parsing output.
        """
        deps = GameDeps(game_state=game_state)
        try:
            result = self.agent.run_sync(
                query,
                deps=deps,
                message_history=self.last_message.all_messages() if self.last_message else None,
            )

            if hasattr(result, "messages"):
                self.logger.log_ai_prompt(result.messages)
            if hasattr(result, "response"):
                self.logger.log_ai_response(result.response)

            self.last_message = result
            return getattr(result.output, "response_text", str(result))
        except Exception as e:
            error_msg = f"API Error: {e}"
            self.logger.log_error(e, f"AI response error for '{query}' from {self.name}")
            raise RuntimeError(error_msg)
