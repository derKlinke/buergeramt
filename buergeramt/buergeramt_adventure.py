import os
from dotenv import load_dotenv
import time
import argparse

from buergeramt.game_engine import GameEngine


def clear_screen():
    """Clear the console screen"""
    os.system("cls" if os.name == "nt" else "clear")


def print_progress(game_engine):
    """Print progress bar"""
    progress = game_engine.game_state.progress
    frustration = game_engine.game_state.frustration_level

    # Progress bar
    bar_length = 20
    filled_length = int(bar_length * progress / 100)
    bar = "█" * filled_length + "░" * (bar_length - filled_length)

    # Frustration indicator
    frustration_bar = "!" * frustration

    print(f"\nFortschritt: [{bar}] {progress}%  Frustration: {frustration_bar}")


def setup_api_key():
    """Check for and set up OpenAI API key"""
    if "OPENAI_API_KEY" not in os.environ or not os.environ["OPENAI_API_KEY"]:
        key = input("OpenAI API Key: ").strip()
        if key:
            os.environ["OPENAI_API_KEY"] = key
            return True
        else:
            print("Das Spiel benötigt einen OpenAI API Key, um zu funktionieren.")
            print("Sie können diesen als Umgebungsvariable setzen: export OPENAI_API_KEY=sk-...")
            print("Oder beim Spielstart mit --api-key=sk-... übergeben.")
            return False
    return True


def main():
    """Main game function"""
    load_dotenv()

    parser = argparse.ArgumentParser(description="Bürgeramt Adventure: Schenkungssteuer Edition")
    parser.add_argument("--api-key", help="OpenAI API key")
    args = parser.parse_args()

    # Set API key if provided as argument
    if args.api_key:
        os.environ["OPENAI_API_KEY"] = args.api_key

    # Check if API key is available
    if not setup_api_key():
        return

    clear_screen()
    print("Initialisiere das Finanzamt...")
    print("Verbinde mit KI-Beamten...")
    time.sleep(1)

    # Create game
    game = GameEngine()

    # Check if game initialized successfully
    if game.game_over:
        return

    # Start the game
    game.start_game()

    # Main game loop
    while not game.game_over:
        # Show progress
        print_progress(game)

        # Get user input
        user_input = input("\n> ")

        # Process input
        if not game.process_input(user_input):
            break

    # Game over, check if player won
    if hasattr(game, "win_condition") and game.win_condition:
        print("\nGlückwunsch! Sie haben das deutsche Bürokratiesystem besiegt.")
    else:
        print("\nVielen Dank für Ihren Besuch im Finanzamt. Kommen Sie bald wieder.")


# allow running as a module: python -m buergeramt
def run():
    try:
        main()
    except KeyboardInterrupt:
        print("\nBeenden des Programms...")
    except Exception as e:
        print(f"Ein unerwarteter Fehler ist aufgetreten: {e}")
        import traceback

        traceback.print_exc()
