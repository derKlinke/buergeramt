from buergeramt.rules.game_state import GameState
from buergeramt.rules.loader import get_config


def test_find_win_path():
    config = get_config()
    gs = GameState()
    # build dependency graph for documents
    doc_graph = {}
    for doc_id, doc in config.documents.items():
        doc_graph[doc_id] = set(doc.requirements)
    # find path to final document
    final_doc = config.final_document
    assert final_doc in doc_graph
    # topological sort for dependency order
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

    visit(final_doc)
    # do not reverse order; post-order DFS ensures dependencies first
    for doc_id in order:
        doc = config.documents[doc_id]
        for req in doc.requirements:
            if req in config.evidence:
                form = config.evidence[req].acceptable_forms[0]
                gs.add_evidence(req, form)
        gs.current_department = doc.department
        result = gs.add_document(doc_id)
        if doc_id == final_doc:
            print(f"Result of adding final doc: {result}")
    assert final_doc in gs.collected_documents
