from typing import Dict, List

from pydantic import BaseModel


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


# model for a persona definition
class PersonaExample(BaseModel):
    user: str
    assistant: str


class Persona(BaseModel):
    id: str
    name: str
    role: str
    department: str
    system_prompt_template: str
    personality: List[str]
    behavioral_rules: List[str]
    examples: List[PersonaExample]
    handled_documents: List[str]
    required_evidence: List[str]


# overall game configuration
class GameConfig(BaseModel):
    documents: Dict[str, Document]
    evidence: Dict[str, Evidence]
    procedures: Dict[str, Procedure]
    personas: Dict[str, Persona]
