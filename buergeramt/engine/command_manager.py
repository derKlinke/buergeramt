from typing import Callable, Dict, List, Optional


class Command:
    def __init__(
        self,
        name: str,
        handler: Callable,
        description: str,
        takes_argument: bool = False,
        argument_suggestions: Optional[Callable[[], List[str]]] = None,
    ):
        self.name = name
        self.handler = handler
        self.description = description
        self.takes_argument = takes_argument
        self.argument_suggestions = argument_suggestions


class CommandManager:
    def __init__(self):
        self.commands: Dict[str, Command] = {}

    def register(
        self,
        name: str,
        handler: Callable,
        description: str,
        takes_argument: bool = False,
        argument_suggestions: Optional[Callable[[], List[str]]] = None,
    ):
        self.commands[name] = Command(name, handler, description, takes_argument, argument_suggestions)

    def get_command(self, name: str) -> Optional[Command]:
        return self.commands.get(name)

    def get_suggestions(self, partial: str) -> List[str]:
        return [cmd for cmd in self.commands if cmd.startswith(partial)]

    def get_argument_suggestions(self, name: str) -> List[str]:
        cmd = self.get_command(name)
        if cmd and cmd.argument_suggestions:
            return cmd.argument_suggestions()
        return []

    def all_commands(self) -> List[Command]:
        return list(self.commands.values())
