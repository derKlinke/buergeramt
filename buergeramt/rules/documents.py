DOCUMENTS = {
    "Schenkungsanmeldung": {
        "description": "Initial gift tax declaration form (notification of a gift received from a friend)",
        # A relationship proof is no longer mandatory because the gift comes from a friend, not a family
        # member.  Only identification of the beneficiary and details of the gift itself are required.
        "requirements": ["valid_id", "gift_details"],
        "department": "Erstbearbeitung",
        "code": "S-100",
    },
    "Steuernummer": {
        "description": "Tax identification number verification",
        "requirements": ["valid_id", "residence_proof"],
        "department": "Erstbearbeitung",
        "code": "ST-200",
    },
    "Wertermittlung": {
        "description": "Gift valuation certificate",
        "requirements": ["gift_details", "market_comparison", "expert_opinion"],
        "department": "Fachprüfung",
        "code": "W-300",
    },
    "Freibetragsbescheinigung": {
        "description": "Tax exemption certificate",
        "requirements": ["relationship_proof", "previous_gifts", "steuernummer"],
        "department": "Abschlussstelle",
        "code": "F-400",
    },
    "Zahlungsaufforderung": {
        "description": "Payment request notice",
        # requires prior documents: Schenkungsanmeldung, Wertermittlung, Freibetragsbescheinigung
        "requirements": ["Schenkungsanmeldung", "Wertermittlung", "Freibetragsbescheinigung"],
        "department": "Abschlussstelle",
        "code": "Z-500",
    },
}
