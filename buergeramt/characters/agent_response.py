from typing import List, Optional

from pydantic import BaseModel


class AgentActions(BaseModel):
    intent: Optional[str]
    document: Optional[str]
    requirements_met: Optional[bool]
    evidence: Optional[List[str]]
    department: Optional[str]
    valid: bool
    message: str


class AgentResponse(BaseModel):
    response_text: str
    actions: AgentActions
