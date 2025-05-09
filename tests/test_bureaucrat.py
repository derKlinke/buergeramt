from unittest.mock import MagicMock

import pytest

from buergeramt.characters.agent_response import AgentResponse
from buergeramt.characters.bureaucrat import Bureaucrat
from buergeramt.rules.game_state import GameState


class DummyGameState:
    def get_formatted_gamestate(self):
        return "dummy game state"
    # ...add any other methods needed for tests...

@pytest.fixture
def dummy_bureaucrat():
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
    class DummyAgentRunResult:
        def __init__(self):
            self.output = type('Output', (), {'response_text': 'ok'})()
            self.response = "raw response"
    dummy_bureaucrat.agent.run_sync = MagicMock(return_value=DummyAgentRunResult())
    game_state = DummyGameState()
    # should not raise AttributeError, should return a string response
    response = dummy_bureaucrat.respond("ich habe ein geschenk bekommen", game_state)
    assert isinstance(response, str)
    assert response == "ok"
