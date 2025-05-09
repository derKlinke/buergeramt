# agent/AI integration and end-to-end tests
import pytest

from buergeramt.characters.bureaucrat import Bureaucrat
from buergeramt.rules.game_state import GameState


def test_agent_tool_end_to_end_add_evidence():
    game_state = GameState()
    system_prompt = (
        "You are a bureaucratic AI agent. Whenever the user provides a document or evidence, you MUST call the add_evidence tool with the correct evidence_name and evidence_form. "
        "For 'Personalausweis', call add_evidence with evidence_name='valid_id' and evidence_form='Personalausweis'. "
        "Do not just mention the action, always call the tool."
    )
    bureaucrat = Bureaucrat(
        "Herr Schmidt",
        "Oberamtsrat",
        "Erstbearbeitung",
        system_prompt
    )
    user_input = "Hier ist mein Personalausweis."
    try:
        response = bureaucrat.respond(user_input, game_state)
    except RuntimeError as e:
        pytest.fail(f"Agent failed to respond: {e}")
    assert any(
        ev.lower() == "valid_id" and form.lower() == "personalausweis"
        for ev, form in game_state.evidence_provided.items()
    ), f"GameState did not add valid_id evidence for Personalausweis: {game_state.evidence_provided}"


def test_bureaucrat_agent_tool_context_integration():
    game_state = GameState()
    test_system_prompt = (
        "You are a bureaucratic AI agent. Whenever the user provides a document or evidence, you MUST call the add_evidence tool with the correct evidence_id and form. "
        "For 'Personalausweis', call add_evidence with evidence_id='valid_id' and form='Personalausweis'. "
        "Do not just mention the action, always call the tool."
    )
    bureaucrat = Bureaucrat(
        "Herr Schmidt",
        "Oberamtsrat",
        "Erstbearbeitung",
        test_system_prompt
    )
    user_input = "Ich habe meinen Personalausweis dabei."
    try:
        response = bureaucrat.respond(user_input, game_state)
    except RuntimeError as e:
        pytest.fail(f"Agent failed to respond: {e}")
    assert any(
        ev.lower() == "valid_id" and form.lower() == "personalausweis"
        for ev, form in game_state.evidence_provided.items()
    ), f"GameState did not add valid_id evidence for Personalausweis: {game_state.evidence_provided}"
