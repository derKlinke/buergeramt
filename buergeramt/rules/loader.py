from pathlib import Path
from typing import Dict, List

import yaml

from .models import (Document, Evidence, GameConfig, Persona, PersonaExample,
                     Procedure)

CONFIG_PATH = Path(__file__).parent / "config.yaml"


def load_config() -> GameConfig:
    # read yaml
    raw = yaml.safe_load(CONFIG_PATH.read_text())

    # parse documents
    docs: Dict[str, Document] = {}
    for doc_id, data in raw.get("documents", {}).items():
        docs[doc_id] = Document(id=doc_id, **data)

    # parse evidence
    evs: Dict[str, Evidence] = {}
    for ev_id, data in raw.get("evidence", {}).items():
        evs[ev_id] = Evidence(id=ev_id, **data)

    # parse procedures
    procs: Dict[str, Procedure] = {}
    for pid, data in raw.get("procedures", {}).items():
        procs[pid] = Procedure(id=pid, **data)

    # parse personas
    pers: Dict[str, Persona] = {}
    for persona_id, data in raw.get("personas", {}).items():
        # parse examples
        examples: List[PersonaExample] = [PersonaExample(**ex) for ex in data.get("examples", [])]
        attrs = {k: v for k, v in data.items() if k != "examples"}
        persona = Persona(id=persona_id, examples=examples, **attrs)

        # Fail if required fields are missing
        missing = []
        for field in [
            "name",
            "role",
            "department",
            "personality",
            "handled_documents",
            "required_evidence",
            "examples",
            "system_prompt_template",
            "behavioral_rules",
        ]:
            if getattr(persona, field, None) is None:
                missing.append(field)
        if missing:
            raise ValueError(f"Persona '{persona_id}' is missing required fields: {', '.join(missing)}")

        pers[persona_id] = persona

    # build config
    config = GameConfig(documents=docs, evidence=evs, procedures=procs, personas=pers)
    return config

# singleton config
_cfg: GameConfig = None

def get_config() -> GameConfig:
    global _cfg
    if _cfg is None:
        _cfg = load_config()
    return _cfg
