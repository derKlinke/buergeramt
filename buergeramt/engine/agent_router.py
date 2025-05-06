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
        # determine starting department: map procedure department codes to persona departments
        proc_dept_code = game_state.current_department or config.procedures[game_state.current_procedure].department
        # alias mapping from procedure-level codes to persona departments
        DEPT_ALIAS = {
            "initial": "Erstbearbeitung",
            "final": "Abschlussstelle",
            "appeals": "Erstbearbeitung",
        }
        dept_key = DEPT_ALIAS.get(proc_dept_code, proc_dept_code)
        # fall back to any matching persona department
        self.active_bureaucrat = self.bureaucrats.get(dept_key) or next(iter(self.bureaucrats.values()))
        # set game state to the persona department
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
            print_styled(f"\n{self.active_bureaucrat.introduce()}", "bureaucrat")
            if len(self.game_state.collected_documents) > 0:
                doc_list = ", ".join(list(self.game_state.collected_documents.keys()))
                print_styled(f"Ich sehe, Sie haben bereits folgende Dokumente: {doc_list}.", "bureaucrat")
            else:
                print_styled("Was kann ich für Sie tun?", "bureaucrat")

    def get_active_bureaucrat(self):
        return self.active_bureaucrat

    def get_bureaucrats(self):
        return self.bureaucrats
