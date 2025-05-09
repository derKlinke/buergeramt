from pathlib import Path
from typing import Dict

import yaml

from buergeramt.rules.game_config import GameConfig
from buergeramt.rules.models import (Document, Evidence, PersonaConfig,
                                     PersonaDefaults)
from buergeramt.rules.persona import Persona

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

    # Require persona_defaults in YAML
    if "persona_defaults" not in raw:
        raise ValueError("persona_defaults section missing in config.yaml")
    persona_defaults = PersonaDefaults(**raw["persona_defaults"])

    # parse personas
    pers: Dict[str, Persona] = {}
    for persona_id, data in raw.get("personas", {}).items():
        # Create a raw PersonaConfig object
        persona_config = PersonaConfig(**data)

        # Generate the complete Persona with defaults filled in
        persona = create_persona_from_config(persona_id, persona_config, persona_defaults)
        pers[persona_id] = persona

    # read global game config
    game_section = raw.get("game", {})
    starting_agent = game_section.get("starting_agent")
    final_document = game_section.get("final_document")
    # build config
    config = GameConfig(
        documents=docs,
        evidence=evs,
        personas=pers,
        persona_defaults=persona_defaults,
        final_document=final_document,
        starting_agent=starting_agent,
    )

    # check that all document requirements that refer to documents are defined
    all_doc_ids = set(docs.keys())
    all_evidence_ids = set(evs.keys())
    for doc in docs.values():
        for req in doc.requirements:
            # if requirement is not evidence, it must be a document
            if req not in all_evidence_ids and req not in all_doc_ids:
                raise ValueError(f"Document '{doc.id}' requires '{req}', which is not defined as a document or evidence.")

    return config


def create_persona_from_config(persona_id: str, config: PersonaConfig, defaults: PersonaDefaults) -> Persona:
    """Create a complete Persona object from a minimal config, merging defaults and persona-specific rules."""
    # Merge behavioral_rules: defaults first, then persona-specific (if any)
    if config.behavioral_rules:
        behavioral_rules = defaults.behavioral_rules + [
            rule for rule in config.behavioral_rules if rule not in defaults.behavioral_rules
        ]
    else:
        behavioral_rules = defaults.behavioral_rules
    system_prompt_template = defaults.system_prompt_template

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
