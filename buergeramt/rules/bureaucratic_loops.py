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
