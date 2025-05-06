import time

from buergeramt.characters import *
from buergeramt.engine.agent_router import AgentRouter
from buergeramt.rules import *


class GameEngine:
    """Main game engine class handling the game loop and state"""

    def __init__(self, use_ai_characters: bool = True):
        self.game_state = GameState()
        self.use_ai_characters = True
        try:
            self.agent_router = AgentRouter(self.game_state)
            print("Bürokratensimulation mit KI-Charakteren gestartet. Viel Erfolg!")
        except Exception as e:
            print(f"Fehler beim Initialisieren der KI-Charaktere: {e}")
            print("Das Spiel kann nicht gestartet werden.")
            self.game_over = True
            return
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
        valid = actions.valid
        message = actions.message

        # Evidence submission
        if intent == "provide_evidence" and evidence:
            for ev in evidence or []:
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
