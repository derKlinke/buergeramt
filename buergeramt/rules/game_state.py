from buergeramt.rules.loader import get_config


# Game state tracking
class GameState:
    def __init__(self, config=None):
        # load unified game config
        self.config = config or get_config()
        self.collected_documents = {}  # id->Document
        self.evidence_provided = {}  # id->form
        self.current_department = "initial"
        self.current_procedure = "Antragstellung"
        self.attempts = 0
        self.frustration_level = 0
        self.progress = 0

    def add_document(self, document_name: str) -> bool:
        """add a completed document to the player's collection"""
        docs = self.config.documents
        if document_name in docs:
            self.collected_documents[document_name] = docs[document_name]
            return True
        return False

    def add_evidence(self, evidence_name: str, evidence_form: str) -> bool:
        """add a piece of evidence to the player's collection"""
        evs = self.config.evidence
        if evidence_name in evs and evidence_form in evs[evidence_name].acceptable_forms:
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

    def get_collected_documents(self):
        """Return a list of collected document names."""
        return list(self.collected_documents.keys())

    def get_evidence_provided(self):
        """Return a list of provided evidence names."""
        return list(self.evidence_provided.keys())

    def get_department_documents(self) -> list[str]:
        """return document ids available in the current department"""
        return [doc_id for doc_id, doc in self.config.documents.items() if doc.department == self.current_department]

    def get_missing_evidence(self) -> dict[str, list[str]]:
        """return a map of doc ids to list of missing evidence ids"""
        missing: dict[str, list[str]] = {}
        for doc_id, doc in self.config.documents.items():
            if doc_id in self.collected_documents:
                continue
            # find requirements not yet provided
            missing_reqs = [r for r in doc.requirements if r not in self.evidence_provided]
            if missing_reqs:
                missing[doc_id] = missing_reqs
        return missing

    def get_formatted_gamestate(self):
        """Return a JSON-formatted string of the current game state for messaging or debugging."""
        import json

        state_info = {
            "current_department": self.current_department,
            "current_procedure": self.current_procedure,
            "collected_documents": self.get_collected_documents(),
            "evidence_provided": self.get_evidence_provided(),
            "attempts": self.attempts,
            "frustration_level": self.frustration_level,
            "progress": self.progress,
            "department_documents": self.get_department_documents(),
            "missing_evidence": self.get_missing_evidence(),
        }
        return json.dumps(state_info, indent=2)
