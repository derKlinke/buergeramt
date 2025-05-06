import argparse
import io
import os
import sys
import time

from dotenv import load_dotenv

from buergeramt.engine.command_manager import CommandManager
from buergeramt.engine.game_engine import GameEngine

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8", errors="replace")


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




# --- CommandManager setup ---
def setup_commands(game):
    command_manager = CommandManager()

    def cmd_hilfe(arg=None):
        print("\nVerfügbare Befehle:")
        for cmd in command_manager.all_commands():
            print(f"/{cmd.name}{' <argument>' if cmd.takes_argument else ''}: {cmd.description}")
        return True

    def cmd_status(arg=None):
        print_progress(game)
        return True

    def cmd_beenden(arg=None):
        print("Spiel wird beendet.")
        sys.exit(0)

    def agent_suggestions():
        # Suggest agent names from the game engine (use bureaucrat names)
        if hasattr(game, 'agent_router'):
            return [b.name for b in game.agent_router.get_bureaucrats().values()]
        return []

    def cmd_gehe_zu(arg):
        if not arg:
            print("Bitte geben Sie einen Agentennamen an. Beispiel: /gehe_zu Frau Müller")
            return True
        # Try to switch agent in the game engine
        if hasattr(game, 'switch_agent'):
            if game.switch_agent(arg):
                print(f"Sie sprechen jetzt mit {arg}.")
            else:
                print(f"Agent oder Abteilung '{arg}' nicht gefunden.")
        else:
            print("Agentenwechsel ist in diesem Spielmodus nicht verfügbar.")
        return True

    # Register commands
    command_manager.register("hilfe", cmd_hilfe, "Zeigt diese Hilfe an.")
    command_manager.register("status", cmd_status, "Zeigt den aktuellen Fortschritt und Frustrationslevel an.")
    command_manager.register("beenden", cmd_beenden, "Beendet das Spiel.")
    command_manager.register("gehe_zu", cmd_gehe_zu, "Wechselt zu einem anderen Beamten (z.B. /gehe_zu Frau Müller)",
                             takes_argument=True, argument_suggestions=agent_suggestions)
    return command_manager


def main():
    load_dotenv()
    parser = argparse.ArgumentParser(description="Bürgeramt Adventure: Schenkungssteuer Edition")
    parser.add_argument("--api-key", help="OpenAI API key")
    args = parser.parse_args()
    if args.api_key:
        os.environ["OPENAI_API_KEY"] = args.api_key
    if not setup_api_key():
        return
    clear_screen()
    print("Initialisiere das Finanzamt...")
    print("Verbinde mit KI-Beamten...")
    time.sleep(1)
    game = GameEngine()
    if game.game_over:
        return
    game.start_game()

    command_manager = setup_commands(game)

    # Main game loop with slash command support
    while not game.game_over:
        print_progress(game)
        user_input = input("\n> ")
        if user_input.startswith("/"):
            # Parse command
            parts = user_input[1:].split(maxsplit=1)
            cmd_name = parts[0]
            arg = parts[1] if len(parts) > 1 else None
            cmd = command_manager.get_command(cmd_name)
            if cmd:
                cmd.handler(arg)
                continue
            else:
                # Suggest closest command
                suggestions = command_manager.get_suggestions(cmd_name)
                if suggestions:
                    print(f"Unbekannter Befehl. Meinten Sie: {', '.join('/' + s for s in suggestions)}?")
                else:
                    print("Unbekannter Befehl. Geben Sie /hilfe für eine Liste aller Befehle ein.")
                continue
        # Process normal input
        if not game.process_input(user_input):
            break
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
