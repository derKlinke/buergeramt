import time

from buergeramt.engine.agent_router import AgentRouter
from buergeramt.rules import *
from buergeramt.utils.game_logger import get_logger


class GameEngine:
    """Main game engine class handling the game loop and state"""

    def __init__(self, use_ai_characters: bool = True):
        # Initialize logger
        self.logger = get_logger()
        self.logger.logger.info("=== Starting new game session ===")
        
        # Initialize game state
        self.game_state = GameState()
        self.use_ai_characters = True
        
        try:
            self.agent_router = AgentRouter(self.game_state)
            message = "Bürokratensimulation mit KI-Charakteren gestartet. Viel Erfolg!"
            print(message)
            self.logger.logger.info(message)
        except Exception as e:
            error_msg = f"Fehler beim Initialisieren der KI-Charaktere: {e}"
            print(error_msg)
            print("Das Spiel kann nicht gestartet werden.")
            self.logger.log_error(e, "Game initialization")
            self.game_over = True
            return
            
        self.game_over = False
        self.win_condition = False
        self.logger.logger.info("Game engine initialized successfully")

    def start_game(self):
        """Start the game with an introduction"""
        self._print_styled("=== WILLKOMMEN ZUM SCHENKUNGSSTEUERABENTEUER ===", "title")
        self._print_styled("Sie versuchen eine Schenkungssteuer beim Finanzamt anzumelden.", "normal")
        self._print_styled("Viel Glück... Sie werden es brauchen!", "normal")

        # Show more helpful instructions
        self._print_styled("\nTipps zum Spielen:", "hint")
        self._print_styled("• Sprechen Sie mit den Beamten über 'Formulare', 'Anträge', 'Dokumente'", "hint")
        self._print_styled(
            "• Zeigen Sie Ausweise und Unterlagen durch Angabe von 'Personalausweis', 'Urkunde', etc.", "hint"
        )

        self._print_styled("• Wechseln Sie zwischen Abteilungen mit Befehlen wie 'Ich möchte zu Herrn Weber'", "hint")
        self._print_styled("• Drücken Sie Ihre Frustration aus - manchmal führt Chaos zu überraschenden Ergebnissen", "hint")
        self._print_styled(
            "• Fragen Sie nach konkreten Dokumenten wie 'Schenkungsanmeldung' oder 'Wertermittlung'", "hint"
        )
        self._print_styled(
            "• Nutzen Sie Slash-Befehle wie /hilfe, /status, /beenden oder /gehe_zu <Name> für wichtige Aktionen",
            "hint",
        )

        # Show an example
        self._print_styled(
            "\nBeispiel: 'Ich möchte eine Schenkungssteuer anmelden und habe meinen Personalausweis dabei.'", "italic"
        )

        time.sleep(1)
        self._print_styled("\nSie betreten das Finanzamt...", "italic")
        time.sleep(1)

        # First bureaucrat introduces themselves
        self._print_styled(f"\n{self.agent_router.get_active_bureaucrat().introduce()}", "bureaucrat")
        self._print_styled("Wie kann ich Ihnen behilflich sein?", "bureaucrat")

    def show_help(self):
        """Show help information"""
        self._print_styled("\n=== HILFE ZUM SPIEL ===", "title")
        self._print_styled(
            "In diesem Spiel versuchen Sie, eine Schenkungssteuer anzumelden. Dafür müssen Sie:", "normal"
        )
        self._print_styled("1. Dokumente sammeln (Schenkungsanmeldung, Wertermittlung, etc.)", "hint")
        self._print_styled("2. Nachweise einreichen (Personalausweis, Notarielle Urkunde, etc.)", "hint")
        self._print_styled("3. Zwischen verschiedenen Abteilungen wechseln", "hint")
        self._print_styled("4. Mit den Bürokraten interagieren", "hint")

        self._print_styled("\nAktuelle Informationen:", "normal")
        self._print_styled(f"• Sie sind derzeit in der Abteilung: {self.game_state.current_department}", "info")
        self._print_styled(f"• Ihr aktueller Beamter ist: {self.agent_router.get_active_bureaucrat().name}", "info")

        # Show collected documents
        if self.game_state.collected_documents:
            docs = ", ".join(list(self.game_state.collected_documents.keys()))
            self._print_styled(f"• Gesammelte Dokumente: {docs}", "info")
        else:
            self._print_styled("• Sie haben noch keine Dokumente gesammelt", "info")

        # Show provided evidence
        if self.game_state.evidence_provided:
            evidence = ", ".join(list(self.game_state.evidence_provided.keys()))
            self._print_styled(f"• Eingereichte Nachweise: {evidence}", "info")
        else:
            self._print_styled("• Sie haben noch keine Nachweise eingereicht", "info")

        # Give a hint about what to do next
        self._print_styled("\nVorschlag für den nächsten Schritt:", "normal")
        self._suggest_next_step()

    def switch_agent(self, agent_name: str) -> bool:
        return self.agent_router.switch_agent(agent_name, print_styled=self._print_styled)

    def _suggest_next_step(self):
        """Suggest what the player should do next based on their progress"""
        # If player has no evidence yet
        if not self.game_state.evidence_provided:
            self._print_styled("Zeigen Sie Ihren Ausweis vor: 'Hier ist mein Personalausweis'", "hint")
            self._print_styled(
                "Und reichen Sie Details zur Schenkung ein: 'Ich habe eine notarielle Urkunde zur Schenkung'", "hint"
            )
            return

        # If player has some evidence but no documents
        if not self.game_state.collected_documents:
            if self.game_state.current_department == "Erstbearbeitung":
                if (
                    "valid_id" in self.game_state.evidence_provided
                    and "gift_details" in self.game_state.evidence_provided
                ):
                    self._print_styled(
                        "Fragen Sie nach der Schenkungsanmeldung: 'Ich möchte eine Schenkungsanmeldung beantragen'",
                        "hint",
                    )
                else:
                    missing = []
                    for evidence_id in ["valid_id", "gift_details"]:
                        if evidence_id not in self.game_state.evidence_provided:
                            missing.append(self._get_user_friendly_evidence_name(evidence_id))
                    self._print_styled(f"Reichen Sie zuerst folgende Nachweise ein: {', '.join(missing)}", "hint")
            else:
                self._print_styled(f"Gehen Sie zur Abteilung Erstbearbeitung: 'Ich möchte zu Herrn Schmidt'", "hint")
            return

        # If player has Schenkungsanmeldung but no Wertermittlung
        if (
            "Schenkungsanmeldung" in self.game_state.collected_documents
            and "Wertermittlung" not in self.game_state.collected_documents
        ):
            if self.game_state.current_department != "Fachprüfung":
                self._print_styled("Gehen Sie zur Abteilung Fachprüfung: 'Ich möchte zu Frau Müller'", "hint")
            else:
                if "market_comparison" not in self.game_state.evidence_provided:
                    friendly_name = self._get_user_friendly_evidence_name("market_comparison")
                    self._print_styled(
                        f"Reichen Sie eine {friendly_name} ein: 'Ich habe eine {friendly_name}'", "hint"
                    )
                if "expert_opinion" not in self.game_state.evidence_provided:
                    friendly_name = self._get_user_friendly_evidence_name("expert_opinion")
                    self._print_styled(f"Reichen Sie ein {friendly_name} ein: 'Hier ist mein {friendly_name}'", "hint")
                if (
                    "market_comparison" in self.game_state.evidence_provided
                    and "expert_opinion" in self.game_state.evidence_provided
                ):
                    self._print_styled(
                        "Fragen Sie nach der Wertermittlung: 'Kann ich jetzt die Wertermittlung bekommen?'", "hint"
                    )
            return

        # If player has Wertermittlung but no Freibetragsbescheinigung
        if (
            "Wertermittlung" in self.game_state.collected_documents
            and "Freibetragsbescheinigung" not in self.game_state.collected_documents
        ):
            if self.game_state.current_department != "Abschlussstelle":
                self._print_styled("Gehen Sie zur Abteilung Abschlussstelle: 'Ich möchte zu Herrn Weber'", "hint")
            else:
                missing = []
                for evidence_id in ["relationship_proof", "previous_gifts", "steuernummer"]:
                    if evidence_id not in self.game_state.evidence_provided:
                        friendly_name = self._get_user_friendly_evidence_name(evidence_id)
                        missing.append(friendly_name)

                if missing:
                    self._print_styled(f"Reichen Sie folgende Nachweise ein: {', '.join(missing)}", "hint")
                else:
                    self._print_styled(
                        "Fragen Sie nach der Freibetragsbescheinigung: 'Ich möchte eine Freibetragsbescheinigung'",
                        "hint",
                    )
            return

        # If player has most documents but not Zahlungsaufforderung
        if (
            "Freibetragsbescheinigung" in self.game_state.collected_documents
            and "Zahlungsaufforderung" not in self.game_state.collected_documents
        ):
            if self.game_state.current_department != "Erstbearbeitung":
                self._print_styled("Gehen Sie zurück zur Erstbearbeitung: 'Ich möchte zu Herrn Schmidt'", "hint")
            else:
                self._print_styled(
                    "Fragen Sie nach der Zahlungsaufforderung: 'Ich möchte die Zahlungsaufforderung'", "hint"
                )
            return

        # If player has all documents
        if "Zahlungsaufforderung" in self.game_state.collected_documents:
            if self.game_state.current_department != "Abschlussstelle":
                self._print_styled("Gehen Sie zur Abschlussstelle: 'Ich möchte zu Herrn Weber'", "hint")
            else:
                self._print_styled("Schließen Sie den Vorgang ab: 'Ich möchte den Vorgang abschließen'", "hint")
            return

    def process_input(self, user_input: str) -> bool:
        """Process user input and update game state using AI agent structured output"""
        if getattr(self, "game_over", True):
            return False
            
        # Log the user input
        self.logger.log_user_input(user_input)

        # Check for winning condition
        if self.check_win_condition():
            win_message = "\n=== HERZLICHEN GLÜCKWUNSCH! ==="
            self._print_styled(win_message, "title")
            self.logger.logger.info(win_message)
            
            success_msg = "Sie haben es tatsächlich geschafft! Die Schenkungssteuer wurde bewilligt."
            self._print_styled(success_msg, "success")
            
            stats_msg = f"Sie haben {self.game_state.attempts} Versuche gebraucht und Ihre Frustration erreichte maximal Level {self.game_state.frustration_level}."
            self._print_styled(stats_msg, "italic")
            self.logger.logger.info(f"GAME COMPLETED - Attempts: {self.game_state.attempts}, Max Frustration: {self.game_state.frustration_level}")
            
            final_msg = "Sie dürfen jetzt den Brief mit dem Steuerbescheid in 4-6 Wochen erwarten."
            self._print_styled(final_msg, "bureaucrat")
            
            self.game_over = True
            self.win_condition = True
            self.logger.logger.info("=== Game session completed successfully ===")
            return False

        self.game_state.attempts += 1
        self.logger.logger.debug(f"Processing input (attempt #{self.game_state.attempts}): {user_input}")

        # Get structured response from the active bureaucrat

        agent_result = self.agent_router.get_active_bureaucrat().respond(user_input, self.game_state)
        # Always expect an AgentResponse object
        response_text = agent_result.response_text
        actions = agent_result.actions
        self._print_styled(response_text, "bureaucrat")

        # Handle actions from the agent
        intent = actions.intent
        document = actions.document
        requirements_met = actions.requirements_met
        evidence = actions.evidence
        department = actions.department
        procedure = actions.procedure
        next_procedure = actions.next_procedure
        procedure_transition = actions.procedure_transition
        valid = actions.valid
        message = actions.message

        # Evidence submission
        if intent == "provide_evidence" and evidence:
            for ev in evidence or []:
                # Check if the evidence is already provided
                if ev in self.game_state.evidence_provided:
                    continue
                    
                # Map common evidence names to valid evidence IDs
                evidence_id = self._map_evidence_name_to_id(ev)
                if evidence_id:
                    # Map to a valid form for this evidence type
                    form = self._get_valid_form_for_evidence(evidence_id)
                    
                    # Get a user-friendly name for display
                    friendly_name = self._get_user_friendly_evidence_name(evidence_id)
                    
                    # Add the evidence with a valid form
                    if self.game_state.add_evidence(evidence_id, form):
                        self._print_styled(f"\nSie haben '{friendly_name}' als Nachweis eingereicht.", "success")
                    else:
                        # In case something went wrong with validation despite our mapping
                        self._print_styled(f"\nIhr Nachweis '{friendly_name}' konnte nicht akzeptiert werden.", "failure")
                else:
                    # No valid mapping found - CREATIVE HANDLING
                    # Let's add some whimsical bureaucratic randomness - sometimes random evidence
                    # actually works in strange bureaucracies!
                    import random
                    
                    # Generate a random chance based on frustration level (higher frustration = more chaos)
                    bizarre_chance = min(40, 10 + (self.game_state.frustration_level * 5))
                    
                    if random.randint(1, 100) <= bizarre_chance:
                        # Randomly select an evidence ID that's needed but not yet provided
                        missing_evidence = []
                        for doc_needs in self.game_state.get_missing_evidence().values():
                            missing_evidence.extend(doc_needs)
                        
                        # Remove duplicates
                        missing_evidence = list(set(missing_evidence))
                        
                        if missing_evidence:
                            # Randomly pick one of the missing evidence types
                            random_evidence_id = random.choice(missing_evidence)
                            form = self._get_valid_form_for_evidence(random_evidence_id)
                            friendly_name = self._get_user_friendly_evidence_name(random_evidence_id)
                            
                            # Add it to the player's evidence
                            if self.game_state.add_evidence(random_evidence_id, form):
                                self._print_styled(f"\nDurch einen glücklichen bürokratischen Zufall hat Ihr Nachweis '{ev}' " +
                                                 f"als '{friendly_name}' Anerkennung gefunden!", "success")
                                # Add a funny comment about bureaucracy
                                comments = [
                                    "Das Formular 27B/6 wurde offenbar korrekt ausgefüllt.",
                                    "Beamtenwillkür kann manchmal zu Ihren Gunsten ausfallen.",
                                    "Ein seltsamer Zufall, aber wir nehmen es an.",
                                    "Der Beamte nickt verwirrt, aber akzeptiert das Dokument.",
                                    "Irgendwie hat das funktioniert. Bürokratie ist unergründlich."
                                ]
                                self._print_styled(random.choice(comments), "italic")
                                return
                    
                    # Regular failure case
                    self._print_styled(f"\nDer Nachweis '{ev}' ist kein gültiges Dokument.", "failure")

        # Document request
        if intent == "request_document" and document:
            if requirements_met:
                if document not in self.game_state.collected_documents:
                    self.game_state.add_document(document)
                    self._print_styled(f"\nSie erhalten das Dokument '{document}'!", "success")
                    self.game_state.decrease_frustration(1)
                    
                    # Automatically advance procedure when document is received
                    # This is a common bureaucratic pattern - getting a document often moves you to the next stage
                    valid_next = self.game_state.get_valid_next_procedures()
                    if valid_next and procedure_transition is not True:
                        # Try to advance to the next logical procedure
                        if "Bescheiderteilung" in valid_next and document in ["Freibetragsbescheinigung"]:
                            self._handle_procedure_transition("Bescheiderteilung")
                        elif "Zahlungsaufforderung" in valid_next and document in ["Wertermittlung"]:
                            self._handle_procedure_transition("Zahlungsaufforderung")
                        elif "Abschluss" in valid_next and document in ["Zahlungsaufforderung"]:
                            self._handle_procedure_transition("Abschluss")
                        elif "Formularprüfung" in valid_next and document in ["Schenkungsanmeldung"]:
                            self._handle_procedure_transition("Formularprüfung")
            else:
                self._print_styled(f"\nSie können das Dokument '{document}' nicht erhalten: {message}", "failure")
                self.game_state.increase_frustration(1)

        # Department switch
        if intent == "switch_department" and department:
            if department != self.game_state.current_department:
                self._transition_to_department(department)
                
                # Automatically trigger a Weiterleitung procedure when switching departments
                if "Weiterleitung" in self.game_state.get_valid_next_procedures() and procedure_transition is not True:
                    self._handle_procedure_transition("Weiterleitung")
            else:
                self._print_styled("\nSie sind bereits in dieser Abteilung.", "italic")

        # Procedure transition
        if procedure_transition is True and next_procedure:
            self._handle_procedure_transition(next_procedure)

        # Invalid input
        if not valid:
            self._print_styled(f"\n{message}", "failure")
            self.game_state.increase_frustration(1)

        # Provide help if user seems stuck
        if self.game_state.attempts % 5 == 0:
            self._print_styled(
                "\nTipp: Tippen Sie 'hilfe' für Spieltipps oder 'status' für Ihren aktuellen Stand.", "hint"
            )

        self.game_state.update_progress()

        return True

    def check_win_condition(self) -> bool:
        """Check if the player has won the game"""
        # To win, player needs:
        # 1. The final Zahlungsaufforderung document
        # 2. To be in the final department
        # 3. To have completed the Bescheiderteilung procedure

        has_final_doc = "Zahlungsaufforderung" in self.game_state.collected_documents
        is_final_dept = self.game_state.current_department == "Abschlussstelle"
        # final procedure is Abschluss after payment request
        is_final_proc = self.game_state.current_procedure == "Abschluss"

        # Also allow winning if player has collected all documents and has high frustration
        all_docs = all(doc in self.game_state.collected_documents for doc in self.game_state.config.documents)
        is_frustrated = self.game_state.frustration_level > 8
        
        primary_condition_met = has_final_doc and is_final_dept and is_final_proc
        frustration_condition_met = all_docs and is_frustrated
        
        # Log the win condition check
        if primary_condition_met:
            self.logger.log_win_condition(True, "Regular win condition met - all requirements fulfilled")
        elif frustration_condition_met:
            self.logger.log_win_condition(True, f"Frustration win condition met - Level: {self.game_state.frustration_level}")
        else:
            missing = []
            if not has_final_doc:
                missing.append("Missing final document")
            if not is_final_dept:
                missing.append(f"Not in final department (current: {self.game_state.current_department})")
            if not is_final_proc:
                missing.append(f"Not in final procedure (current: {self.game_state.current_procedure})")
            self.logger.log_win_condition(False, f"Not met: {', '.join(missing)}")

        return primary_condition_met or frustration_condition_met
    
    def _transition_to_department(self, department):
        """Transition to a new department"""
        self.game_state.current_department = department
        success = self.switch_agent(self.game_state.get_bureaucrat_for_department(department))
        if success:
            self._print_styled(f"\nSie wechseln zur Abteilung {department}.", "italic")
            time.sleep(0.5)
            self._print_styled(f"\n{self.agent_router.get_active_bureaucrat().introduce()}", "bureaucrat")
        else:
            self._print_styled(f"\nFehler: Konnte nicht zur Abteilung {department} wechseln.", "failure")
        
    def _handle_procedure_transition(self, next_procedure: str):
        """Handle transition to a new bureaucratic procedure"""
        # Don't transition if already in this procedure
        if next_procedure == self.game_state.current_procedure:
            return
            
        # Try to transition using the game state's validation logic
        if self.game_state.transition_procedure(next_procedure):
            current_proc = self.game_state.config.procedures.get(next_procedure)
            if current_proc:
                self._print_styled(f"\n-- {current_proc.description} --", "procedure")
                
                # Provide contextual message based on procedure
                if next_procedure == "Antragstellung":
                    self._print_styled("Sie beginnen den Antragsprozess.", "italic")
                elif next_procedure == "Formularprüfung":
                    self._print_styled("Ihr Antrag wird nun geprüft.", "italic")
                elif next_procedure == "Nachweisanforderung":
                    self._print_styled("Sie müssen weitere Nachweise einreichen.", "italic")
                elif next_procedure == "Terminvereinbarung":
                    self._print_styled("Ein persönlicher Termin wird vereinbart.", "italic")
                elif next_procedure == "Weiterleitung":
                    self._print_styled("Ihr Vorgang wird an eine andere Abteilung weitergeleitet.", "italic")
                elif next_procedure == "Warteschleife":
                    self._print_styled("Ihr Antrag wird bearbeitet. Bitte haben Sie Geduld.", "italic")
                    # Warteschleife increases frustration by design
                    self.game_state.increase_frustration(1)
                elif next_procedure == "Bescheiderteilung":
                    self._print_styled("Eine Entscheidung zu Ihrem Antrag wird getroffen.", "italic")
                elif next_procedure == "Widerspruch":
                    self._print_styled("Sie legen Widerspruch gegen eine Entscheidung ein.", "italic")
                elif next_procedure == "Zahlungsaufforderung":
                    self._print_styled("Sie müssen nun die fälligen Gebühren bezahlen.", "italic")
                elif next_procedure == "Abschluss":
                    self._print_styled("Ihr Antrag wird abgeschlossen.", "italic")
                
                # Update progress when procedure changes
                self.game_state.update_progress()
                
                # Update context for the active bureaucrat if method exists
                if hasattr(self.agent_router.get_active_bureaucrat(), 'update_context'):
                    self.agent_router.get_active_bureaucrat().update_context(self.game_state)
        else:
            # If transition not allowed, might increase frustration (bureaucratic confusion)
            self._print_styled(f"\nDer Verfahrensschritt '{next_procedure}' ist derzeit nicht möglich.", "failure")
            self.game_state.increase_frustration(1)

    def _print_styled(self, text: str, style: str):
        """Print text with styling based on the style parameter"""
        # Log UI message
        self.logger.log_ui_message(text, style)

        # ANSI color codes
        COLORS = {
            "red": "\033[91m",
            "green": "\033[92m",
            "yellow": "\033[93m",
            "blue": "\033[94m",
            "magenta": "\033[95m",
            "cyan": "\033[96m",
            "white": "\033[97m",
            "reset": "\033[0m",
            "bold": "\033[1m",
            "italic": "\033[3m",
        }

        # Apply styling based on style parameter
        if style == "bureaucrat":
            print(f"{COLORS['cyan']}{COLORS['bold']}{text}{COLORS['reset']}")
        elif style == "success":
            print(f"{COLORS['green']}{text}{COLORS['reset']}")
        elif style == "failure":
            print(f"{COLORS['red']}{text}{COLORS['reset']}")
        elif style == "hint":
            print(f"{COLORS['yellow']}{text}{COLORS['reset']}")
        elif style == "italic":
            print(f"{COLORS['italic']}{text}{COLORS['reset']}")
        elif style == "title":
            print(f"{COLORS['magenta']}{COLORS['bold']}{text}{COLORS['reset']}")
        elif style == "info":
            print(f"{COLORS['blue']}{text}{COLORS['reset']}")
        elif style == "procedure":
            print(f"{COLORS['magenta']}{COLORS['bold']}{COLORS['italic']}{text}{COLORS['reset']}")
        else:  # normal
            print(text)

        # Small delay for better readability
        time.sleep(0.1)

    def _normalize_response(self, text: str) -> str:
        """Replace form codes and shorthand with full document names in AI responses."""
        # replace document codes (e.g., S-100) with names
        for doc_id, doc in self.game_state.config.documents.items():
            code = doc.code
            if code and code in text:
                text = text.replace(code, doc_id)
        # replace common shorthand
        text = text.replace("WE", "Wertermittlung")
        text = text.replace("FBB", "Freibetragsbescheinigung")
        return text
        
    def _map_evidence_name_to_id(self, evidence_name: str) -> str:
        """Map common evidence names to valid evidence IDs in the game config."""
        # First, check if the evidence_name is already a valid ID
        if evidence_name in self.game_state.config.evidence:
            self.logger.logger.debug(f"Evidence name '{evidence_name}' is already a valid ID")
            return evidence_name
            
        # Convert to lowercase for case-insensitive matching
        name_lower = evidence_name.lower()
        
        # Dictionary mapping common terms to evidence IDs
        evidence_mapping = {
            # valid_id mappings
            "personalausweis": "valid_id",
            "ausweis": "valid_id",
            "identitätsnachweis": "valid_id",
            "reisepass": "valid_id",
            "aufenthaltstitel": "valid_id",
            "id": "valid_id",
            
            # gift_details mappings
            "notarielle urkunde": "gift_details",
            "schenkungsdetails": "gift_details",
            "übergabeprotokoll": "gift_details",
            "bankbeleg": "gift_details",
            "eigentumsnachweis": "gift_details",
            "schenkungsurkunde": "gift_details",
            "geschenk": "gift_details",
            "schenkung": "gift_details",
            "kekse": "gift_details",  # Game-specific example (cookies as gift)
            
            # residence_proof mappings
            "meldebescheinigung": "residence_proof",
            "mietvertrag": "residence_proof",
            "grundbuchauszug": "residence_proof",
            "wohnsitznachweis": "residence_proof",
            "meldebestätigung": "residence_proof",
            "wohnort": "residence_proof",
            "adresse": "residence_proof",
            
            # market_comparison mappings
            "marktwertanalyse": "market_comparison",
            "marktanalyse": "market_comparison",
            "vergleichspreise": "market_comparison",
            "marktvergleich": "market_comparison",
            "marktwert": "market_comparison",
            "preisgutachten": "market_comparison",
            
            # expert_opinion mappings
            "gutachten": "expert_opinion",
            "sachverständigengutachten": "expert_opinion", 
            "wertgutachten": "expert_opinion",
            "expertenmeinung": "expert_opinion",
            "sachverständiger": "expert_opinion",
            "experte": "expert_opinion",
            
            # relationship_proof mappings
            "beziehungsnachweis": "relationship_proof",
            "freundschaftserklärung": "relationship_proof",
            "verwandtschaftsnachweis": "relationship_proof",
            "bekanntenkreis": "relationship_proof",
            "freundschaft": "relationship_proof",
            "beziehung": "relationship_proof",
            
            # previous_gifts mappings
            "frühere schenkungen": "previous_gifts",
            "eigenerklärung": "previous_gifts",
            "frühere steuerbescheide": "previous_gifts",
            "notarielle urkunden": "previous_gifts",
            "erklärung zu früheren schenkungen": "previous_gifts",
            "vorherige schenkungen": "previous_gifts",
            "frühere geschenke": "previous_gifts",
            
            # steuernummer mappings
            "steuernummer": "steuernummer",
            "steuer-id": "steuernummer",
            "steueridentifikationsnummer": "steuernummer",
            "steuer-identifikationsnummer": "steuernummer",
            "steuerbescheid": "steuernummer",
            "steuer-id mitteilung": "steuernummer",
            "steuer": "steuernummer"
        }
        
        # Check if any key in our mapping dictionary is contained in the evidence name
        for key, value in evidence_mapping.items():
            if key in name_lower:
                self.logger.logger.debug(f"Evidence mapping: '{evidence_name}' -> '{value}'")
                return value
                
        # Log when we can't map an evidence name
        self.logger.logger.warning(f"Could not map evidence name: '{evidence_name}'")
        return None
        
    def _get_valid_form_for_evidence(self, evidence_id: str) -> str:
        """Return a valid form for the given evidence ID."""
        # Get the evidence definition from the config
        if evidence_id in self.game_state.config.evidence:
            evidence_def = self.game_state.config.evidence[evidence_id]
            if evidence_def.acceptable_forms:
                # Return the first acceptable form
                form = evidence_def.acceptable_forms[0]
                self.logger.logger.debug(f"Using form '{form}' for evidence '{evidence_id}'")
                return form
                
        # Default fallback form - should not be reached if config is complete
        self.logger.logger.warning(f"No valid form found for evidence ID: '{evidence_id}'")
        return "Standardform"
        
    def _get_user_friendly_evidence_name(self, evidence_id: str) -> str:
        """Convert an evidence ID to a user-friendly name for display."""
        # Dictionary of user-friendly names for evidence IDs
        friendly_names = {
            "valid_id": "Personalausweis",
            "gift_details": "Schenkungsdetails",
            "residence_proof": "Wohnsitznachweis",
            "market_comparison": "Marktwertanalyse",
            "expert_opinion": "Gutachten",
            "relationship_proof": "Beziehungsnachweis",
            "previous_gifts": "Erklärung zu früheren Schenkungen",
            "steuernummer": "Steuernummer"
        }
        
        # Return the friendly name if available, otherwise return the ID
        return friendly_names.get(evidence_id, evidence_id)
