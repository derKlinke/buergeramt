from typing import List, Optional

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


class PersonaConfig(BaseModel):
    """Raw persona config from YAML file - minimal required fields"""

    name: str
    role: str
    department: str
    personality: List[str]
    handled_documents: List[str]
    required_evidence: List[str]
    behavioral_rules: Optional[List[str]] = None


class PersonaDefaults(BaseModel):
    system_prompt_template: str
    behavioral_rules: List[str]


# overall game configuration
