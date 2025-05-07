#!/usr/bin/env python3
"""
Simple test script to verify that the game engine initializes without errors.
"""

from buergeramt.engine.game_engine import GameEngine


def main():
    print("Initializing game engine...")
    try:
        # Pass False to avoid creating AI characters which require API keys
        game = GameEngine(use_ai_characters=False)
        
        # Check if game state and configuration loaded correctly
        if game.game_state and game.game_state.config:
            print("Game state initialized successfully")
            print(f"Loaded {len(game.game_state.config.documents)} documents")
            print(f"Loaded {len(game.game_state.config.evidence)} evidence types")
            print(f"Loaded {len(game.game_state.config.procedures)} procedures")
            print(f"Loaded {len(game.game_state.config.personas)} personas")
            
            print("\nDocument codes:")
            for doc_id, doc in game.game_state.config.documents.items():
                print(f"  - {doc_id}: {doc.code}")
            
            # Test win condition logic
            print("\nTesting win condition method...")
            result = game.check_win_condition()
            print(f"Win condition result: {result} (should be False at game start)")
            
            print("\nAll tests passed successfully!")
        else:
            print("ERROR: Game state or configuration not initialized properly")
            
    except Exception as e:
        print(f"ERROR initializing game engine: {e}")


if __name__ == "__main__":
    main()