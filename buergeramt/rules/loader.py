from pathlib import Path
from typing import Dict

import yaml

from .models import Document, Evidence, GameConfig, Persona, PersonaConfig, PersonaDefaults, Procedure

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

    # Initialize defaults
    persona_defaults = PersonaDefaults()
    if "persona_defaults" in raw:
        # Update defaults with values from config if provided
        persona_defaults = PersonaDefaults(**raw["persona_defaults"])

    # parse personas
    pers: Dict[str, Persona] = {}
    for persona_id, data in raw.get("personas", {}).items():
        # Create a raw PersonaConfig object
        persona_config = PersonaConfig(**data)

        # Generate the complete Persona with defaults filled in
        persona = create_persona_from_config(persona_id, persona_config, persona_defaults)
        pers[persona_id] = persona

    # build config
    config = GameConfig(
        documents=docs, evidence=evs, procedures=procs, personas=pers, persona_defaults=persona_defaults
    )
    return config


def create_persona_from_config(persona_id: str, config: PersonaConfig, defaults: PersonaDefaults) -> Persona:
    """Create a complete Persona object from a minimal config, filling in defaults."""
    # Apply defaults for optional fields if not provided
    behavioral_rules = config.behavioral_rules or defaults.behavioral_rules
    system_prompt_template = config.system_prompt_template or defaults.system_prompt_template

    # Build the complete persona
    return Persona(
        id=persona_id,
        name=config.name,
        role=config.role,
        department=config.department,
        personality=config.personality,
        handled_documents=config.handled_documents,
        required_evidence=config.required_evidence,
        behavioral_rules=behavioral_rules,
        system_prompt_template=system_prompt_template,
    )


# singleton config
_cfg: GameConfig = None


def get_config() -> GameConfig:
    global _cfg
    if _cfg is None:
        _cfg = load_config()
    return _cfg
