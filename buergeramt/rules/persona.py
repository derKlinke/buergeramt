from typing import List

from pydantic import BaseModel


class Persona(BaseModel):
    """Complete persona with all required fields populated, merging global defaults with persona-specific rules"""

    id: str
    name: str
    role: str
    department: str
    system_prompt_template: str
    personality: List[str]
    behavioral_rules: List[str]
    handled_documents: List[str]
    required_evidence: List[str]
