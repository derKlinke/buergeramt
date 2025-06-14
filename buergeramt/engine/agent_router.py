from buergeramt.characters.persona_factory import build_bureaucrat
from buergeramt.rules.loader import get_config


class AgentRouter:
    def __init__(self, game_state):
        # dynamically build agents from config
        config = get_config()
        self.bureaucrats = {}
        for persona_id, persona in config.personas.items():
            agent = build_bureaucrat(persona_id)
            self.bureaucrats[persona.department] = agent
        self.game_state = game_state
        # always start with the configured starting agent if available
        starting_agent = getattr(config, "starting_agent", None)
        if starting_agent and starting_agent in self.bureaucrats:
            self.active_bureaucrat = self.bureaucrats[starting_agent]
        else:
            self.active_bureaucrat = self.bureaucrats.get("Erstbearbeitung") or next(iter(self.bureaucrats.values()))
        self.game_state.current_department = self.active_bureaucrat.department

    def switch_agent(self, agent_name: str, print_styled=None) -> bool:
        name = agent_name.strip().lower()
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
        for key, dept in name_to_dept.items():
            if key in name:
                if dept == self.game_state.current_department:
                    if print_styled:
                        print_styled("\nSie sind bereits in dieser Abteilung.", "italic")
                    return True
                self.transition_to_department(dept, print_styled)
                return True
        for dept in self.bureaucrats:
            if dept.lower() in name:
                if dept == self.game_state.current_department:
                    if print_styled:
                        print_styled("\nSie sind bereits in dieser Abteilung.", "italic")
                    return True
                self.transition_to_department(dept, print_styled)
                return True
        return False

    def transition_to_department(self, department: str, print_styled=None):
        if department == self.game_state.current_department:
            if print_styled:
                print_styled("\nSie sind bereits in dieser Abteilung.", "italic")
            return
        if print_styled:
            print_styled(f"\nSie verlassen das Büro von {self.active_bureaucrat.name}...", "italic")
        import time

        time.sleep(1)
        if print_styled:
            print_styled(f"Sie gehen zum Büro der Abteilung {department}...", "italic")
        time.sleep(1)
        self.game_state.current_department = department
        self.active_bureaucrat = self.bureaucrats[department]
        if print_styled:
            print_styled(f"\n{self.active_bureaucrat.introduce(game_state=self.game_state)}", "bureaucrat")
            if len(self.game_state.collected_documents) > 0:
                doc_list = ", ".join(list(self.game_state.collected_documents.keys()))
                print_styled(f"Ich sehe, Sie haben bereits folgende Dokumente: {doc_list}.", "bureaucrat")
            else:
                print_styled("Was kann ich für Sie tun?", "bureaucrat")

    def get_active_bureaucrat(self):
        return self.active_bureaucrat

    def get_bureaucrats(self):
        return self.bureaucrats
