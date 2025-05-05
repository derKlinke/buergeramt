import json

from buergeramt.characters.ai_agent import OpenAIAgent
from buergeramt.characters.context_manager import ContextManager
from buergeramt.characters.message_builder import MessageBuilder
from buergeramt.rules.documents import DOCUMENTS


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

    def _validate_input(self, text: str, game_state) -> dict:
        """
        Use the AI agent to validate the player's input and return a structured result.
        The result should be a dict with at least:
            - valid: bool
            - message: str (explanation for the user)
            - intent: str (optional, e.g. 'request_document', 'provide_evidence', etc.)
            - document: str (optional, if a document is referenced)
            - evidence: list (optional, if evidence is referenced)
        """
        if not self.agent.has_api_key():
            # fallback: always valid, minimal info
            return {"valid": True, "message": "", "intent": None, "document": None, "evidence": []}

        # Provide the agent with all relevant context
        system_prompt = (
            "Du bist ein bürokratischer KI-Agent in einem deutschen Verwaltungs-Adventure-Spiel. "
            "Analysiere die Nutzereingabe im Kontext des aktuellen Spiels. "
            "Antworte ausschließlich mit JSON im folgenden Format: "
            "{ 'valid': bool, 'message': '<Erklärung>', 'intent': '<Absicht>', 'document': '<Dokument>', 'evidence': [<Beweise>] } "
            "\nErkläre im Feld 'message' ggf. warum die Eingabe ungültig ist oder was fehlt. "
            "Mögliche Werte für intent: 'request_document', 'provide_evidence', 'greeting', 'other'. "
            "Lasse 'document' und 'evidence' leer, falls nicht relevant."
        )
        game_state_info = self.message_builder._format_game_state(game_state)
        user_msg = {
            "role": "user",
            "content": f"Eingabe: '{text}'\nAktueller Spielstand: {game_state_info}"
        }
        try:
            resp = self.agent.chat([
                {"role": "system", "content": system_prompt},
                user_msg
            ], temperature=0)
            content = resp.choices[0].message.content.strip()
            # try to parse JSON from the response
            result = json.loads(content)
            # ensure required fields
            for key in ["valid", "message", "intent", "document", "evidence"]:
                if key not in result:
                    if key == "evidence":
                        result[key] = []
                    else:
                        result[key] = None
            return result
        except Exception:
            # fallback: always valid, minimal info
            return {"valid": True, "message": "", "intent": None, "document": None, "evidence": []}

    def respond(self, query, game_state):
        validation = self._validate_input(query, game_state)
        if not validation.get("valid", False):
            return validation["message"]
        try:
            if not self.agent.has_api_key():
                return self._fallback_response(query, game_state)
            messages = self.build_messages(query, game_state)
            action_system_message = {
                "role": "system",
                "content": """
                As a bureaucrat, you can take specific actions based on game rules. You should:
                1. Determine if a user is asking for a specific document that you can provide
                2. Check if a user is showing evidence (like ID or forms)
                3. Decide if you should redirect them to another department
                When responding, you should remain in character as a German bureaucrat.
                Keep your responses under 100 words.
                """,
            }
            messages.append(action_system_message)
            response = self.agent.chat(messages)
            ai_response = response.choices[0].message.content.strip()
            self.context_manager.add_exchange(query, ai_response)
            # Optionally, you could return both the AI response and the validation dict for game logic
            return ai_response
        except Exception as e:
            print(f"API Error: {e}")
            return self._fallback_response(query, game_state)

    def check_requirements(self, document, game_state):
        try:
            if not self.agent.has_api_key():
                return super().check_requirements(document, game_state)
            state_info = self.message_builder._format_game_state(game_state)
            prompt = f"""
            As {self.name}, you need to decide if the user meets requirements for the document: {document}.

            Game state: {state_info}

            Document requirements: {DOCUMENTS[document]['requirements']}

            Based on your bureaucratic nature and the game rules, do they meet all requirements?

            Respond with \"yes\" or \"no\" followed by a brief reason.
            """
            response = self.agent.chat([
                {"role": "user", "content": prompt}
            ], max_tokens=100, temperature=0.5)
            ai_response = response.choices[0].message.content.strip().lower()
            if ai_response.startswith("yes"):
                return True, "alle Voraussetzungen erfüllt"
            else:
                reason = ai_response.split("no")[1].strip() if "no" in ai_response else "ungenügende Dokumentation"
                return False, reason
        except Exception as e:
            print(f"API Error in check_requirements: {e}")
            return super().check_requirements(document, game_state)

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
