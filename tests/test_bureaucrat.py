from unittest.mock import MagicMock

import pytest

from buergeramt.characters.agent_response import AgentResponse
from buergeramt.characters.bureaucrat import Bureaucrat


class DummyGameState:
    def get_formatted_gamestate(self):
        return "dummy game state"

@pytest.fixture
def dummy_bureaucrat():
    # minimal Bureaucrat with mocked logger and agent
    bureaucrat = Bureaucrat(
        name="Test",
        title="Beamter",
        department="Testabteilung",
        system_prompt="Test system prompt"
    )
    bureaucrat.logger = MagicMock()
    return bureaucrat

def test_respond_agentrunresult_missing_messages(dummy_bureaucrat, monkeypatch):
    # simulate Agent.run returning an object without 'messages' attribute
    from buergeramt.characters.agent_response import AgentActions
    class DummyAgentRunResult:
        def __init__(self):
            self.output = AgentResponse(
                response_text="ok",
                actions=AgentActions(
                    intent=None,
                    document=None,
                    requirements_met=None,
                    evidence=None,
                    department=None,
                    procedure=None,
                    next_procedure=None,
                    procedure_transition=None,
                    valid=True,
                    message=""
                )
            )
            self.response = "raw response"
    dummy_bureaucrat.agent.run = MagicMock(return_value=DummyAgentRunResult())
    game_state = DummyGameState()
    # should not raise AttributeError, should return valid AgentResponse
    response = dummy_bureaucrat.respond("ich habe ein geschenk bekommen", game_state)
    assert isinstance(response, type(dummy_bureaucrat.agent.run().output))
    assert response.response_text == "ok"
