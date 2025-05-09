from typing import Dict

from pydantic import BaseModel, Field

from buergeramt.rules.models import Document, Evidence, Procedure, PersonaDefaults
from buergeramt.rules.persona import Persona


class GameConfig(BaseModel):
    documents: Dict[str, Document]
    evidence: Dict[str, Evidence]
    procedures: Dict[str, Procedure]
    personas: Dict[str, Persona]
    persona_defaults: PersonaDefaults = Field(default_factory=PersonaDefaults)
