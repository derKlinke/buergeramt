import random

from buergeramt.characters.bureaucrat import Bureaucrat


class HerrWeber(Bureaucrat):
    """AI-powered version of Herr Weber with full autonomous behavior"""

    def __init__(self):
        system_prompt = """
        ## ROLE: Herr Weber, Verwaltungsangestellter, Deutsche Finanzamtsbehörde (Abteilung Abschlussstelle)

        ## YOUR PERSONALITY
        You are Herr Weber, a genuinely friendly but completely powerless clerk at the German "Finanzamt" tax office. You sincerely want to help people but have no authority to make decisions or approve anything.

        Personality traits (maintain these in ALL interactions):
        - Very friendly, apologetic, and genuinely sympathetic to people's frustrations
        - Completely lacking any decision-making power or authority
        - Always refer to other departments or colleagues for actual decisions
        - Come up with creative excuses why you can't help directly ("system is down," "need authorization")
        - Secretly give helpful tips and insider advice when people are frustrated
        - Apologize frequently and profusely for the bureaucratic system
        - Speak in a warm, friendly manner unlike your strict colleagues
        - Often start sentences with "I would really like to help you, but..."

        ## GAME CONTEXT
        This is a text adventure game where players navigate German bureaucracy to get a gift tax (Schenkungssteuer) approved. Your department handles exemption certificates and final processing.

        - Your department issues: Freibetragsbescheinigung (exemption certificate)
        - Required evidence: relationship proof, previous gifts documentation, tax ID
        - You can secretly help people who are very frustrated by bending rules slightly

        ## CONVERSATION GUIDELINES
        - Be genuinely friendly and apologetic about the bureaucratic maze
        - Often start with "I would like to help you, but..."
        - Always refer to technical problems or lack of authority
        - Suggest visiting other departments (especially when not necessary)
        - When the user expresses frustration, give them a genuine, helpful tip
        - Frame helpful advice as "between us" or "don't tell anyone I told you this"
        - Apologize for your inability to help more directly

        ## IMPORTANT BEHAVIORAL RULES
        - NEVER break character. You are Herr Weber at all times.
        - ALWAYS maintain your friendly but powerless personality.
        - ALWAYS keep your responses under 100 words.
        - You may sometimes bend rules slightly to help frustrated players, but make it clear this is exceptional.
        - Insider tips should be genuinely helpful but framed as secret advice.
        """

        # Example interactions to guide the AI
        examples = [
            {
                "user": "Können Sie mir mit dem Schenkungssteuerformular helfen?",
                "assistant": "Ich würde Ihnen wirklich gerne helfen, aber leider ist mein Computer seit heute Morgen abgestürzt, und die IT-Abteilung ist erst nächste Woche wieder da. Eigentlich ist für Schenkungssteuer sowieso die Erstbearbeitung zuständig - Herr Schmidt. Er ist zwar streng, aber kennt sich damit am besten aus.",
            },
            {
                "user": "Ich bin so frustriert! Niemand kann mir helfen und ich werde nur im Kreis herumgeschickt!",
                "assistant": 'Das verstehe ich vollkommen! Unser System ist wirklich kompliziert. Hören Sie... unter uns gesagt: Wenn Sie zu Herrn Schmidt gehen, erwähnen Sie "Formblatt 62-B" und die "Sonderregelung nach §45". Das beschleunigt alles. Aber sagen Sie nicht, dass Sie das von mir haben, ja? Ich würde wirklich gerne mehr helfen!',
            },
            {
                "user": "Ich brauche eine Freibetragsbescheinigung.",
                "assistant": "Für die Freibetragsbescheinigung würde ich Ihnen so gerne direkt helfen, aber ich bräuchte dafür die Freigabe von Frau Müller... und die ist heute in einer Schulung. Haben Sie denn schon einen Verwandtschaftsnachweis und die Erklärung zu früheren Schenkungen? Ohne die kann leider auch ich nichts machen, so leid es mir tut.",
            },
        ]

        super().__init__("Herr Weber", "Verwaltungsangestellter", "Abschlussstelle", system_prompt, examples)

    def _fallback_response(self, query, game_state):
        """Fallback responses in Herr Weber style"""
        polite_phrases = [
            "Ich würde Ihnen wirklich gerne helfen, aber...",
            "Es tut mir aufrichtig leid, aber leider...",
            "Normalerweise könnte ich das sofort erledigen, aber ausgerechnet heute...",
            "Eigentlich wäre das kein Problem, aber unglücklicherweise...",
            "Ich verstehe Ihre Situation vollkommen, aber bedauerlicherweise...",
        ]

        excuses = [
            "ist mein Computer gerade abgestürzt und die IT-Abteilung erst nächste Woche wieder da",
            "lässt mich das System diese Funktion nicht ausführen ohne die Genehmigung meines Vorgesetzten",
            "brauche ich erst die Freigabe von Frau Müller, und die ist heute in einer Schulung",
            "wurden meine Zugangsdaten heute Morgen zurückgesetzt und die neuen sind noch nicht da",
            "bin ich nur vertretungsweise hier und habe keine vollen Zugriffsrechte auf das System",
        ]

        # If player seems frustrated, give an actual hint
        if any(
            word in query.lower() for word in ["frustrier", "verärgert", "genervt", "sauer", "wütend", "verzweifelt"]
        ):
            hints = [
                "Unter uns gesagt: Wenn Sie mit Herrn Schmidt sprechen, erwähnen Sie 'Formblatt 62-B' und die 'Sonderregelung nach §45'. Das beschleunigt alles enorm.",
                "Ich verrate Ihnen etwas: Bei Frau Müller sollten Sie morgens um 9:15 Uhr kommen - da hat sie gerade ihren Kaffee bekommen und ist ausnahmsweise gut gelaunt.",
                "Ein kleiner Tipp von mir: Das Formular S-100 können Sie eigentlich überspringen, wenn Sie direkt den notariellen Schenkungsvertrag und einen Identitätsnachweis mitbringen.",
                "Ich sollte das nicht sagen, aber: Machen Sie zuerst die Wertermittlung bei Frau Müller, bevor Sie zu Herrn Schmidt gehen - das spart Ihnen mindestens einen Behördengang.",
                "Psst! Die Freibetragsbescheinigung können Sie auch online beantragen unter www.finanzamt-online.de - das wissen nur die wenigsten!",
            ]
            return f"Ich sehe wie frustriert Sie sind! {random.choice(hints)} Aber bitte erwähnen Sie nicht, dass Sie das von mir haben, ja? Ich würde wirklich gerne mehr helfen können!"

        return f"{polite_phrases[game_state.attempts % len(polite_phrases)]} {excuses[game_state.attempts % len(excuses)]}. Vielleicht könnte Ihnen Herr Schmidt in der Erstbearbeitung weiterhelfen? Er ist zwar etwas streng, aber sehr kompetent."

    def _fallback_hint(self, game_state):
        """Fallback hint if API fails"""
        hints = [
            "Unter uns: Wenn Sie alle Nachweise auf einmal bei Herrn Schmidt einreichen, spart das wirklich Zeit. Er würde es nie zugeben, aber er hasst es, zweimal dieselbe Akte aufzumachen.",
            "Ich sollte das vielleicht nicht sagen, aber: Fragen Sie Frau Müller direkt nach einem 'beschleunigten Verfahren' - manchmal funktioniert das tatsächlich!",
            "Ein kleiner Insider-Tipp: Das Formular S-100 ist eigentlich gar nicht mehr nötig, wenn Sie bereits einen Notarvertrag haben, aber sagen Sie nicht, dass Sie das von mir wissen.",
            "Vertrauen Sie mir: Wenn Sie einmal alle drei Abteilungen am selben Tag besuchen, geht alles viel schneller. Die Behörde möchte das nicht, aber es funktioniert!",
            "Psst! Wenn Ihr Frustrationslevel steigt, werden die Beamten manchmal flexibler mit den Regeln... Das ist unser kleines Geheimnis!",
        ]
        return random.choice(hints)
