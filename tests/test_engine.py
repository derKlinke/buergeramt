import pytest

from buergeramt.engine.game_engine import GameEngine


def test_game_engine_init_without_ai_characters():
    engine = GameEngine(use_ai_characters=False)
    assert engine.game_state is not None
    # when AI characters disabled, agent_router should be None
    assert getattr(engine, 'agent_router', None) is None
    assert engine.use_ai_characters is False
