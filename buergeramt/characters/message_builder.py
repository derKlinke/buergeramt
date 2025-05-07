class MessageBuilder:
    def __init__(self, system_prompt, context_manager):
        self.system_prompt = system_prompt
        self.context_manager = context_manager

    def build(self, query, game_state, stage_guidance=None):
        messages = [{"role": "system", "content": self.system_prompt}]

        messages.extend(self.context_manager.get_recent(6))

        game_state_info = game_state.get_formatted_gamestate()
        messages.append({"role": "system", "content": f"Current game state: {game_state_info}"})

        if stage_guidance:
            messages.append({"role": "system", "content": stage_guidance})
        messages.append({"role": "user", "content": query})

        return messages
