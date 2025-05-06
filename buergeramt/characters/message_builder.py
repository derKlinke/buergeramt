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
        
        game_state_info = game_state.get_formatted_gamestate()
        messages.append({"role": "system", "content": f"Current game state: {game_state_info}"})
        
        if stage_guidance:
            messages.append({"role": "system", "content": stage_guidance})
        messages.append({"role": "user", "content": query})
        
        return messages
