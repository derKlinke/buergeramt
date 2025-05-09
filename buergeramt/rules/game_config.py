from typing import Dict, Optional

from pydantic import BaseModel, Field

from buergeramt.rules.models import Document, Evidence, PersonaDefaults
from buergeramt.rules.persona import Persona


class GameConfig(BaseModel):
    documents: Dict[str, Document]
    evidence: Dict[str, Evidence]
    personas: Dict[str, Persona]
    persona_defaults: PersonaDefaults = Field(default_factory=PersonaDefaults)
    final_document: Optional[str] = None  # id of the end goal document
    starting_agent: Optional[str] = None  # persona_id or department name
