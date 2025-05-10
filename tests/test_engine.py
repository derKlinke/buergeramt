import pytest

from buergeramt.engine.game_engine import GameEngine


def test_game_engine_init_without_ai_characters():
    engine = GameEngine(use_ai_characters=False)
    assert engine.game_state is not None
    # when AI characters disabled, agent_router should be None
    assert getattr(engine, 'agent_router', None) is None
    assert engine.use_ai_characters is False


def test_engine_minimal_progression_flow(monkeypatch):
    from buergeramt.engine.game_engine import GameEngine
    engine = GameEngine(use_ai_characters=False)
    gs = engine.game_state
    config = gs.config
    doc_graph = {doc_id: set(doc.requirements) for doc_id, doc in config.documents.items()}
    visited = set()
    order = []

    def visit(doc_id):
        if doc_id in visited:
            return
        for req in doc_graph[doc_id]:
            if req in config.documents:
                visit(req)
        order.append(doc_id)
        visited.add(doc_id)

    for doc_id in config.documents:
        visit(doc_id)
    # add all except final doc
    for doc_id in order:
        if doc_id == config.final_document:
            continue
        doc = config.documents[doc_id]
        for req in doc.requirements:
            if req in config.evidence:
                form = config.evidence[req].acceptable_forms[0]
                gs.add_evidence(req, form)
        gs.current_department = doc.department
        gs.add_document(doc_id)
    # now add final doc
    final_doc = config.final_document
    doc = config.documents[final_doc]
    for req in doc.requirements:
        if req in config.evidence:
            form = config.evidence[req].acceptable_forms[0]
            gs.add_evidence(req, form)
    gs.current_department = doc.department
    gs.add_document(final_doc)
    gs.current_department = doc.department
    gs.frustration_level = 12
    for doc_id in config.documents:
        assert doc_id in gs.collected_documents
    assert gs.progress <= 100
