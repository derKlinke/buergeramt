from buergeramt.characters.bureaucrat import Bureaucrat
from buergeramt.rules.loader import get_config
from buergeramt.rules.persona import Persona


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

    # Build detailed info for handled documents
    doc_infos = []
    for doc_id in p.handled_documents:
        doc = config.documents.get(doc_id)
        if doc:
            reqs = ", ".join(doc.requirements)
            doc_infos.append(f"- {doc_id}: {doc.description} (benötigte Nachweise: {reqs})")
    docs_section = "\n".join(doc_infos)

    # Build detailed info for required evidence
    evidence_infos = []
    for ev_id in p.required_evidence:
        ev = config.evidence.get(ev_id)
        if ev:
            forms = ", ".join(ev.acceptable_forms)
            evidence_infos.append(f"- {ev_id}: {ev.description} (akzeptierte Formen: {forms})")
    evidence_section = "\n".join(evidence_infos)

    # Add info about other agents' handled documents
    other_agents_docs = []
    for other_id, other_p in config.personas.items():
        if other_id == persona_id:
            continue
        other_docs = []
        for doc_id in other_p.handled_documents:
            doc = config.documents.get(doc_id)
            if doc:
                other_docs.append(f"- {doc_id}: {doc.description}")
        if other_docs:
            other_agents_docs.append(
                f"{other_p.name} ({other_p.role}, {other_p.department}):\n" + "\n".join(other_docs)
            )
    others_section = "\n\n".join(other_agents_docs)
    if others_section:
        others_section = f"\n## DOKUMENTE DER ANDEREN ABTEILUNGEN\n{others_section}\n"

    # Add to system prompt
    persona_context = (
        f"\n## DOKUMENTE DIE SIE BEARBEITEN\n{docs_section}\n"
        f"\n## NACHWEISE DIE SIE PRÜFEN\n{evidence_section}\n"
        f"{others_section if others_section else ''}"
    )

    # Add behavioral rules section
    behavioral_rules_section = "\n## VERHALTENSREGELN\n" + "\n".join(f"- {rule}" for rule in p.behavioral_rules) + "\n"

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
    system_prompt = (
        p.system_prompt_template.format(
            name=p.name,
            role=p.role,
            department=p.department,
            personality=personality_text,
            handled_documents=handled_docs,
            required_evidence=required_evidence,
        )
        + behavioral_rules_section
        + persona_context
        + tool_instructions
    )

    # Create and return the Bureaucrat instance
    return Bureaucrat(
        name=p.name,
        title=p.role,
        department=p.department,
        system_prompt=system_prompt,
    )
