"""
Game Logger module for capturing detailed game interactions, AI prompts, and state changes.
"""

import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union


class GameLogger:
    """
    A logger specifically designed for the Bürgeramt game to capture detailed
    interaction logs, AI prompts/responses, and game state changes.
    """

    def __init__(self, log_dir: str = ".log"):
        # Create log directory if it doesn't exist
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True, parents=True)
        
        # Generate timestamp for this game session
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = self.log_dir / f"game_session_{timestamp}.log"
        
        # Set up the logger
        self.logger = logging.getLogger("buergeramt_game")
        self.logger.setLevel(logging.DEBUG)
        
        # Create file handler
        file_handler = logging.FileHandler(self.log_file, mode="w", encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        
        # Create formatter
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        
        # Add handlers to logger
        self.logger.addHandler(file_handler)
        
        # Log session start
        self.logger.info(f"=== Game Session Started at {timestamp} ===")
        
    def log_user_input(self, user_input: str):
        """Log user input"""
        self.logger.info(f"USER INPUT: {user_input}")
        
    def log_ai_prompt(self, prompt: Union[str, Dict, list]):
        """Log the prompt sent to the AI model"""
        self.logger.debug(f"AI PROMPT: {self._format_object(prompt)}")
        
    def log_ai_response(self, response: Any):
        """Log the raw response from the AI model"""
        self.logger.debug(f"AI RESPONSE: {self._format_object(response)}")
        
    def log_agent_action(self, action: Dict):
        """Log structured actions from the agent"""
        self.logger.info(f"AGENT ACTION: {self._format_object(action)}")
        
    def log_state_change(self, name: str, old_value: Any, new_value: Any):
        """Log a change in game state"""
        self.logger.info(f"STATE CHANGE - {name}: {self._format_object(old_value)} -> {self._format_object(new_value)}")
        
    def log_procedure_transition(self, old_procedure: str, new_procedure: str, reason: str = "Normal transition"):
        """Log a procedure transition"""
        self.logger.info(f"PROCEDURE TRANSITION: {old_procedure} -> {new_procedure} (Reason: {reason})")
        
    def log_document_acquired(self, document_name: str):
        """Log when a document is acquired"""
        self.logger.info(f"DOCUMENT ACQUIRED: {document_name}")
        
    def log_evidence_provided(self, evidence_name: str, evidence_form: str):
        """Log when evidence is provided"""
        self.logger.info(f"EVIDENCE PROVIDED: {evidence_name} ({evidence_form})")
        
    def log_department_change(self, old_department: str, new_department: str):
        """Log a department change"""
        self.logger.info(f"DEPARTMENT CHANGE: {old_department} -> {new_department}")
        
    def log_game_state(self, game_state: Any):
        """Log the complete game state"""
        if hasattr(game_state, "get_formatted_gamestate"):
            # If it's our GameState object with the formatted method
            formatted_state = game_state.get_formatted_gamestate()
            self.logger.debug(f"GAME STATE: {formatted_state}")
        else:
            # Otherwise just log the object
            self.logger.debug(f"GAME STATE: {self._format_object(game_state)}")
            
    def log_error(self, error: Exception, context: Optional[str] = None):
        """Log an error"""
        message = f"ERROR: {str(error)}"
        if context:
            message = f"{message} (Context: {context})"
        self.logger.error(message)
        
    def log_win_condition(self, condition_met: bool, reason: str = ""):
        """Log win condition check"""
        self.logger.info(f"WIN CONDITION CHECK: {'Met' if condition_met else 'Not Met'} - {reason}")
        
    def log_ui_message(self, message: str, style: str):
        """Log a message displayed to the user"""
        self.logger.info(f"UI MESSAGE ({style}): {message}")
    
    def _format_object(self, obj: Any) -> str:
        """Format an object for logging"""
        if isinstance(obj, (dict, list)):
            return json.dumps(obj, ensure_ascii=False, indent=2)
        return str(obj)
        
    def get_log_file_path(self) -> str:
        """Get the path to the current log file"""
        return str(self.log_file)


# Singleton instance
_game_logger = None

def get_logger() -> GameLogger:
    """Get or create the singleton logger instance"""
    global _game_logger
    if _game_logger is None:
        _game_logger = GameLogger()
    return _game_logger