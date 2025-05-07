#!/usr/bin/env python3
"""
Test script to verify that the persona system works correctly without examples.
This test just loads the configuration and verifies the persona data without creating
actual Bureaucrat instances (which would require OpenAI API keys).
"""

from buergeramt.rules.loader import get_config


def main():
    print("Loading configuration...")
    config = get_config()
    
    print(f"\nLoaded {len(config.personas)} personas")
    print("Personas in config:")
    for persona_id in config.personas:
        print(f"  - {persona_id}")
    
    print("\nTesting persona data...")
    
    for persona_id, persona in config.personas.items():
        print(f"\n=== Checking persona {persona_id} ===")
        print(f"Name: {persona.name}")
        print(f"Role: {persona.role}")
        print(f"Department: {persona.department}")
        print(f"Personality traits: {len(persona.personality)}")
        print(f"Behavioral rules: {len(persona.behavioral_rules)}")
        print(f"System prompt template length: {len(persona.system_prompt_template)} characters")
        
        # Format the system prompt to verify it works
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
            print(f"System prompt formatted successfully ({len(formatted_prompt)} characters) ✓")
        except Exception as e:
            print(f"ERROR formatting system prompt: {e}")
    
    print("\nAll tests completed!")


if __name__ == "__main__":
    main()