from dataclasses import dataclass
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, PrivateAttr
from pydantic_ai import RunContext

from buergeramt.rules.game_config import GameConfig
from buergeramt.rules.loader import get_config
from buergeramt.rules.models import Document
from buergeramt.utils.game_logger import get_logger


class GameState(BaseModel):
    # debug: log tool calls for agent integration
    def _debug_log_tool_call(self, tool_name: str, **kwargs):
        self._logger.logger.info(f"[TOOL CALL] {tool_name}({', '.join(f'{k}={v}' for k, v in kwargs.items())})")

    config: GameConfig = Field(default_factory=get_config)
    collected_documents: Dict[str, Document] = Field(default_factory=dict)
    evidence_provided: Dict[str, str] = Field(default_factory=dict)
    current_department: str = "initial"
    current_procedure: str = "Antragstellung"
    procedure_history: List[str] = Field(default_factory=lambda: ["Antragstellung"])
    attempts: int = 0
    frustration_level: int = 0
    progress: int = 0

    # _logger is not part of the model serialization
    _logger: any = PrivateAttr(default_factory=get_logger)

    def __init__(self, **data):
        super().__init__(**data)
        self._logger.log_game_state("Initializing new game state")
        self._logger.log_game_state(self)

    def add_document(self, document_name: str) -> str:
        self._debug_log_tool_call("add_document", document_name=document_name)
        docs = self.config.documents
        if document_name not in docs:
            self._logger.log_error(ValueError(f"Document '{document_name}' not found in config"), "add_document")
            return f"Dokument '{document_name}' ist nicht bekannt."
        doc = docs[document_name]
        missing_reqs = [req for req in doc.requirements if req not in self.evidence_provided]
        if missing_reqs:
            missing_str = ", ".join(missing_reqs)
            return f"Sie müssen zuerst folgende Nachweise vorlegen: {missing_str}."
        self.collected_documents[document_name] = doc

        print(f"Document '{document_name}' added to collected documents.")

        self._logger.log_document_acquired(document_name)
        return f"Dokument '{document_name}' wurde erfolgreich hinzugefügt."

    def add_evidence(self, evidence_name: str, evidence_form: str) -> bool:
        self._debug_log_tool_call("add_evidence", evidence_name=evidence_name, evidence_form=evidence_form)
        evs = self.config.evidence
        if evidence_name in evs and evidence_form in evs[evidence_name].acceptable_forms:
            self.evidence_provided[evidence_name] = evidence_form

            print(f"Evidence '{evidence_name}' with form '{evidence_form}' added to evidence provided.")

            self._logger.log_evidence_provided(evidence_name, evidence_form)
            return True
        self._logger.log_error(
            ValueError(f"Evidence '{evidence_name}' with form '{evidence_form}' is invalid"), "add_evidence"
        )
        return False

    def increase_frustration(self, amount: int = 1):
        self._debug_log_tool_call("increase_frustration", amount=amount)
        old_level = self.frustration_level
        self.frustration_level += amount
        self._logger.log_state_change("frustration_level", old_level, self.frustration_level)

    def decrease_frustration(self, amount: int = 1):
        self._debug_log_tool_call("decrease_frustration", amount=amount)
        old_level = self.frustration_level
        self.frustration_level = max(0, self.frustration_level - amount)
        self._logger.log_state_change("frustration_level", old_level, self.frustration_level)

    def transition_procedure(self, next_procedure: str) -> bool:
        self._debug_log_tool_call("transition_procedure", next_procedure=next_procedure)
        if next_procedure not in self.config.procedures:
            self._logger.log_error(
                ValueError(f"Procedure '{next_procedure}' not found in config"), "transition_procedure"
            )
            return False
        current_proc = self.config.procedures.get(self.current_procedure)
        old_procedure = self.current_procedure
        if current_proc and next_procedure in current_proc.next_steps:
            self.current_procedure = next_procedure
            self.procedure_history.append(next_procedure)
            self._logger.log_procedure_transition(old_procedure, next_procedure)
            return True
        if self.frustration_level > 5:
            self.current_procedure = next_procedure
            self.procedure_history.append(next_procedure)
            self._logger.log_procedure_transition(
                old_procedure, next_procedure, f"Force transition due to high frustration ({self.frustration_level})"
            )
            return True
        self._logger.log_error(
            ValueError(f"Cannot transition from '{old_procedure}' to '{next_procedure}'"),
            f"next_steps={current_proc.next_steps if current_proc else '[]'}",
        )
        return False

    def get_valid_next_procedures(self) -> List[str]:
        current_proc = self.config.procedures.get(self.current_procedure)
        if current_proc:
            return current_proc.next_steps
        return []

    def get_procedure_keywords(self) -> List[str]:
        current_proc = self.config.procedures.get(self.current_procedure)
        if current_proc:
            return current_proc.keywords
        return []

    def get_procedure_description(self) -> Optional[str]:
        current_proc = self.config.procedures.get(self.current_procedure)
        if current_proc:
            return current_proc.description
        return None

    def update_progress(self):
        old_progress = self.progress
        document_progress = len(self.collected_documents) * 10
        evidence_progress = len(self.evidence_provided) * 5
        procedure_weights = {
            "Antragstellung": 0,
            "Formularprüfung": 5,
            "Nachweisanforderung": 10,
            "Terminvereinbarung": 15,
            "Weiterleitung": 15,
            "Warteschleife": 15,
            "Bescheiderteilung": 20,
            "Widerspruch": 15,
            "Zahlungsaufforderung": 25,
            "Abschluss": 30,
        }
        procedure_bonus = procedure_weights.get(self.current_procedure, 0)
        history_bonus = min(20, len(self.procedure_history) * 2)
        self.progress = min(100, document_progress + evidence_progress + procedure_bonus + history_bonus)
        if self.progress != old_progress:
            self._logger.log_state_change("progress", old_progress, self.progress)
        return self.progress

    def get_collected_documents(self) -> List[str]:
        return list(self.collected_documents.keys())

    def get_evidence_provided(self) -> List[str]:
        return list(self.evidence_provided.keys())

    def get_department_documents(self) -> List[str]:
        return [doc_id for doc_id, doc in self.config.documents.items() if doc.department == self.current_department]

    def get_missing_evidence(self) -> Dict[str, List[str]]:
        missing: Dict[str, List[str]] = {}
        for doc_id, doc in self.config.documents.items():
            if doc_id in self.collected_documents:
                continue
            missing_reqs = [r for r in doc.requirements if r not in self.evidence_provided]
            if missing_reqs:
                missing[doc_id] = missing_reqs
        return missing

    def get_bureaucrat_for_department(self, department: str) -> str:
        department_to_bureaucrat = {
            "Erstbearbeitung": "HerrSchmidt",
            "Fachprüfung": "FrauMueller",
            "Abschlussstelle": "HerrWeber",
        }
        bureaucrat = department_to_bureaucrat.get(department)
        if bureaucrat:
            self._logger.logger.debug(f"Selected bureaucrat '{bureaucrat}' for department '{department}'")
        else:
            self._logger.logger.warning(f"No bureaucrat found for department '{department}'")
        return department_to_bureaucrat.get(department, "HerrSchmidt")

    def get_formatted_gamestate(self) -> str:
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

    def export_for_agent(self) -> dict:
        return self.model_dump()


# Context class for agent and tools
@dataclass
class GameDeps:
    game_state: "GameState"


# Tool registration will be done via @agent.tool in the agent setup, not here.
# Example tool function signatures for use with @agent.tool:
def add_document(ctx: RunContext[GameDeps], document_name: str):
    return ctx.deps.game_state.add_document(document_name)


def add_evidence(ctx: RunContext[GameDeps], evidence_name: str, evidence_form: str):
    return ctx.deps.game_state.add_evidence(evidence_name, evidence_form)


def transition_procedure(ctx: RunContext[GameDeps], next_procedure: str):
    return ctx.deps.game_state.transition_procedure(next_procedure)


def increase_frustration(ctx: RunContext[GameDeps], amount: int = 1):
    return ctx.deps.game_state.increase_frustration(amount)


def decrease_frustration(ctx: RunContext[GameDeps], amount: int = 1):
    return ctx.deps.game_state.decrease_frustration(amount)
