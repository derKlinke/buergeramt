# Document types and their requirements
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

# Supporting evidence types
EVIDENCE = {
    "valid_id": {
        "description": "Valid identification document",
        "acceptable_forms": ["Personalausweis", "Reisepass", "Aufenthaltstitel"],
    },
    "gift_details": {
        "description": "Detailed description of the gift with proof of transfer",
        "acceptable_forms": ["Notarielle Urkunde", "Übergabeprotokoll", "Bankbeleg", "Eigentumsnachweis"],
    },
    "relationship_proof": {
        "description": "Proof of the relationship between donor and recipient (e.g. affidavit of friendship)",
        "acceptable_forms": ["Freundschaftserklärung", "Gemeinsamer Mietvertrag", "Gemeinsames Konto"],
    },
    "residence_proof": {
        "description": "Proof of current residence",
        "acceptable_forms": ["Meldebescheinigung", "Mietvertrag", "Grundbuchauszug"],
    },
    "market_comparison": {
        "description": "Market comparison for similar items/properties",
        "acceptable_forms": ["Gutachten", "Marktwertanalyse", "Vergleichspreise"],
    },
    "expert_opinion": {
        "description": "Expert opinion on the value of the gift",
        "acceptable_forms": ["Sachverständigengutachten", "Wertgutachten"],
    },
    "previous_gifts": {
        "description": "Declaration of previous gifts from the same person",
        "acceptable_forms": ["Eigenerklärung", "Frühere Steuerbescheide", "Notarielle Urkunden"],
    },
    "steuernummer": {
        "description": "Tax identification number document",
        "acceptable_forms": ["Steuerbescheid", "Steuer-ID Mitteilung"],
    },
}

# Bureaucratic procedures and their keywords
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

# Bureaucratic loops (designed to send the player back and forth)
BUREAUCRATIC_LOOPS = [
    {
        "trigger": "Formularprüfung",
        "condition": "missing_evidence",
        "redirect": "Nachweisanforderung",
        "message": "Es fehlen noch Unterlagen. Bitte wenden Sie sich an die Abteilung {department}.",
    },
    {
        "trigger": "Weiterleitung",
        "condition": "wrong_department",
        "redirect": "Antragstellung",
        "message": "Sie sind bei der falschen Abteilung. Bitte beginnen Sie den Prozess bei Abteilung {department}.",
    },
    {
        "trigger": "Nachweisanforderung",
        "condition": "incomplete_form",
        "redirect": "Antragstellung",
        "message": "Ihr Formular ist nicht vollständig ausgefüllt. Bitte beginnen Sie erneut.",
    },
    {
        "trigger": "Bescheiderteilung",
        "condition": "missing_signatures",
        "redirect": "Weiterleitung",
        "message": "Es fehlen noch wichtige Unterschriften von Abteilung {department}.",
    },
    {
        "trigger": "Zahlungsaufforderung",
        "condition": "calculation_error",
        "redirect": "Widerspruch",
        "message": "Es liegt ein Berechnungsfehler vor. Bitte legen Sie Widerspruch ein.",
    },
]


# Game state tracking
class GameState:
    def __init__(self):
        self.collected_documents = {}
        self.current_department = "initial"
        self.evidence_provided = {}
        self.current_procedure = "Antragstellung"
        self.attempts = 0
        self.frustration_level = 0
        self.progress = 0

    def add_document(self, document_name):
        """Add a completed document to the player's collection"""
        if document_name in DOCUMENTS:
            self.collected_documents[document_name] = DOCUMENTS[document_name]
            return True
        return False

    def add_evidence(self, evidence_name, evidence_form):
        """Add a piece of evidence to the player's collection"""
        if evidence_name in EVIDENCE and evidence_form in EVIDENCE[evidence_name]["acceptable_forms"]:
            self.evidence_provided[evidence_name] = evidence_form
            return True
        return False

    def check_document_requirements(self, document_name):
        """Check if the player has all requirements for a document"""
        if document_name not in DOCUMENTS:
            return False

        # A requirement may be an evidence key or a prior document name
        requirements = DOCUMENTS[document_name]["requirements"]
        for req in requirements:
            # evidence requirement
            if req in EVIDENCE:
                if req not in self.evidence_provided:
                    return False
            # document requirement
            elif req in DOCUMENTS:
                if req not in self.collected_documents:
                    return False
            else:
                # unknown requirement
                return False
        return True

    def set_department(self, department_name):
        """Change the player's current department"""
        self.current_department = department_name

    def set_procedure(self, procedure_name):
        """Change the player's current procedure"""
        if procedure_name in PROCEDURES:
            self.current_procedure = procedure_name
            self.attempts += 1
            return True
        return False

    def get_next_steps(self):
        """Get possible next steps based on current procedure"""
        if self.current_procedure in PROCEDURES:
            return PROCEDURES[self.current_procedure]["next_steps"]
        return []

    def check_for_loop(self):
        """Check if player is in a bureaucratic loop"""
        for loop in BUREAUCRATIC_LOOPS:
            if loop["trigger"] == self.current_procedure:
                # Implement conditions for loops here
                if loop["condition"] == "missing_evidence" and len(self.evidence_provided) < 3:
                    return loop
                elif (
                    loop["condition"] == "wrong_department"
                    and self.current_department != PROCEDURES[self.current_procedure]["department"]
                ):
                    return loop
                elif loop["condition"] == "incomplete_form" and self.attempts % 3 == 0:
                    return loop
                elif loop["condition"] == "missing_signatures" and len(self.collected_documents) < 2:
                    return loop
                elif loop["condition"] == "calculation_error" and self.attempts % 5 == 0:
                    return loop
        return None

    def increase_frustration(self, amount=1):
        """Increase the player's frustration level"""
        self.frustration_level += amount

    def decrease_frustration(self, amount=1):
        """Decrease the player's frustration level"""
        self.frustration_level = max(0, self.frustration_level - amount)

    def update_progress(self):
        """Update the player's progress in the game"""
        document_progress = len(self.collected_documents) * 10
        evidence_progress = len(self.evidence_provided) * 5
        procedure_bonus = 0

        if self.current_procedure == "Bescheiderteilung":
            procedure_bonus = 15
        elif self.current_procedure == "Zahlungsaufforderung":
            procedure_bonus = 20
        elif self.current_procedure == "Abschluss":
            procedure_bonus = 25

        self.progress = min(100, document_progress + evidence_progress + procedure_bonus)
        return self.progress
