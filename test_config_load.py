#!/usr/bin/env python3
"""
Test script to verify that the config loader works with the simplified persona structure.
This script just tests the config loading without creating actual Bureaucrat instances.
"""

from buergeramt.rules.loader import get_config
from buergeramt.rules.models import Persona


def main():
    print("Loading configuration...")
    config = get_config()
    
    print(f"\nLoaded {len(config.personas)} personas, "
          f"{len(config.documents)} documents, "
          f"{len(config.evidence)} evidence types, and "
          f"{len(config.procedures)} procedures\n")
    
    print("Personas in config:")
    for persona_id in config.personas:
        print(f"  - {persona_id}")
    
    print("\nChecking persona details:\n")
    
    for persona_id, persona in config.personas.items():
        print(f"=== Details for {persona_id} ===")
        print(f"Name: {persona.name}")
        print(f"Role: {persona.role}")
        print(f"Department: {persona.department}")
        print(f"Personality traits: {len(persona.personality)}")
        print(f"Behavioral rules: {len(persona.behavioral_rules)}")
        print(f"Examples: {len(persona.examples)}")
        print(f"Handles documents: {', '.join(persona.handled_documents)}")
        print(f"Required evidence: {', '.join(persona.required_evidence)}")
        
        # Verify that system_prompt_template is populated
        if persona.system_prompt_template:
            print("System prompt template is defined ✓")
        else:
            print("ERROR: System prompt template is missing!")
            
        # Test if the template can be formatted without errors
        personality_text = "\n".join(f"- {trait}" for trait in persona.personality)
        handled_docs = ", ".join(persona.handled_documents)
        required_evidence = ", ".join(persona.required_evidence)
        
        try:
            formatted_prompt = persona.system_prompt_template.format(
                name=persona.name,
                role=persona.role,
                department=persona.department,
                personality=personality_text,
                handled_documents=handled_docs,
                required_evidence=required_evidence,
            )
            print("Template formatting succeeds ✓")
        except Exception as e:
            print(f"ERROR: Template formatting failed: {e}")
            
        print("\n")


if __name__ == "__main__":
    main()