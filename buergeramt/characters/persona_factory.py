from buergeramt.characters.bureaucrat import Bureaucrat
from buergeramt.rules.loader import get_config
from buergeramt.rules.models import Persona


def build_bureaucrat(persona_id: str) -> Bureaucrat:
    """instantiate a Bureaucrat from config by persona id"""
    config = get_config()
    if persona_id not in config.personas:
        raise KeyError(f"Persona '{persona_id}' not found in config")
    p: Persona = config.personas[persona_id]

    # Format personality list for the system prompt
    personality_text = "\n".join(f"- {trait}" for trait in p.personality)

    # Format handled documents and required evidence as comma-separated lists
    handled_docs = ", ".join(p.handled_documents)
    required_evidence = ", ".join(p.required_evidence)

    # Build system prompt using the template
    system_prompt = p.system_prompt_template.format(
        name=p.name,
        role=p.role,
        department=p.department,
        personality=personality_text,
        handled_documents=handled_docs,
        required_evidence=required_evidence,
    )

    # Create and return the Bureaucrat instance
    return Bureaucrat(
        name=p.name,
        title=p.role,
        department=p.department,
        system_prompt=system_prompt,
    )
