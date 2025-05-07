from typing import List, Optional

from pydantic import BaseModel


class AgentActions(BaseModel):
    intent: Optional[str]
    document: Optional[str]
    requirements_met: Optional[bool]
    evidence: Optional[List[str]]
    department: Optional[str]
    procedure: Optional[str]  # Current or target procedure
    next_procedure: Optional[str]  # Procedure to transition to
    procedure_transition: Optional[bool]  # Flag indicating if a procedure transition is needed
    valid: bool
    message: str


class AgentResponse(BaseModel):
    response_text: str
    actions: AgentActions
