from typing import List, Optional

from buergeramt.rules.loader import get_config
from buergeramt.utils.game_logger import get_logger


# Game state tracking
class GameState:
    def __init__(self, config=None):
        # Initialize logger
        self.logger = get_logger()
        self.logger.log_game_state("Initializing new game state")
        
        # load unified game config
        self.config = config or get_config()
        self.collected_documents = {}  # id->Document
        self.evidence_provided = {}  # id->form
        self.current_department = "initial"
        self.current_procedure = "Antragstellung"
        self.procedure_history = ["Antragstellung"]  # Track procedure progression
        self.attempts = 0
        self.frustration_level = 0
        self.progress = 0
        
        # Log initial state
        self.logger.log_game_state(self)

    def add_document(self, document_name: str) -> bool:
        """add a completed document to the player's collection"""
        docs = self.config.documents
        if document_name in docs:
            self.collected_documents[document_name] = docs[document_name]
            self.logger.log_document_acquired(document_name)
            return True
        else:
            self.logger.log_error(ValueError(f"Document '{document_name}' not found in config"), 
                                "add_document")
        return False

    def add_evidence(self, evidence_name: str, evidence_form: str) -> bool:
        """add a piece of evidence to the player's collection"""
        evs = self.config.evidence
        if evidence_name in evs and evidence_form in evs[evidence_name].acceptable_forms:
            self.evidence_provided[evidence_name] = evidence_form
            self.logger.log_evidence_provided(evidence_name, evidence_form)
            return True
        else:
            self.logger.log_error(ValueError(f"Evidence '{evidence_name}' with form '{evidence_form}' is invalid"), 
                                "add_evidence")
        return False

    def increase_frustration(self, amount=1):
        """Increase the player's frustration level"""
        old_level = self.frustration_level
        self.frustration_level += amount
        self.logger.log_state_change("frustration_level", old_level, self.frustration_level)

    def decrease_frustration(self, amount=1):
        """Decrease the player's frustration level"""
        old_level = self.frustration_level
        self.frustration_level = max(0, self.frustration_level - amount)
        self.logger.log_state_change("frustration_level", old_level, self.frustration_level)

    def transition_procedure(self, next_procedure: str) -> bool:
        """Transition to a new procedure if it's a valid next step"""
        # Check if the procedure exists in the config
        if next_procedure not in self.config.procedures:
            self.logger.log_error(ValueError(f"Procedure '{next_procedure}' not found in config"),
                                "transition_procedure")
            return False
            
        # Get current procedure definition
        current_proc = self.config.procedures.get(self.current_procedure)
        old_procedure = self.current_procedure
        
        # Check if next_procedure is in the allowed next_steps
        if current_proc and next_procedure in current_proc.next_steps:
            self.current_procedure = next_procedure
            self.procedure_history.append(next_procedure)
            self.logger.log_procedure_transition(old_procedure, next_procedure)
            return True
        # Allow transition if player is frustrated enough (bureaucratic difficulty)
        elif self.frustration_level > 5:
            self.current_procedure = next_procedure
            self.procedure_history.append(next_procedure)
            self.logger.log_procedure_transition(
                old_procedure, next_procedure, 
                f"Force transition due to high frustration ({self.frustration_level})"
            )
            return True
        
        self.logger.log_error(
            ValueError(f"Cannot transition from '{old_procedure}' to '{next_procedure}'"),
            f"next_steps={current_proc.next_steps if current_proc else '[]'}"
        )
        return False

    def get_valid_next_procedures(self) -> List[str]:
        """Get list of valid next procedures based on current procedure"""
        current_proc = self.config.procedures.get(self.current_procedure)
        if current_proc:
            return current_proc.next_steps
        return []

    def get_procedure_keywords(self) -> List[str]:
        """Get keywords for the current procedure"""
        current_proc = self.config.procedures.get(self.current_procedure)
        if current_proc:
            return current_proc.keywords
        return []

    def get_procedure_description(self) -> Optional[str]:
        """Get description of the current procedure"""
        current_proc = self.config.procedures.get(self.current_procedure)
        if current_proc:
            return current_proc.description
        return None

    def update_progress(self):
        """Update the player's progress in the game"""
        old_progress = self.progress
        
        document_progress = len(self.collected_documents) * 10
        evidence_progress = len(self.evidence_provided) * 5
        
        # Base procedure progression on position in the overall flow
        procedure_weights = {
            "Antragstellung": 0,
            "Formularprüfung": 5,
            "Nachweisanforderung": 10,
            "Terminvereinbarung": 15,
            "Weiterleitung": 15,
            "Warteschleife": 15,
            "Bescheiderteilung": 20,
            "Widerspruch": 15,  # Lower than Bescheid since it's a detour
            "Zahlungsaufforderung": 25,
            "Abschluss": 30
        }
        
        procedure_bonus = procedure_weights.get(self.current_procedure, 0)
        
        # Extra bonus for procedure history length (shows progression through system)
        history_bonus = min(20, len(self.procedure_history) * 2)
        
        self.progress = min(100, document_progress + evidence_progress + procedure_bonus + history_bonus)
        
        if self.progress != old_progress:
            self.logger.log_state_change("progress", old_progress, self.progress)
            
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
        
    def get_bureaucrat_for_department(self, department: str) -> str:
        """Get the appropriate bureaucrat name for a department"""
        department_to_bureaucrat = {
            "Erstbearbeitung": "HerrSchmidt",
            "Fachprüfung": "FrauMueller",
            "Abschlussstelle": "HerrWeber"
        }
        
        # Log the bureaucrat selection
        bureaucrat = department_to_bureaucrat.get(department)
        if bureaucrat:
            self.logger.logger.debug(f"Selected bureaucrat '{bureaucrat}' for department '{department}'")
        else:
            self.logger.logger.warning(f"No bureaucrat found for department '{department}'")
            
        return department_to_bureaucrat.get(department, "HerrSchmidt")  # Default to HerrSchmidt if department unknown

    def get_formatted_gamestate(self):
        """Return a JSON-formatted string of the current game state for messaging or debugging."""
        import json

        state_info = {
            "current_department": self.current_department,
            "current_procedure": self.current_procedure,
            "valid_next_procedures": self.get_valid_next_procedures(),
            "procedure_history": self.procedure_history,
            "procedure_keywords": self.get_procedure_keywords(),
            "procedure_description": self.get_procedure_description(),
            "collected_documents": self.get_collected_documents(),
            "evidence_provided": self.get_evidence_provided(),
            "attempts": self.attempts,
            "frustration_level": self.frustration_level,
            "progress": self.progress,
            "department_documents": self.get_department_documents(),
            "missing_evidence": self.get_missing_evidence(),
        }
        return json.dumps(state_info, indent=2)
