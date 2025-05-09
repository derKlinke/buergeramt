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


    # Build system prompt using the template, and add explicit tool usage instructions
    tool_instructions = (
        "\n---\n"
        "You have access to the following tools for updating the game state. Whenever the user provides a document, evidence, or requests a procedure change, always use the appropriate tool. Do not just mention the action, always call the tool.\n"
        "\n"
        "Tool usage examples:\n"
        "- If the user says 'Hier ist mein Personalausweis', call add_evidence with evidence_name='valid_id', evidence_form='Personalausweis'.\n"
        "- If the user says 'Ich reiche die Schenkungsanmeldung ein', call add_document with document_name='Schenkungsanmeldung'.\n"
        "- If the user says 'Ich möchte zur nächsten Abteilung', call transition_procedure with next_procedure='<target_procedure>'.\n"
        "- If the user expresses frustration (e.g., 'Das ist doch lächerlich!'), call increase_frustration.\n"
        "- If the user calms down, call decrease_frustration.\n"
        "\n"
        "Tool reference:\n"
        "- add_document(document_name: str)\n"
        "- add_evidence(evidence_name: str, evidence_form: str)\n"
        "- transition_procedure(next_procedure: str)\n"
        "- increase_frustration(amount: int = 1)\n"
        "- decrease_frustration(amount: int = 1)\n"
        "---\n"
    )
    system_prompt = p.system_prompt_template.format(
        name=p.name,
        role=p.role,
        department=p.department,
        personality=personality_text,
        handled_documents=handled_docs,
        required_evidence=required_evidence,
    ) + tool_instructions

    # Create and return the Bureaucrat instance
    return Bureaucrat(
        name=p.name,
        title=p.role,
        department=p.department,
        system_prompt=system_prompt,
    )
