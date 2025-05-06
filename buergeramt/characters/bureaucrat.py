from buergeramt.characters.agent import Agent
from buergeramt.characters.agent_response import AgentResponse
from buergeramt.characters.context_manager import ContextManager
from buergeramt.characters.message_builder import MessageBuilder


class Bureaucrat:
    def __init__(self, name, title, department, system_prompt, example_interactions=None, api_key=None):
        self.name = name
        self.title = title
        self.department = department
        self.system_prompt = system_prompt
        self.example_interactions = example_interactions or []
        self.context_manager = ContextManager()
        self.agent = Agent(api_key=api_key)
        self.message_builder = MessageBuilder(self.system_prompt, self.example_interactions, self.context_manager)
        print(f"Using {self.agent.get_model()} for {name}")

    def introduce(self) -> str:
        return f"Mein Name ist {self.name}, {self.title} der Abteilung {self.department}."

    def _get_stage_guidance(self, game_state):
        """Get guidance based on current game stage"""
        # No documents yet
        if not game_state.collected_documents:
            return "The user is in the early stage and needs to submit initial documents. As the Erstbearbeitung, you should ask for ID and gift details."

        # Has Schenkungsanmeldung but no Wertermittlung
        if (
            "Schenkungsanmeldung" in game_state.collected_documents
            and "Wertermittlung" not in game_state.collected_documents
        ):
            return "The user has the initial application but needs valuation. As Fachprüfung, you should request market comparison and expert opinion."

        # Has Wertermittlung but no Freibetragsbescheinigung
        if (
            "Wertermittlung" in game_state.collected_documents
            and "Freibetragsbescheinigung" not in game_state.collected_documents
        ):
            return "The user has valuation but needs exemption certificate. As Abschlussstelle, you should ask for relationship proof and previous gifts."

        # Has most documents but not final one
        if (
            "Freibetragsbescheinigung" in game_state.collected_documents
            and "Zahlungsaufforderung" not in game_state.collected_documents
        ):
            return "The user is in the final stage and needs payment request. Return to Erstbearbeitung for final processing."

        return None

    def respond(self, query, game_state) -> AgentResponse:
        """
        respond to user input and return structured output for the game engine to process.
        output is always an AgentResponse instance (enforced by pydantic).
        if the agent cannot respond (e.g. no api key or error), raise an exception.
        """
        if not self.agent.has_api_key():
            raise RuntimeError("AI agent is not available: missing API key.")

        system_instruction = (
            "You are a bureaucratic AI agent in a German administrative adventure game. "
            "Analyze the user's input in the context of the current game state. "
            "Always respond with a JSON object in the following format: "
            "{ 'response_text': <text>, 'actions': { 'intent': <intent>, 'document': <document>, "
            "'requirements_met': <bool>, 'evidence': <list>, 'department': <str>, 'valid': <bool>, 'message': <str> } } "
            "Possible values for intent: 'request_document', 'provide_evidence', 'switch_department', 'greeting', 'other'. "
            "If the user requests a document, check if all requirements are met and set 'requirements_met' accordingly. "
            "If the user provides evidence, list it in 'evidence'. "
            "If the user wants to switch department, set 'department'. "
            "If the input is invalid or incomplete, set 'valid' to false and explain in 'message'. "
            "Keep 'response_text' as your in-character reply to the user. "
            "If a field is not relevant, set it to null or an empty list."
        )
        game_state_info = self.message_builder._format_game_state(game_state)
        user_msg = {"role": "user", "content": f"Eingabe: '{query}'\nAktueller Spielstand: {game_state_info}"}
        try:
            messages = [{"role": "system", "content": system_instruction}, user_msg]
            completion = self.agent.chat_structured(
                messages=messages, response_format=AgentResponse, max_tokens=200, temperature=0
            )
            agent_response = completion.choices[0].message.parsed
            self.context_manager.add_exchange(query, agent_response.response_text)
            return agent_response
        except Exception as e:
            print(f"API Error (structured): {e}")
            raise RuntimeError("AI agent failed to respond.")

    # TODO: implement this somewhere
    def give_hint(self, game_state):
        if not self.agent.has_api_key():
            raise RuntimeError("AI agent is not available: missing API key.")
        state_info = self.message_builder._format_game_state(game_state)
        prompt = f"""
        As {self.name}, provide a hint to the user about their next steps.

        Game state: {state_info}

        Based on your bureaucratic personality, what hint would you give?
        Keep it brief (1-2 sentences) and in character.
        """
        try:
            response = self.agent.chat([{"role": "user", "content": prompt}], max_tokens=100, temperature=0.7)
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"API Error in give_hint: {e}")
            raise RuntimeError("AI agent failed to provide a hint.")
