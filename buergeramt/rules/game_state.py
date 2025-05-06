from buergeramt.rules.documents import DOCUMENTS
from buergeramt.rules.evidence import EVIDENCE


# Game state tracking
class GameState:
    def __init__(self):
        self.collected_documents = {}
        self.current_department = "initial"
        self.evidence_provided = {}
        self.current_procedure = "Antragstellung"
        self.attempts = 0
        self.frustration_level = 0
        self.progress = 0

    def add_document(self, document_name):
        """Add a completed document to the player's collection"""
        if document_name in DOCUMENTS:
            self.collected_documents[document_name] = DOCUMENTS[document_name]
            return True
        return False

    def add_evidence(self, evidence_name, evidence_form):
        """Add a piece of evidence to the player's collection"""
        if evidence_name in EVIDENCE and evidence_form in EVIDENCE[evidence_name]["acceptable_forms"]:
            self.evidence_provided[evidence_name] = evidence_form
            return True
        return False

    def increase_frustration(self, amount=1):
        """Increase the player's frustration level"""
        self.frustration_level += amount

    def decrease_frustration(self, amount=1):
        """Decrease the player's frustration level"""
        self.frustration_level = max(0, self.frustration_level - amount)

    # FIXME: this makes no sense anymore
    def update_progress(self):
        """Update the player's progress in the game"""
        document_progress = len(self.collected_documents) * 10
        evidence_progress = len(self.evidence_provided) * 5
        procedure_bonus = 0

        if self.current_procedure == "Bescheiderteilung":
            procedure_bonus = 15
        elif self.current_procedure == "Zahlungsaufforderung":
            procedure_bonus = 20
        elif self.current_procedure == "Abschluss":
            procedure_bonus = 25

        self.progress = min(100, document_progress + evidence_progress + procedure_bonus)
        return self.progress
