import pytest

from buergeramt.rules.loader import get_config


def test_get_config_structure():
    config = get_config()
    assert hasattr(config, "documents")
    assert hasattr(config, "evidence")
    assert hasattr(config, "procedures")
    assert hasattr(config, "personas")
    assert isinstance(config.documents, dict)
    assert isinstance(config.evidence, dict)
    assert isinstance(config.procedures, dict)
    assert isinstance(config.personas, dict)
    assert len(config.personas) > 0


def test_persona_templates_and_formatting():
    config = get_config()
    for persona_id, persona in config.personas.items():
        # template defined and non-empty
        template = persona.system_prompt_template
        assert template and isinstance(template, str)
        # formatting should succeed
        personality_text = "\n".join(f"- {t}" for t in persona.personality)
        handled_docs = ", ".join(persona.handled_documents)
        required_evidence = ", ".join(persona.required_evidence)
        formatted = template.format(
            name=persona.name,
            role=persona.role,
            department=persona.department,
            personality=personality_text,
            handled_documents=handled_docs,
            required_evidence=required_evidence,
        )
        assert isinstance(formatted, str)
