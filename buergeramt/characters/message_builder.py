import json

from buergeramt.rules import DOCUMENTS


class MessageBuilder:
    def __init__(self, system_prompt, example_interactions, context_manager):
        self.system_prompt = system_prompt
        self.example_interactions = example_interactions or []
        self.context_manager = context_manager

    def build(self, query, game_state, stage_guidance=None):
        messages = [{"role": "system", "content": self.system_prompt}]
        if len(self.context_manager.all()) < 2:
            for example in self.example_interactions:
                messages.append({"role": "user", "content": example["user"]})
                messages.append({"role": "assistant", "content": example["assistant"]})
        messages.extend(self.context_manager.get_recent(6))
        game_state_info = self._format_game_state(game_state)
        messages.append({"role": "system", "content": f"Current game state: {game_state_info}"})
        if stage_guidance:
            messages.append({"role": "system", "content": stage_guidance})
        messages.append({"role": "user", "content": query})
        return messages

    def _format_game_state(self, game_state):
        collected_documents = list(game_state.collected_documents.keys())
        evidence_provided = list(game_state.evidence_provided.keys())
        state_info = {
            "current_department": game_state.current_department,
            "current_procedure": game_state.current_procedure,
            "collected_documents": collected_documents,
            "evidence_provided": evidence_provided,
            "attempts": game_state.attempts,
            "frustration_level": game_state.frustration_level,
            "progress": game_state.progress,
            "department_documents": [
                doc for doc, data in DOCUMENTS.items() if data["department"] == game_state.current_department
            ],
            "missing_evidence": self._get_missing_evidence(game_state),
        }
        return json.dumps(state_info, indent=2)

    def _get_missing_evidence(self, game_state):
        missing = {}
        for doc_name, doc_data in DOCUMENTS.items():
            if doc_name not in game_state.collected_documents:
                required = doc_data["requirements"]
                missing_reqs = [req for req in required if req not in game_state.evidence_provided]
                if missing_reqs:
                    missing[doc_name] = missing_reqs
        return missing
