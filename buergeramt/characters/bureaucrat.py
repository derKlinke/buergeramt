from buergeramt.characters.agent import Agent
from buergeramt.characters.agent_response import AgentResponse
from buergeramt.characters.context_manager import ContextManager
from buergeramt.characters.message_builder import MessageBuilder
from buergeramt.utils.game_logger import get_logger


class Bureaucrat:
    def __init__(self, name, title, department, system_prompt, api_key=None):
        self.name = name
        self.title = title
        self.department = department
        self.system_prompt = system_prompt
        self.context_manager = ContextManager()
        self.agent = Agent(api_key=api_key)
        self.message_builder = MessageBuilder(self.system_prompt, self.context_manager)
        self.logger = get_logger()
        self.logger.logger.info(f"Initialized bureaucrat: {name}, {title} ({department})")
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
            "{ 'response_text': <text>, 'actions': { "
            "'intent': <intent>, 'document': <document>, 'requirements_met': <bool>, "
            "'evidence': <list>, 'department': <str>, 'procedure': <procedure>, 'next_procedure': <next_procedure>, "
            "'procedure_transition': <bool>, 'valid': <bool>, 'message': <str> } } "
            
            "Possible values for intent: 'request_document', 'provide_evidence', 'switch_department', "
            "'procedure_transition', 'greeting', 'other'. "
            
            "If the user requests a document, check if all requirements are met and set 'requirements_met' accordingly. "
            "If the user provides evidence, list it in 'evidence'. "
            "If the user wants to switch department, set 'department'. "
            
            "PROCEDURE HANDLING: "
            "If the user's interaction suggests a bureaucratic procedure change, set: "
            "- 'procedure_transition': true "
            "- 'next_procedure': to one of the valid next procedures from the current game state "
            "Valid next procedures are provided in the game state information. "
            "Look for keywords matching procedure descriptions to determine if a transition is appropriate. "
            
            "EVIDENCE HANDLING: "
            "When user provides evidence in their input, identify specific evidence types from this list: "
            "- valid_id: Personal identification (Personalausweis, Reisepass, Aufenthaltstitel) "
            "- gift_details: Gift documentation (notarielle Urkunde, Übergabeprotokoll, Bankbeleg) "
            "- residence_proof: Residence proof (Meldebescheinigung, Mietvertrag, Grundbuchauszug) "
            "- market_comparison: Market value evidence (Marktwertanalyse, Vergleichspreise) "
            "- expert_opinion: Expert valuation (Gutachten, Wertgutachten, Sachverständigengutachten) "
            "- relationship_proof: Relationship documentation (Freundschaftserklärung, Verwandtschaftsnachweis) "
            "- previous_gifts: Previous gifts declaration (Eigenerklärung, frühere Steuerbescheide) "
            "- steuernummer: Tax number documentation (Steuer-ID, Steuerbescheid) "
            
            "When user mentions evidence, identify the correct evidence ID from the list above and return it in the evidence field. "
            "Example: If user says 'Hier ist mein Personalausweis', return 'valid_id' in the evidence list. "
            
            "Each procedure has specific keywords and characteristics: "
            "- Antragstellung: Initial application submission - use when user starts a new process "
            "- Formularprüfung: Form verification - use when checking documents for correctness "
            "- Nachweisanforderung: Request for evidence - use when asking for specific documents "
            "- Terminvereinbarung: Scheduling appointments - use when discussing meeting times "
            "- Weiterleitung: Forwarding to other departments - use when redirecting the user "
            "- Warteschleife: Waiting period - use when the user must wait "
            "- Bescheiderteilung: Decision issuance - use when making official decisions "
            "- Widerspruch: Formal objection - use when user objects to decisions "
            "- Zahlungsaufforderung: Payment request - use when requesting payment "
            "- Abschluss: Process completion - use for finalizing the process "
            
            "If the input is invalid or incomplete, set 'valid' to false and explain in 'message'. "
            "Keep 'response_text' as your in-character reply to the user. "
            "If a field is not relevant, set it to null or an empty list."
        )
        game_state_info = game_state.get_formatted_gamestate()
        user_msg = {"role": "user", "content": f"Eingabe: '{query}'\nAktueller Spielstand: {game_state_info}"}
        try:
            messages = [{"role": "system", "content": system_instruction}, user_msg]
            
            # Log the AI prompt
            self.logger.log_ai_prompt(messages)
            
            # Make the API call
            completion = self.agent.chat_structured(
                messages=messages, response_format=AgentResponse, max_tokens=200, temperature=0
            )
            
            # Log the raw AI response
            self.logger.log_ai_response(completion)
            
            agent_response = completion.choices[0].message.parsed
            
            # Log the structured agent action
            self.logger.log_agent_action(agent_response.actions.dict())
            
            self.context_manager.add_exchange(query, agent_response.response_text)
            return agent_response
        except Exception as e:
            error_msg = f"API Error (structured): {e}"
            print(error_msg)
            self.logger.log_error(e, f"AI response error for '{query}' from {self.name}")
            raise RuntimeError("AI agent failed to respond.")

    def update_context(self, game_state):
        """Update the bureaucrat's context with current game state information"""
        # Get procedure information
        current_proc = game_state.current_procedure
        proc_desc = game_state.get_procedure_description() or "Unknown procedure"
        
        # Add a context note about the current procedure
        context_note = f"CURRENT PROCEDURE: {current_proc} - {proc_desc}"
        
        # Get keywords for the current procedure
        keywords = game_state.get_procedure_keywords()
        if keywords:
            keywords_str = ", ".join(keywords)
            context_note += f"\nKEYWORDS: {keywords_str}"
        
        # Get valid next procedures
        next_steps = game_state.get_valid_next_procedures()
        if next_steps:
            next_steps_str = ", ".join(next_steps)
            context_note += f"\nPOSSIBLE NEXT STEPS: {next_steps_str}"
        
        # Add this context note to the bureaucrat's memory
        self.context_manager.add_system_note(context_note)
    
    def give_hint(self, game_state):
        """Provide a helpful hint to the user based on current game state"""
        if not self.agent.has_api_key():
            raise RuntimeError("AI agent is not available: missing API key.")
        
        # Update context before giving hint
        self.update_context(game_state)
        
        state_info = game_state.get_formatted_gamestate()
        prompt = f"""
        As {self.name}, provide a hint to the user about their next steps.

        Game state: {state_info}

        You are currently in the '{game_state.current_procedure}' procedure.
        Valid next procedures are: {', '.join(game_state.get_valid_next_procedures())}
        
        Based on your bureaucratic personality, what hint would you give?
        Keep it brief (1-2 sentences) and in character.
        """
        try:
            # Log the hint prompt
            self.logger.log_ai_prompt([{"role": "user", "content": prompt}])
            
            # Get hint from AI
            response = self.agent.chat([{"role": "user", "content": prompt}], max_tokens=100, temperature=0.7)
            
            # Log the hint response
            self.logger.log_ai_response(response)
            
            hint = response.choices[0].message.content.strip()
            self.logger.logger.info(f"HINT from {self.name}: {hint}")
            
            return hint
        except Exception as e:
            error_msg = f"API Error in give_hint: {e}"
            print(error_msg)
            self.logger.log_error(e, "give_hint")
            raise RuntimeError("AI agent failed to provide a hint.")
