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

        # initialize game state
        self.game_state = GameState()
        # decide whether to enable AI characters
        self.use_ai_characters = use_ai_characters
        if self.use_ai_characters:
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
        else:
            self.agent_router = None
        # game control flags
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
        self._print_styled(
            "• Drücken Sie Ihre Frustration aus - manchmal führt Chaos zu überraschenden Ergebnissen", "hint"
        )
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
        self._print_styled(
            f"\n{self.agent_router.get_active_bureaucrat().introduce(game_state=self.game_state)}", "bureaucrat"
        )

    def switch_agent(self, agent_name: str) -> bool:
        return self.agent_router.switch_agent(agent_name, print_styled=self._print_styled)

    def process_input(self, user_input: str) -> bool:
        if getattr(self, "game_over", True):
            return False
        self.logger.log_user_input(user_input)
        if self.check_win_condition():
            win_message = "\n=== HERZLICHEN GLÜCKWUNSCH! ==="
            self._print_styled(win_message, "title")
            self.logger.logger.info(win_message)
            success_msg = "Sie haben es tatsächlich geschafft! Die Schenkungssteuer wurde bewilligt."
            self._print_styled(success_msg, "success")
            stats_msg = f"Sie haben {self.game_state.attempts} Versuche gebraucht und Ihre Frustration erreichte maximal Level {self.game_state.frustration_level}."
            self._print_styled(stats_msg, "italic")
            self.logger.logger.info(
                f"GAME COMPLETED - Attempts: {self.game_state.attempts}, Max Frustration: {self.game_state.frustration_level}"
            )
            final_msg = "Sie dürfen jetzt den Brief mit dem Steuerbescheid in 4-6 Wochen erwarten."
            self._print_styled(final_msg, "bureaucrat")
            self.game_over = True
            self.win_condition = True
            self.logger.logger.info("=== Game session completed successfully ===")
            return False
        self.game_state.attempts += 1
        self.logger.logger.debug(f"Processing input (attempt #{self.game_state.attempts}): {user_input}")
        # Use dependency injection for agent call
        response_text = self.agent_router.get_active_bureaucrat().respond(user_input, self.game_state)
        self._print_styled(response_text, "bureaucrat")
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
            self.logger.log_win_condition(
                True, f"Frustration win condition met - Level: {self.game_state.frustration_level}"
            )
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
