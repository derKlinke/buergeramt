import random
import time
from typing import List

from buergeramt.characters import *
from buergeramt.rules import *


class GameEngine:
    def switch_agent(self, agent_name: str) -> bool:
        """Public method to switch to a different agent/department by agent name. Returns True if successful."""
        # Normalize input for matching
        name = agent_name.strip().lower()
        # Map possible names to departments
        name_to_dept = {
            "herr schmidt": "Erstbearbeitung",
            "schmidt": "Erstbearbeitung",
            "erstbearbeitung": "Erstbearbeitung",
            "frau müller": "Fachprüfung",
            "mueller": "Fachprüfung",
            "müller": "Fachprüfung",
            "fachprüfung": "Fachprüfung",
            "herr weber": "Abschlussstelle",
            "weber": "Abschlussstelle",
            "abschlussstelle": "Abschlussstelle",
        }
        # Try to match
        for key, dept in name_to_dept.items():
            if key in name:
                if dept == self.game_state.current_department:
                    self._print_styled("\nSie sind bereits in dieser Abteilung.", "italic")
                    return True
                self._transition_to_department(dept)
                return True
        # Fallback: try direct department match
        for dept in self.bureaucrats:
            if dept.lower() in name:
                if dept == self.game_state.current_department:
                    self._print_styled("\nSie sind bereits in dieser Abteilung.", "italic")
                    return True
                self._transition_to_department(dept)
                return True
        return False
    """Main game engine class handling the game loop and state"""

    def __init__(self, use_ai_characters: bool = True):
        self.game_state = GameState()

        # Always use AI characters by default
        self.use_ai_characters = True

        try:
            self.bureaucrats = {
                "Erstbearbeitung": HerrSchmidt(),
                "Fachprüfung": FrauMueller(),
                "Abschlussstelle": HerrWeber(),
            }
            print("Bürokratensimulation mit KI-Charakteren gestartet. Viel Erfolg!")
        except Exception as e:
            print(f"Fehler beim Initialisieren der KI-Charaktere: {e}")
            print("Das Spiel kann nicht gestartet werden.")
            self.game_over = True
            return

        # Set the active bureaucrat
        self.active_bureaucrat = self.bureaucrats["Erstbearbeitung"]
        self.game_state.current_department = "Erstbearbeitung"

        # Game flow tracking
        self.game_over = False
        self.win_condition = False

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
        self._print_styled("• Drücken Sie Ihre Frustration aus, wenn Sie möchten", "hint")
        self._print_styled("• Fragen Sie nach konkreten Dokumenten wie 'Schenkungsanmeldung' oder 'Wertermittlung'", "hint")
        self._print_styled("• Nutzen Sie Slash-Befehle wie /hilfe, /status, /beenden oder /gehe_zu <Name> für wichtige Aktionen", "hint")

        # Show an example
        self._print_styled(
            "\nBeispiel: 'Ich möchte eine Schenkungssteuer anmelden und habe meinen Personalausweis dabei.'", "italic"
        )

        time.sleep(1)
        self._print_styled("\nSie betreten das Finanzamt...", "italic")
        time.sleep(1)

        # First bureaucrat introduces themselves
        self._print_styled(f"\n{self.active_bureaucrat.introduce()}", "bureaucrat")
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
        self._print_styled(f"• Ihr aktueller Beamter ist: {self.active_bureaucrat.name}", "info")

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
                    if "valid_id" not in self.game_state.evidence_provided:
                        missing.append("Personalausweis")
                    if "gift_details" not in self.game_state.evidence_provided:
                        missing.append("Schenkungsdetails")
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
                    self._print_styled(
                        "Reichen Sie eine Marktwertanalyse ein: 'Ich habe eine Marktwertanalyse'", "hint"
                    )
                if "expert_opinion" not in self.game_state.evidence_provided:
                    self._print_styled("Reichen Sie ein Wertgutachten ein: 'Hier ist mein Wertgutachten'", "hint")
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
                if "relationship_proof" not in self.game_state.evidence_provided:
                    missing.append("Beziehungsnachweis (z.B. Freundschaftserklärung)")
                if "previous_gifts" not in self.game_state.evidence_provided:
                    missing.append("Erklärung zu früheren Schenkungen")
                if "steuernummer" not in self.game_state.evidence_provided:
                    missing.append("Steuernummer")

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

        # Check for winning condition
        if self.check_win_condition():
            self._print_styled("\n=== HERZLICHEN GLÜCKWUNSCH! ===", "title")
            self._print_styled("Sie haben es tatsächlich geschafft! Die Schenkungssteuer wurde bewilligt.", "success")
            self._print_styled(
                f"Sie haben {self.game_state.attempts} Versuche gebraucht und Ihre Frustration erreichte maximal Level {self.game_state.frustration_level}.",
                "italic",
            )
            self._print_styled(
                "Sie dürfen jetzt den Brief mit dem Steuerbescheid in 4-6 Wochen erwarten.", "bureaucrat"
            )
            self.game_over = True
            self.win_condition = True
            return False

        self.game_state.attempts += 1

        # Get structured response from the active bureaucrat

        agent_result = self.active_bureaucrat.respond(user_input, self.game_state)
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
        valid = actions.valid
        message = actions.message

        # Evidence submission
        if intent == "provide_evidence" and evidence:
            for ev in (evidence or []):
                # Accept evidence if not already provided
                if ev not in self.game_state.evidence_provided:
                    self.game_state.add_evidence(ev, "(Form über KI)")
                    self._print_styled(f"\nSie haben '{ev}' als Nachweis eingereicht.", "success")

        # Document request
        if intent == "request_document" and document:
            if requirements_met:
                if document not in self.game_state.collected_documents:
                    self.game_state.add_document(document)
                    self._print_styled(f"\nSie erhalten das Dokument '{document}'!", "success")
                    self.game_state.decrease_frustration(1)
            else:
                self._print_styled(f"\nSie können das Dokument '{document}' nicht erhalten: {message}", "failure")
                self.game_state.increase_frustration(1)

        # Department switch
        if intent == "switch_department" and department:
            if department != self.game_state.current_department:
                self._transition_to_department(department)
            else:
                self._print_styled("\nSie sind bereits in dieser Abteilung.", "italic")

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

    def _bureaucratic_interruption(self):
        """Random bureaucratic interruption for added frustration and realism"""
        interruptions = [
            (
                "Moment! Es ist jetzt Mittagspause!",
                "Der Beamte verschwindet plötzlich hinter einer Tür mit einem 'Pause' Schild.",
            ),
            (
                "Oh, das System ist gerade abgestürzt!",
                "Der Beamte starrt frustriert auf den Bildschirm und tippt wahllos auf der Tastatur herum.",
            ),
            (
                "Einen Moment, bitte. Dringendes Telefonat!",
                "Der Beamte nimmt ein Telefonat entgegen und ignoriert Sie für einige Minuten.",
            ),
            (
                "Es tut mir leid, aber Ihr Vorgang muss neu nummeriert werden.",
                "Der Beamte beginnt, alle Ihre Unterlagen neu zu sortieren.",
            ),
            (
                "Bitte warten, ich muss kurz mit meinem Vorgesetzten sprechen.",
                "Der Beamte verschwindet mit Ihren Unterlagen in einem Nebenzimmer.",
            ),
        ]

        interruption, description = random.choice(interruptions)
        self._print_styled(f"\n{self.active_bureaucrat.name}: {interruption}", "bureaucrat")
        self._print_styled(description, "italic")

        time.sleep(2)  # Dramatic pause

        # 30% chance to actually change departments after an interruption
        if random.random() < 0.3:
            options = [dept for dept in self.bureaucrats.keys() if dept != self.game_state.current_department]
            target_dept = random.choice(options)
            reason = random.choice(
                [
                    "Ihr Anliegen muss woanders bearbeitet werden",
                    "für diesen Fall ist eine andere Abteilung zuständig",
                    "aufgrund einer neuen Dienstanweisung",
                    "wegen Systemumstellung",
                    "weil das Verfahren geändert wurde",
                ]
            )

            self._print_styled(
                f"\n{self.active_bureaucrat.name}: Sie müssen zur Abteilung {target_dept}, {reason}.", "bureaucrat"
            )
            self._transition_to_department(target_dept)
        else:
            self._print_styled("\nWir können jetzt fortfahren.", "bureaucrat")

    def _transition_to_department(self, department: str):
        """Transition the player to a new department"""
        if department == self.game_state.current_department:
            self._print_styled("\nSie sind bereits in dieser Abteilung.", "italic")
            return

        # Show transition text
        self._print_styled(f"\nSie verlassen das Büro von {self.active_bureaucrat.name}...", "italic")
        time.sleep(1)
        self._print_styled(f"Sie gehen zum Büro der Abteilung {department}...", "italic")
        time.sleep(1)

        # Update game state
        self.game_state.current_department = department
        self.active_bureaucrat = self.bureaucrats[department]

        # New bureaucrat introduces themselves
        self._print_styled(f"\n{self.active_bureaucrat.introduce()}", "bureaucrat")

        # Bureaucrat mentions something about the player's current state
        if len(self.game_state.collected_documents) > 0:
            doc_list = ", ".join(list(self.game_state.collected_documents.keys()))
            self._print_styled(f"Ich sehe, Sie haben bereits folgende Dokumente: {doc_list}.", "bureaucrat")
        else:
            self._print_styled("Was kann ich für Sie tun?", "bureaucrat")

    def _process_document_acquisition(self, document_names: List[str]):
        """Process the player attempting to acquire documents"""
        for document_name in document_names:
            # Check if the player meets the requirements
            can_receive, reason = self.active_bureaucrat.check_requirements(document_name, self.game_state)

            if can_receive:
                self._print_styled(f"\nSie erhalten das Dokument '{document_name}'!", "success")
                self.game_state.add_document(document_name)
                self.game_state.decrease_frustration(1)
                # advance game procedure to next stage
                next_proc = {
                    "Schenkungsanmeldung": "Formularprüfung",
                    "Wertermittlung": "Bescheiderteilung",
                    "Freibetragsbescheinigung": "Zahlungsaufforderung",
                    "Zahlungsaufforderung": "Abschluss",
                }
                if document_name in next_proc:
                    self.game_state.set_procedure(next_proc[document_name])

                # Suggest next steps
                if document_name == "Schenkungsanmeldung":
                    self._print_styled(
                        "Als nächstes benötigen Sie eine Wertermittlung von der Abteilung Fachprüfung.", "hint"
                    )
                elif document_name == "Wertermittlung":
                    self._print_styled(
                        "Jetzt könnten Sie eine Freibetragsbescheinigung von der Abschlussstelle beantragen.", "hint"
                    )
                elif document_name == "Freibetragsbescheinigung":
                    self._print_styled(
                        "Mit diesen Dokumenten können Sie zur Erstbearbeitung zurückkehren, um die finale Zahlungsaufforderung zu erhalten.",
                        "hint",
                    )
            else:
                self._print_styled(f"\nSie können das Dokument '{document_name}' nicht erhalten: {reason}", "failure")
                self.game_state.increase_frustration(1)

                # Suggest what they need
                requirements = DOCUMENTS[document_name]["requirements"]
                missing = [req for req in requirements if req not in self.game_state.evidence_provided]
                if missing:
                    self._print_styled(f"Sie benötigen noch: {', '.join(missing)}.", "hint")

                    # Sometimes suggest a different department
                    if random.random() < 0.5:
                        dept = DOCUMENTS[document_name]["department"]
                        if dept != self.game_state.current_department:
                            self._print_styled(
                                f"Eigentlich ist für dieses Dokument die Abteilung {dept} zuständig.", "hint"
                            )

    def _should_redirect_based_on_conversation(self, user_input: str, response: str) -> bool:
        """Determine if we should redirect the player based on conversation context"""
        # Increase redirect chance as frustration increases
        base_chance = 0.05  # 5% base chance
        frustration_modifier = self.game_state.frustration_level * 0.02  # +2% per frustration level
        stuck_modifier = min(0.3, (self.game_state.attempts % 10) * 0.03)  # +3% per attempt up to 30%

        redirect_chance = base_chance + frustration_modifier + stuck_modifier

        # Special keywords in user input can trigger redirects
        if any(keyword in user_input.lower() for keyword in ["hilfe", "weiter", "stecke fest", "nächster", "anderer"]):
            redirect_chance += 0.2

        # If player has been in the same department for too long
        if self.game_state.attempts > 5 and self.game_state.attempts % 7 == 0:
            redirect_chance = 0.8  # 80% chance

        return random.random() < redirect_chance

    def _dynamic_redirect(self):
        """Redirect the player to another department based on game context"""
        current_dept = self.game_state.current_department

        # Determine where to send the player based on their progress
        # This creates the bureaucratic circle feel - always being sent somewhere else
        target_dept = None

        # If they have no documents yet, keep them in Erstbearbeitung
        if len(self.game_state.collected_documents) == 0:
            if current_dept != "Erstbearbeitung":
                target_dept = "Erstbearbeitung"
                reason = "Sie müssen erst den Grundantrag stellen"
            else:
                # Even in Erstbearbeitung, they might get redirected if they're stuck
                if self.game_state.attempts > 5:
                    target_dept = "Fachprüfung"
                    reason = "für die Vorabwertermittlung"

        # If they have the initial document but not the valuation
        elif (
            "Schenkungsanmeldung" in self.game_state.collected_documents
            and "Wertermittlung" not in self.game_state.collected_documents
        ):
            if current_dept != "Fachprüfung":
                target_dept = "Fachprüfung"
                reason = "für die Wertermittlung"
            else:
                # If they're stuck in Fachprüfung
                if self.game_state.attempts % 8 == 0:
                    target_dept = "Erstbearbeitung"
                    reason = "Sie benötigen eine Stempelfreigabe"

        # If they have the valuation but not the exemption certificate
        elif (
            "Wertermittlung" in self.game_state.collected_documents
            and "Freibetragsbescheinigung" not in self.game_state.collected_documents
        ):
            if current_dept != "Abschlussstelle":
                target_dept = "Abschlussstelle"
                reason = "für die Freibetragsbescheinigung"
            else:
                # If they're stuck in Abschlussstelle
                if self.game_state.attempts % 6 == 0:
                    target_dept = "Erstbearbeitung"
                    reason = "Es fehlt die Verfahrensnummer"

        # If they have most documents but not the final payment request
        elif (
            "Freibetragsbescheinigung" in self.game_state.collected_documents
            and "Zahlungsaufforderung" not in self.game_state.collected_documents
        ):
            if current_dept != "Erstbearbeitung":
                target_dept = "Erstbearbeitung"
                reason = "für die finale Zahlungsaufforderung"
            else:
                # If they're stuck in Erstbearbeitung at the end
                if self.game_state.attempts % 5 == 0:
                    target_dept = "Fachprüfung"
                    reason = "Die Wertermittlung muss noch bestätigt werden"

        # If no logical redirect determined, choose randomly
        if target_dept is None:
            options = [dept for dept in self.bureaucrats.keys() if dept != current_dept]
            target_dept = random.choice(options)
            reasons = [
                "für eine zusätzliche Unterschrift",
                "weil dort die Zuständigkeit liegt",
                "für den nächsten Verfahrensschritt",
                "wegen einer neuen Dienstanweisung",
                "aufgrund einer Systemumstellung",
            ]
            reason = random.choice(reasons)

        # Execute the redirect
        if target_dept:
            self._print_styled(f"\nSie müssen zur Abteilung {target_dept} gehen, {reason}.", "bureaucrat")
            self._transition_to_department(target_dept)

    def _redirect_player(self):
        """Redirect the player to another department"""
        current = self.game_state.current_department
        departments = list(self.bureaucrats.keys())

        # Remove current department from options
        departments.remove(current)

        # Choose a random department
        new_department = random.choice(departments)
        reason = random.choice(
            ["fehlende Zuständigkeit", "Mittagspause", "Systemumstellung", "Personalwechsel", "neue Dienstanweisung"]
        )

        # Redirect message
        self._print_styled(f"\nWegen {reason} müssen Sie zur Abteilung {new_department}!", "bureaucrat")
        self._print_styled(f"\nSie gehen zum Büro der Abteilung {new_department}...", "italic")

        # Update game state
        self.game_state.current_department = new_department
        self.active_bureaucrat = self.bureaucrats[new_department]

        # New bureaucrat introduces themselves
        self._print_styled(f"\n{self.active_bureaucrat.introduce()}", "bureaucrat")
        self._print_styled("Was kann ich für Sie tun?", "bureaucrat")

    def _process_loop(self, loop):
        """Process a bureaucratic loop redirection"""
        redirect = loop["redirect"]
        department = random.choice(list(self.bureaucrats.keys()))
        message = loop["message"].format(department=department)

        self._print_styled(f"\n{message}", "bureaucrat")
        self._print_styled(f"\nSie werden weitergeleitet...", "italic")
        time.sleep(1)

        # Update game state
        self.game_state.current_procedure = redirect

        # Determine if department should change
        if random.random() < 0.7:
            self.game_state.current_department = department
            self.active_bureaucrat = self.bureaucrats[department]

            # New bureaucrat introduces themselves
            self._print_styled(f"\n{self.active_bureaucrat.introduce()}", "bureaucrat")
            self._print_styled("Was führt Sie zu mir?", "bureaucrat")

        # Increase frustration
        self.game_state.increase_frustration(2)

    def _process_keywords(self, user_input: str):
        """(deprecated) previously handled command keywords here; now handled elsewhere"""
        pass

    def _handle_document_request(self, document_name: str):
        """Handle a request for a specific document"""
        # Check if the player meets the requirements
        can_receive, reason = self.active_bureaucrat.check_requirements(document_name, self.game_state)

        if can_receive:
            self._print_styled(f"\nSie haben das Dokument '{document_name}' erhalten!", "success")
            self.game_state.add_document(document_name)
            self.game_state.decrease_frustration(1)
        else:
            self._print_styled(f"\nSie können das Dokument '{document_name}' nicht erhalten: {reason}", "failure")
            self.game_state.increase_frustration(1)

    def _handle_evidence_submission(self, evidence_name: str, form: str):
        """Handle submission of a piece of evidence"""
        success = self.game_state.add_evidence(evidence_name, form)

        if success:
            self._print_styled(f"\nSie haben '{form}' als Nachweis für '{evidence_name}' eingereicht.", "success")

            # Check if this enables any documents
            enabled_docs = []
            for doc_name, doc_data in DOCUMENTS.items():
                if evidence_name in doc_data["requirements"] and doc_name not in self.game_state.collected_documents:
                    enabled_docs.append(doc_name)

            if enabled_docs:
                # Check if this department can issue any of these documents
                dept_docs = [
                    doc for doc in enabled_docs if DOCUMENTS[doc]["department"] == self.game_state.current_department
                ]
                if dept_docs:
                    self._print_styled(f"Dies könnte Ihnen helfen, das Dokument '{dept_docs[0]}' zu erhalten.", "hint")

                    # If they only need one more piece of evidence for this document, suggest it
                    doc = dept_docs[0]
                    missing = [
                        req for req in DOCUMENTS[doc]["requirements"] if req not in self.game_state.evidence_provided
                    ]
                    if len(missing) == 1:
                        self._print_styled(f"Sie benötigen nur noch einen Nachweis für '{missing[0]}'.", "hint")
                else:
                    # If they need to go to another department
                    suggestion = enabled_docs[0]
                    dept = DOCUMENTS[suggestion]["department"]
                    self._print_styled(
                        f"Mit diesem Nachweis könnten Sie bei der Abteilung {dept} das Dokument '{suggestion}' beantragen.",
                        "hint",
                    )

            # Auto-grant documents if all requirements are met (simpler experience)
            self._check_for_auto_document_grants()
        else:
            self._print_styled(f"\nDer Nachweis '{form}' für '{evidence_name}' wurde nicht akzeptiert.", "failure")
            self.game_state.increase_frustration(1)

            # Suggest valid forms
            forms = EVIDENCE[evidence_name]["acceptable_forms"]
            self._print_styled(f"Akzeptierte Formen für diesen Nachweis sind: {', '.join(forms)}", "hint")

    def _check_for_auto_document_grants(self):
        """Check if player can automatically receive any documents based on evidence"""
        current_dept = self.game_state.current_department

        # Only consider documents from the current department
        for doc_name, doc_data in DOCUMENTS.items():
            if doc_data["department"] == current_dept and doc_name not in self.game_state.collected_documents:
                # Check if all requirements are met
                requirements = doc_data["requirements"]
                if all(req in self.game_state.evidence_provided for req in requirements):
                    # Grant the document immediately once all requirements are fulfilled – no randomness.
                    self._print_styled(
                        f"\nDa Sie alle Voraussetzungen erfüllen, erhalten Sie das Dokument '{doc_name}'!", "success"
                    )
                    self.game_state.add_document(doc_name)
                    self.game_state.decrease_frustration(1)

                    # Provide a deterministic suggestion for the next logical step
                    if doc_name == "Schenkungsanmeldung":
                        self._print_styled(
                            "Als nächstes benötigen Sie eine Wertermittlung von der Abteilung Fachprüfung.", "hint"
                        )
                    elif doc_name == "Wertermittlung":
                        self._print_styled(
                            "Jetzt könnten Sie eine Freibetragsbescheinigung von der Abschlussstelle beantragen.",
                            "hint",
                        )
                    elif doc_name == "Freibetragsbescheinigung":
                        self._print_styled(
                            "Mit diesen Dokumenten können Sie zur Erstbearbeitung zurückkehren, um die finale Zahlungsaufforderung zu erhalten.",
                            "hint",
                        )

    def _handle_procedure_action(self, procedure_name: str):
        """Handle a procedure action"""
        success = self.game_state.set_procedure(procedure_name)

        if success:
            self._print_styled(f"\nSie beginnen den Vorgang: {procedure_name}", "italic")

            # Check if the department is correct for this procedure
            correct_dept = None
            for dept in self.bureaucrats:
                if (
                    dept == PROCEDURES[procedure_name]["department"]
                    or PROCEDURES[procedure_name]["department"] == "any"
                ):
                    correct_dept = dept
                    break

            if correct_dept and correct_dept != self.game_state.current_department:
                self._print_styled(f"Sie sind in der falschen Abteilung für diesen Vorgang!", "failure")
                self._print_styled(f"Sie müssten eigentlich bei der Abteilung {correct_dept} sein.", "hint")
                self.game_state.increase_frustration(1)
        else:
            self._print_styled(f"\nDer Vorgang '{procedure_name}' konnte nicht gestartet werden.", "failure")
            self.game_state.increase_frustration(1)

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
        all_docs = all(doc in self.game_state.collected_documents for doc in DOCUMENTS)
        is_frustrated = self.game_state.frustration_level > 8

        return (has_final_doc and is_final_dept and is_final_proc) or (all_docs and is_frustrated)

    def _print_styled(self, text: str, style: str):
        """Print text with styling based on the style parameter"""

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
        else:  # normal
            print(text)

        # Small delay for better readability
        time.sleep(0.1)

    def _normalize_response(self, text: str) -> str:
        """Replace form codes and shorthand with full document names in AI responses."""
        # replace document codes (e.g., S-100) with names
        for doc_name, doc_data in DOCUMENTS.items():
            code = doc_data.get("code")
            if code and code in text:
                text = text.replace(code, doc_name)
        # replace common shorthand
        text = text.replace("WE", "Wertermittlung")
        text = text.replace("FBB", "Freibetragsbescheinigung")
        return text
