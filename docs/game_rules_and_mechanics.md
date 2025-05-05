# Game Rules and Game Mechanics

This document explains how the game rules defined in `game_rules.py` relate to the game mechanics implemented in the Bürgeramt Adventure game.

## Overview

The game simulates a bureaucratic process in a German government office, where the player must collect documents, provide evidence, and interact with AI-powered bureaucrats to complete the process of registering a gift for tax purposes. The rules and mechanics are tightly coupled to create a realistic and challenging experience.

## Game Rules (`game_rules.py`)

The `game_rules.py` file defines the core data structures and logic that govern the game's world:

- **DOCUMENTS**: A dictionary describing all official documents the player can obtain. Each document specifies:
  - The department responsible for issuing it
  - The requirements (evidence or other documents) needed to obtain it
  - A unique code and description

- **EVIDENCE**: A dictionary of all types of evidence the player may need to provide. Each evidence type lists:
  - Acceptable forms (e.g., Personalausweis, Notarielle Urkunde)
  - Which documents or steps require this evidence

- **PROCEDURES**: A dictionary of bureaucratic procedures, each with:
  - The department responsible
  - Keywords that trigger the procedure
  - Required documents or evidence

- **GameState**: A class that tracks the player's progress, collected documents, provided evidence, current department, and frustration level.

## Game Mechanics

The game mechanics, implemented in `game_engine.py` and related files, use the rules from `game_rules.py` to drive gameplay:

- **Document Acquisition**: When the player requests a document, the game checks the `DOCUMENTS` rules to determine if the player meets all requirements. If so, the document is granted; otherwise, the game provides hints about missing requirements.

- **Evidence Submission**: The player can submit evidence by mentioning it in their input. The game matches the input to entries in `EVIDENCE` and updates the game state accordingly. Some documents or procedures require specific evidence before they can proceed.

- **Procedures and Department Transfers**: The player must interact with different departments, each responsible for certain procedures and documents. The `PROCEDURES` rules define which actions are available in each department and what is required to complete them.

- **AI Bureaucrats**: AI-powered characters use the rules to check requirements, provide hints, and respond to player actions. They enforce the rules and simulate realistic bureaucratic behavior.

- **Progress and Frustration**: The game state tracks progress based on collected documents and completed procedures. Frustration increases when the player makes mistakes or lacks required items, adding a challenge and realism to the experience.

## Summary

The rules in `game_rules.py` serve as the foundation for all game logic. The mechanics implemented in the engine and AI characters reference these rules to:
- Validate player actions
- Determine available options
- Provide feedback and hints
- Simulate the complexity of real-world bureaucracy

This separation of rules and mechanics makes the game extensible and maintainable, allowing new documents, evidence, or procedures to be added easily by updating the rules file.
