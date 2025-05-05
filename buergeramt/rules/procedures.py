PROCEDURES = {
    "Antragstellung": {
        "description": "Initial application submission",
        "keywords": ["einreichen", "anmelden", "beantragen"],
        "next_steps": ["Formularprüfung", "Nachweisanforderung"],
        "department": "initial",
    },
    "Formularprüfung": {
        "description": "Form verification process",
        "keywords": ["prüfen", "kontrollieren", "verifizieren"],
        "next_steps": ["Nachweisanforderung", "Weiterleitung"],
        "department": "initial",
    },
    "Nachweisanforderung": {
        "description": "Request for additional evidence",
        "keywords": ["nachweisen", "belegen", "dokumentieren"],
        "next_steps": ["Terminvereinbarung", "Weiterleitung"],
        "department": "any",
    },
    "Terminvereinbarung": {
        "description": "Scheduling an appointment",
        "keywords": ["termin", "vereinbaren", "vorstellig"],
        "next_steps": ["Weiterleitung", "Warteschleife"],
        "department": "any",
    },
    "Weiterleitung": {
        "description": "Forwarding to another department",
        "keywords": ["weiterleiten", "zuständigkeit", "vermitteln"],
        "next_steps": ["Antragstellung", "Warteschleife"],
        "department": "any",
    },
    "Warteschleife": {
        "description": "Waiting period",
        "keywords": ["warten", "gedulden", "bearbeitungszeit"],
        "next_steps": ["Bescheiderteilung", "Nachweisanforderung"],
        "department": "any",
    },
    "Bescheiderteilung": {
        "description": "Decision notice issuance",
        "keywords": ["bescheid", "entscheidung", "bewilligen"],
        "next_steps": ["Widerspruch", "Zahlungsaufforderung"],
        "department": "final",
    },
    "Widerspruch": {
        "description": "Formal objection procedure",
        "keywords": ["widersprechen", "anfechten", "beschweren"],
        "next_steps": ["Nachweisanforderung", "Warteschleife"],
        "department": "appeals",
    },
    "Zahlungsaufforderung": {
        "description": "Payment request procedure",
        "keywords": ["zahlen", "überweisen", "entrichten"],
        "next_steps": ["Abschluss"],
        "department": "final",
    },
    "Abschluss": {
        "description": "Completion of the process",
        "keywords": ["abschließen", "beenden", "erledigen"],
        "next_steps": [],
        "department": "final",
    },
}
