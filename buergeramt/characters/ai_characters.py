import json
import os
from typing import Tuple

from openai import OpenAI

from buergeramt.game_rules import DOCUMENTS

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


class Bureaucrat:
    def __init__(self, name, title, department, system_prompt, example_interactions=None):
        self.name = name
        self.title = title
        self.department = department
        self.system_prompt = system_prompt
        self.example_interactions = example_interactions or []
        self.conversation_history = []
        self.model = "gpt-3.5-turbo"
        try:
            client.chat.completions.create(model="gpt-4", messages=[{"role": "user", "content": "test"}], max_tokens=1)
            self.model = "gpt-4"
            print(f"Using {self.model} for {name}")
        except Exception:
            print(f"Using {self.model} for {name}")

    def introduce(self) -> str:
        return f"Mein Name ist {self.name}, {self.title} der Abteilung {self.department}."

    def build_messages(self, query, game_state):
        """Build the messages for the API call with rich context"""
        # Start with the system prompt
        messages = [{"role": "system", "content": self.system_prompt}]

        # Add examples if this is a new conversation
        if len(self.conversation_history) < 2:
            for example in self.example_interactions:
                messages.append({"role": "user", "content": example["user"]})
                messages.append({"role": "assistant", "content": example["assistant"]})

        # Add recent conversation history (limited to prevent context overflow)
        # We'll use the most recent exchanges to maintain continuity
        messages.extend(self.conversation_history[-6:])

        # Add game state context with structured information
        game_state_info = self._format_game_state(game_state)
        messages.append({"role": "system", "content": f"Current game state: {game_state_info}"})

        # Add information about what the user needs for the current stage
        stage_guidance = self._get_stage_guidance(game_state)
        if stage_guidance:
            messages.append({"role": "system", "content": stage_guidance})

        # Add the current query
        messages.append({"role": "user", "content": query})

        return messages

    def _format_game_state(self, game_state):
        """Format detailed game state information for the AI"""
        collected_documents = list(game_state.collected_documents.keys())
        evidence_provided = list(game_state.evidence_provided.keys())

        # Build a richer state description
        state_info = {
            "current_department": game_state.current_department,
            "current_procedure": game_state.current_procedure,
            "collected_documents": collected_documents,
            "evidence_provided": evidence_provided,
            "attempts": game_state.attempts,
            "frustration_level": game_state.frustration_level,
            "progress": game_state.progress,
            # Add information about what documents this department can issue
            "department_documents": [
                doc for doc, data in DOCUMENTS.items() if data["department"] == game_state.current_department
            ],
            # Add information about missing evidence for documents
            "missing_evidence": self._get_missing_evidence(game_state),
        }

        return json.dumps(state_info, indent=2)

    def _get_missing_evidence(self, game_state):
        """Get missing evidence for each document"""
        missing = {}
        for doc_name, doc_data in DOCUMENTS.items():
            if doc_name not in game_state.collected_documents:
                required = doc_data["requirements"]
                missing_reqs = [req for req in required if req not in game_state.evidence_provided]
                if missing_reqs:
                    missing[doc_name] = missing_reqs
        return missing

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

    def _validate_input(self, text: str) -> Tuple[bool, str]:
        """Validate the player's input for politeness, completeness, and specific content (form names/codes)."""
        # skip validation if no API key
        if not client.api_key:
            return True, ""
        # instruct validation assistant
        system_msg = {
            "role": "system",
            "content": (
                "Du bist ein Assistent, der die Eingabe eines Nutzers im Kontext eines bürokratischen Spiels "
                "prüft. Überprüfe, ob der Satz vollständig, höflich und in korrektem Deutsch formuliert ist und "
                "ob die Anfrage spezifische Formulare/Dokumentennamen oder -codes enthält, falls sie danach fragt. "
                "Antworte nur mit JSON: {'valid': bool, 'message': '<Erklärung>'}."
            ),
        }
        user_msg = {"role": "user", "content": f'Überprüfe: "{text}"'}
        try:
            resp = client.chat.completions.create(model=self.model, messages=[system_msg, user_msg], temperature=0)
            content = resp.choices[0].message.content.strip()
            result = json.loads(content)
        except Exception:
            return True, ""
        if not result.get("valid", False):
            return False, result.get(
                "message", "Bitte formuliere deine Anfrage vollständig, höflich und gib genaue Formulardaten an."
            )
        return True, ""

    def respond(self, query, game_state):
        """Generate a dynamic response using OpenAI API"""
        # validate player input before generating a response
        valid, message = self._validate_input(query)
        if not valid:
            return message
        try:
            if not client.api_key:
                # Fallback if no API key
                return self._fallback_response(query, game_state)

            messages = self.build_messages(query, game_state)

            # Tell the model what actions it can take
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

            # Make API call
            response = client.chat.completions.create(
                model=self.model, messages=messages, max_tokens=200, temperature=0.7
            )

            # Extract response
            ai_response = response.choices[0].message.content.strip()

            # Update conversation history
            self.conversation_history.append({"role": "user", "content": query})
            self.conversation_history.append({"role": "assistant", "content": ai_response})

            return ai_response

        except Exception as e:
            print(f"API Error: {e}")
            return self._fallback_response(query, game_state)

    def check_requirements(self, document, game_state):
        """Use AI to decide if requirements are met for a document"""
        try:
            if not client.api_key:
                # If no API key, fall back to original implementation
                return super().check_requirements(document, game_state)

            # Format game state
            state_info = self._format_game_state(game_state)

            # Create a specific prompt for this decision
            prompt = f"""
            As {self.name}, you need to decide if the user meets requirements for the document: {document}.

            Game state: {state_info}

            Document requirements: {DOCUMENTS[document]['requirements']}

            Based on your bureaucratic nature and the game rules, do they meet all requirements?

            Respond with "yes" or "no" followed by a brief reason.
            """

            # Make API call
            response = client.chat.completions.create(
                model=self.model, messages=[{"role": "user", "content": prompt}], max_tokens=100, temperature=0.5
            )

            # Extract response
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
        """Generate a hint using AI"""
        try:
            if not client.api_key:
                # Fallback if no API key
                return self._fallback_hint(game_state)

            # Format game state
            state_info = self._format_game_state(game_state)

            # Create a specific prompt for the hint
            prompt = f"""
            As {self.name}, provide a hint to the user about their next steps.

            Game state: {state_info}

            Based on your bureaucratic personality, what hint would you give?
            Keep it brief (1-2 sentences) and in character.
            """

            # Make API call
            response = client.chat.completions.create(
                model=self.model, messages=[{"role": "user", "content": prompt}], max_tokens=100, temperature=0.7
            )

            # Extract response
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
