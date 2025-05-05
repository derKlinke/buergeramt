from buergeramt.rules.bureaucratic_loops import BUREAUCRATIC_LOOPS
from buergeramt.rules.documents import DOCUMENTS
from buergeramt.rules.evidence import EVIDENCE
from buergeramt.rules.procedures import PROCEDURES

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

    def check_document_requirements(self, document_name):
        """Check if the player has all requirements for a document"""
        if document_name not in DOCUMENTS:
            return False

        # A requirement may be an evidence key or a prior document name
        requirements = DOCUMENTS[document_name]["requirements"]
        for req in requirements:
            # evidence requirement
            if req in EVIDENCE:
                if req not in self.evidence_provided:
                    return False
            # document requirement
            elif req in DOCUMENTS:
                if req not in self.collected_documents:
                    return False
            else:
                # unknown requirement
                return False
        return True

    def set_department(self, department_name):
        """Change the player's current department"""
        self.current_department = department_name

    def set_procedure(self, procedure_name):
        """Change the player's current procedure"""
        if procedure_name in PROCEDURES:
            self.current_procedure = procedure_name
            self.attempts += 1
            return True
        return False

    def get_next_steps(self):
        """Get possible next steps based on current procedure"""
        if self.current_procedure in PROCEDURES:
            return PROCEDURES[self.current_procedure]["next_steps"]
        return []

    def check_for_loop(self):
        """Check if player is in a bureaucratic loop"""
        for loop in BUREAUCRATIC_LOOPS:
            if loop["trigger"] == self.current_procedure:
                # Implement conditions for loops here
                if loop["condition"] == "missing_evidence" and len(self.evidence_provided) < 3:
                    return loop
                elif (
                        loop["condition"] == "wrong_department"
                        and self.current_department != PROCEDURES[self.current_procedure]["department"]
                ):
                    return loop
                elif loop["condition"] == "incomplete_form" and self.attempts % 3 == 0:
                    return loop
                elif loop["condition"] == "missing_signatures" and len(self.collected_documents) < 2:
                    return loop
                elif loop["condition"] == "calculation_error" and self.attempts % 5 == 0:
                    return loop
        return None

    def increase_frustration(self, amount=1):
        """Increase the player's frustration level"""
        self.frustration_level += amount

    def decrease_frustration(self, amount=1):
        """Decrease the player's frustration level"""
        self.frustration_level = max(0, self.frustration_level - amount)

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
