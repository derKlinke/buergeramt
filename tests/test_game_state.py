from buergeramt.rules.game_state import GameState
from buergeramt.rules.loader import get_config


def test_add_document_valid_and_duplicate():
    config = get_config()
    gs = GameState()
    doc_id = next(iter(config.documents))
    # provide all required evidence
    for req in config.documents[doc_id].requirements:
        if req in config.evidence:
            form = config.evidence[req].acceptable_forms[0]
            gs.add_evidence(req, form)
    gs.current_department = config.documents[doc_id].department
    added = gs.add_document(doc_id)
    assert isinstance(added, str) or added is True
    assert doc_id in gs.collected_documents
    added2 = gs.add_document(doc_id)
    assert isinstance(added2, str) or added2 is True
    assert list(gs.collected_documents.keys()).count(doc_id) == 1


def test_add_document_invalid():
    gs = GameState()
    result = gs.add_document("notarealdoc")
    assert result is not True
    assert "notarealdoc" not in gs.collected_documents


def test_add_evidence_valid_forms():
    config = get_config()
    gs = GameState()
    evid_id = next(iter(config.evidence))
    form = config.evidence[evid_id].acceptable_forms[0]
    added = gs.add_evidence(evid_id, form)
    assert added is True
    assert gs.evidence_provided[evid_id] == form
    for form in config.evidence[evid_id].acceptable_forms:
        gs = GameState()
        added = gs.add_evidence(evid_id, form)
        assert added is True
        assert gs.evidence_provided[evid_id] == form


def test_add_evidence_invalid_evidence_or_form():
    config = get_config()
    gs = GameState()
    added = gs.add_evidence("not_evidence", "SomeForm")
    assert added is False
    evid_id = next(iter(config.evidence))
    added2 = gs.add_evidence(evid_id, "WrongForm")
    assert added2 is False
    assert "not_evidence" not in gs.evidence_provided
    assert evid_id not in gs.evidence_provided


def test_increase_decrease_frustration_boundaries():
    gs = GameState()
    gs.increase_frustration()
    assert gs.frustration_level == 1
    gs.increase_frustration(3)
    assert gs.frustration_level == 4
    gs.decrease_frustration(10)
    assert gs.frustration_level == 0
    gs.increase_frustration(2)
    gs.decrease_frustration(1)
    assert gs.frustration_level == 1


def test_update_progress_calculation():
    config = get_config()
    gs = GameState()
    doc_id = next(iter(config.documents))
    gs.current_department = config.documents[doc_id].department
    initial = gs.progress
    gs.add_document(doc_id)
    evid_id = next(iter(config.evidence))
    form = config.evidence[evid_id].acceptable_forms[0]
    gs.add_evidence(evid_id, form)
    p = gs.update_progress()
    assert p >= initial
    gs.progress = 99
    gs.update_progress()
    assert gs.progress <= 100


def test_get_collected_documents_and_evidence_provided():
    config = get_config()
    gs = GameState()
    doc_id = next(iter(config.documents))
    # provide all required evidence
    for req in config.documents[doc_id].requirements:
        if req in config.evidence:
            form = config.evidence[req].acceptable_forms[0]
            gs.add_evidence(req, form)
    gs.current_department = config.documents[doc_id].department
    gs.add_document(doc_id)
    evid_id = next(iter(config.evidence))
    form = config.evidence[evid_id].acceptable_forms[0]
    gs.add_evidence(evid_id, form)
    cd = gs.get_collected_documents()
    ep = gs.get_evidence_provided()
    assert doc_id in cd
    assert evid_id in ep


def test_get_department_documents_and_missing_evidence():
    config = get_config()
    gs = GameState()
    department = next(iter(set(doc.department for doc in config.documents.values())))
    gs.current_department = department
    dep_docs = gs.get_department_documents()
    assert isinstance(dep_docs, list)
    assert any(doc in dep_docs for doc in config.documents)
    missing = gs.get_missing_evidence()
    for doc, reqs in missing.items():
        assert isinstance(reqs, list)
        for req in reqs:
            if req in gs.config.evidence:
                assert req in gs.config.evidence
    # provide evidence for first doc in department
    doc_id = dep_docs[0]
    for req in config.documents[doc_id].requirements:
        if req in config.evidence:
            form = config.evidence[req].acceptable_forms[0]
            gs.add_evidence(req, form)
    missing = gs.get_missing_evidence()
    assert doc_id not in missing


def test_get_bureaucrat_for_department():
    gs = GameState()
    assert isinstance(gs.get_bureaucrat_for_department("Erstbearbeitung"), str)
    assert isinstance(gs.get_bureaucrat_for_department("Fachprüfung"), str)
    assert isinstance(gs.get_bureaucrat_for_department("Abschlussstelle"), str)
    assert isinstance(gs.get_bureaucrat_for_department("KeinAmt"), str)


def test_get_formatted_gamestate_json():
    gs = GameState()
    jstr = gs.get_formatted_gamestate()
    import json

    obj = json.loads(jstr)
    assert isinstance(obj, dict)
    assert "current_department" in obj
    assert "collected_documents" in obj
    assert "frustration_level" in obj


def test_win_by_forced_procedure_and_progress():
    config = get_config()
    gs = GameState()
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
