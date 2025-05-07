from typing import Dict, List, Optional

from pydantic import BaseModel, Field


# model for a document definition
class Document(BaseModel):
    id: str
    description: str
    requirements: List[str]
    department: str
    code: str


# model for an evidence definition
class Evidence(BaseModel):
    id: str
    description: str
    acceptable_forms: List[str]


# model for a procedure definition
class Procedure(BaseModel):
    id: str
    description: str
    keywords: List[str]
    next_steps: List[str]
    department: str


class PersonaConfig(BaseModel):
    """Raw persona config from YAML file - minimal required fields"""

    name: str
    role: str
    department: str
    personality: List[str]
    handled_documents: List[str]
    required_evidence: List[str]
    # Optional fields - will be filled with defaults if not provided
    behavioral_rules: Optional[List[str]] = None
    system_prompt_template: Optional[str] = None


class Persona(BaseModel):
    """Complete persona with all required fields populated"""

    id: str
    name: str
    role: str
    department: str
    system_prompt_template: str
    personality: List[str]
    behavioral_rules: List[str]
    handled_documents: List[str]
    required_evidence: List[str]


# Default templates and values for personas
class PersonaDefaults(BaseModel):
    system_prompt_template: str = """
## ROLE: {name}, {role}, Deutsche Finanzamtsbehörde (Abteilung {department})
## YOUR PERSONALITY
{personality}
## GAME CONTEXT
- Your department issues: {handled_documents}
- Required evidence: {required_evidence}
"""
    behavioral_rules: List[str] = ["NEVER break character", "ALWAYS keep responses under 100 words"]


# overall game configuration
class GameConfig(BaseModel):
    documents: Dict[str, Document]
    evidence: Dict[str, Evidence]
    procedures: Dict[str, Procedure]
    personas: Dict[str, Persona]
    persona_defaults: PersonaDefaults = Field(default_factory=PersonaDefaults)
