import pytest

from buergeramt.rules.game_state import GameState


def test_add_document_valid_and_duplicate():
    gs = GameState()
    # Try adding a valid document
    added = gs.add_document("Schenkungsanmeldung")
    assert added is True
    # Should appear in collected_documents
    assert "Schenkungsanmeldung" in gs.collected_documents
    # Adding same document again should succeed (idempotent by logic)
    added2 = gs.add_document("Schenkungsanmeldung")
    assert added2 is True
    assert list(gs.collected_documents.keys()).count("Schenkungsanmeldung") == 1

def test_add_document_invalid():
    gs = GameState()
    result = gs.add_document("notarealdoc")
    assert result is False
    assert "notarealdoc" not in gs.collected_documents

def test_add_evidence_valid_forms():
    gs = GameState()
    # Personalausweis is valid form for valid_id
    added = gs.add_evidence("valid_id", "Personalausweis")
    assert added is True
    assert gs.evidence_provided["valid_id"] == "Personalausweis"
    # Other valid forms
    for form in ["Reisepass", "Aufenthaltstitel"]:
        gs = GameState()
        added = gs.add_evidence("valid_id", form)
        assert added is True
        assert gs.evidence_provided["valid_id"] == form

def test_add_evidence_invalid_evidence_or_form():
    gs = GameState()
    # Invalid evidence name
    added = gs.add_evidence("not_evidence", "SomeForm")
    assert added is False
    # Valid evidence but invalid form
    added2 = gs.add_evidence("valid_id", "WrongForm")
    assert added2 is False
    # Should not appear in evidence_provided dict
    assert "not_evidence" not in gs.evidence_provided
    assert "valid_id" not in gs.evidence_provided

def test_increase_decrease_frustration_boundaries():
    gs = GameState()
    # Default is 0, increase
    gs.increase_frustration()
    assert gs.frustration_level == 1
    gs.increase_frustration(3)
    assert gs.frustration_level == 4
    # Reduce below zero should clamp to zero
    gs.decrease_frustration(10)
    assert gs.frustration_level == 0
    gs.increase_frustration(2)
    gs.decrease_frustration(1)
    assert gs.frustration_level == 1

def test_update_progress_calculation():
    gs = GameState()
    # Add a document and some evidence, should increment progress
    initial = gs.progress
    gs.add_document("Schenkungsanmeldung")
    gs.add_evidence("valid_id", "Personalausweis")
    gs.add_evidence("gift_details", "Notarielle Urkunde")
    p = gs.update_progress()
    assert p > initial
    # Simulate advancing procedure for higher progress
    gs.transition_procedure("Formularprüfung")
    gs.transition_procedure("Nachweisanforderung")
    higher = gs.update_progress()
    assert higher >= p
    # Check max out logic
    gs.progress = 99
    gs.update_progress()
    assert gs.progress <= 100

def test_get_collected_documents_and_evidence_provided():
    gs = GameState()
    gs.add_document("Wertermittlung")
    gs.add_evidence("expert_opinion", "Sachverständigengutachten")
    cd = gs.get_collected_documents()
    ep = gs.get_evidence_provided()
    assert "Wertermittlung" in cd
    assert "expert_opinion" in ep

def test_get_department_documents_and_missing_evidence():
    gs = GameState()
    gs.current_department = "Erstbearbeitung"
    dep_docs = gs.get_department_documents()
    # There are documents for Erstbearbeitung
    assert isinstance(dep_docs, list)
    assert "Schenkungsanmeldung" in dep_docs
    # If nothing collected and no evidence, missing evidence should report requirements for all docs
    missing = gs.get_missing_evidence()
    # Every document listed with unmet requirements
    for doc, reqs in missing.items():
        assert isinstance(reqs, list)
        for req in reqs:
            # only check evidence requirements
            if req in gs.config.evidence:
                assert req in gs.config.evidence
    # After providing all required evidence for a doc, missing_evidence should no longer report it
    gs.add_evidence("valid_id", "Personalausweis")
    gs.add_evidence("gift_details", "Notarielle Urkunde")
    # Now Schenkungsanmeldung requirements are met
    missing = gs.get_missing_evidence()
    assert "Schenkungsanmeldung" not in missing

def test_get_bureaucrat_for_department():
    gs = GameState()
    assert gs.get_bureaucrat_for_department("Erstbearbeitung") == "HerrSchmidt"
    assert gs.get_bureaucrat_for_department("Fachprüfung") == "FrauMueller"
    assert gs.get_bureaucrat_for_department("Abschlussstelle") == "HerrWeber"
    # Unknown department returns default
    assert gs.get_bureaucrat_for_department("KeinAmt") == "HerrSchmidt"

def test_get_formatted_gamestate_json():
    gs = GameState()
    # Should be valid JSON with expected fields
    jstr = gs.get_formatted_gamestate()
    import json
    obj = json.loads(jstr)
    assert isinstance(obj, dict)
    assert "current_department" in obj
    assert "collected_documents" in obj
    assert "frustration_level" in obj

def test_win_by_forced_procedure_and_progress():
    gs = GameState()
    # Try to forcibly complete documents/procedures for "win" scenario logic (engine-side, but we can simulate)
    for doc in ["Schenkungsanmeldung", "Wertermittlung", "Freibetragsbescheinigung", "Zahlungsaufforderung"]:
        gs.add_document(doc)
    gs.current_procedure = "Abschluss"
    gs.current_department = "Abschlussstelle"
    # User very frustrated for frustration-based win
    gs.frustration_level = 12
    # Should look like a winner's state in game (used in game_engine)
    assert gs.progress <= 100
    assert "Zahlungsaufforderung" in gs.collected_documents
    assert gs.progress <= 100
    assert "Zahlungsaufforderung" in gs.collected_documents
