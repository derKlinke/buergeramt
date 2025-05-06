
from pydantic import BaseModel

from buergeramt.characters.ai_agent import OpenAIAgent
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
        self.agent = OpenAIAgent(api_key=api_key)
        self.message_builder = MessageBuilder(self.system_prompt, self.example_interactions, self.context_manager)
        print(f"Using {self.agent.get_model()} for {name}")

    def introduce(self) -> str:
        return f"Mein Name ist {self.name}, {self.title} der Abteilung {self.department}."

    def build_messages(self, query, game_state):
        stage_guidance = self._get_stage_guidance(game_state)
        return self.message_builder.build(query, game_state, stage_guidance=stage_guidance)



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

    class ValidationStep(BaseModel):
        explanation: str
        output: str

    class UserInputValidation(BaseModel):
        valid: bool
        message: str
        intent: str | None = None
        document: str | None = None
        evidence: list[str] = []
        steps: list['Bureaucrat.ValidationStep'] = []

    def _validate_input(self, text: str, game_state) -> 'Bureaucrat.UserInputValidation':
        if not self.agent.has_api_key():
            return Bureaucrat.UserInputValidation(valid=True, message="", intent=None, document=None, evidence=[], steps=[])

        persona_prompt = self.system_prompt.strip()
        game_state_info = self.message_builder._format_game_state(game_state)
        validation_instruction = (
            "Bevor du antwortest, prüfe die Nutzereingabe nach folgenden Regeln: "
            "- Ist die Anfrage höflich und vollständig? "
            "- Ist sie relevant für die aktuelle Spielsituation? "
            "- Enthält sie einen klaren Bezug zu Dokumenten, Formularen oder Beweismitteln? "
            "Gib eine strukturierte Analyse im folgenden Format zurück: "
            "UserInputValidation(valid: bool, message: str, intent: str | None, document: str | None, evidence: list[str], steps: list[ValidationStep]) "
            "Jeder Schritt in steps sollte eine kurze Erklärung und das jeweilige Zwischenergebnis enthalten. "
            "Mögliche Werte für intent: 'request_document', 'provide_evidence', 'greeting', 'other'. "
            "Lasse 'document' und 'evidence' leer, falls nicht relevant."
        )
        validation_prompt = f"{persona_prompt}\n\n{validation_instruction}\n\nAktueller Spielstand: {game_state_info}\nNutzereingabe: '{text}'"
        try:
            completion = self.agent.client.beta.chat.completions.parse(
                model=self.agent.get_model(),
                messages=[{"role": "system", "content": validation_prompt}],
                response_format=Bureaucrat.UserInputValidation,
                temperature=0
            )
            validation = completion.choices[0].message.parsed
            return validation
        except Exception:
            return Bureaucrat.UserInputValidation(valid=True, message="", intent=None, document=None, evidence=[], steps=[])

    def respond(self, query, game_state):
        validation = self._validate_input(query, game_state)
        # Use Pydantic model fields, not dict access
        if not validation.valid:
            return validation.message
        try:
            if not self.agent.has_api_key():
                return self._fallback_response(query, game_state)
            messages = self.build_messages(query, game_state)
            messages.append({
                "role": "system",
                "content": f"Strukturiertes Analyseergebnis der Nutzereingabe: {validation.model_dump_json()}"
            })
            response = self.agent.chat(messages)
            ai_response = response.choices[0].message.content.strip()
            self.context_manager.add_exchange(query, ai_response)
            return ai_response
        except Exception as e:
            print(f"API Error: {e}")
            return self._fallback_response(query, game_state)

    # navigation to other agents is intentionally not supported in this Bureaucrat class

    def give_hint(self, game_state):
        try:
            if not self.agent.has_api_key():
                return self._fallback_hint(game_state)
            state_info = self.message_builder._format_game_state(game_state)
            prompt = f"""
            As {self.name}, provide a hint to the user about their next steps.

            Game state: {state_info}

            Based on your bureaucratic personality, what hint would you give?
            Keep it brief (1-2 sentences) and in character.
            """
            response = self.agent.chat([
                {"role": "user", "content": prompt}
            ], max_tokens=100, temperature=0.7)
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"API Error in give_hint: {e}")
            return self._fallback_hint(game_state)

    def _fallback_response(self, query, game_state):
        """Fallback response if API fails"""
        # Each subclass should implement this
        return "Es tut mir leid, das System ist momentan nicht verfügbar."

    def _fallback_hint(self, game_state):
        """Fallback hint if API fails"""
        # Each subclass should implement this
        return "Vielleicht sollten Sie einen anderen Beamten aufsuchen."
