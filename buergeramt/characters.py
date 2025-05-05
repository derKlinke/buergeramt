"""
Rule-based bureaucrat characters for the Schenkungssteuer game.
Defines a base Bureaucrat class and fallback NPCs.
"""
from .game_rules import DOCUMENTS

class Bureaucrat:
    """Base class for rule-based bureaucrat characters."""
    def __init__(self, name: str, title: str, department: str):
        self.name = name
        self.title = title
        self.department = department

    def introduce(self) -> str:
        return f"Mein Name ist {self.name}, {self.title} der Abteilung {self.department}."

    def respond(self, user_input: str, game_state) -> str:
        # Default fallback response when AI is unavailable
        return "Es tut mir leid, das System ist momentan nicht verfügbar."

    def check_requirements(self, document: str, game_state):
        # Rule-based check: use game_state to verify requirements
        has_req = game_state.check_document_requirements(document)
        reason = "alle Voraussetzungen erfüllt" if has_req else "nicht alle Voraussetzungen erfüllt"
        return has_req, reason

    def give_hint(self, game_state) -> str:
        # Simple generic hint
        missing = []
        for doc, data in DOCUMENTS.items():
            if doc not in game_state.collected_documents:
                missing.append(doc)
        if missing:
            return f"Sie könnten folgendes Dokument anfragen: {missing[0]}."
        return "Bitte prüfen Sie Ihre Unterlagen."

class HerrSchmidt(Bureaucrat):
    def __init__(self):
        super().__init__("Herr Schmidt", "Oberamtsrat", "Erstbearbeitung")

class FrauMüller(Bureaucrat):
    def __init__(self):
        super().__init__("Frau Müller", "Sachbearbeiterin", "Fachprüfung")

class HerrWeber(Bureaucrat):
    def __init__(self):
        super().__init__("Herr Weber", "Leiter", "Abschlussstelle")