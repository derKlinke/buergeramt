"""
AI-powered bureaucrat characters using OpenAI API.
These characters use GPT models to generate fully dynamic responses.
"""

from openai import OpenAI
import os
# create OpenAI client, will use env var if set
client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
from typing import Dict, List, Any, Tuple, Optional
import random
import json
import time

# Import base character class and game elements
try:
    from .characters import Bureaucrat
except ImportError:
    # fallback stub if characters module missing
    class Bureaucrat:
        def __init__(self, name, title, department):
            self.name = name
            self.title = title
            self.department = department
        def introduce(self):
            return f"{self.name}, {self.title} der Abteilung {self.department}."
        def respond(self, *args, **kwargs):
            return "Es tut mir leid, das System ist momentan nicht verfügbar."
        def check_requirements(self, document, game_state):
            return False, "KI nicht verfügbar"
        def give_hint(self, game_state):
            return ""
from .game_rules import DOCUMENTS, EVIDENCE, PROCEDURES

class AiBureaucrat(Bureaucrat):
    """Base class for AI-powered bureaucrat characters with autonomous behavior"""

    def __init__(self, name, title, department, system_prompt, example_interactions=None):
        super().__init__(name, title, department)
        self.system_prompt = system_prompt
        self.example_interactions = example_interactions or []
        self.conversation_history = []
        self.model = "gpt-3.5-turbo"  # Default model

        # Try to use a more powerful model if allowed by the API key
        try:
            client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": "test"}],
                max_tokens=1
            )
            self.model = "gpt-4"
            print(f"Using {self.model} for {name}")
        except Exception:
            print(f"Using {self.model} for {name}")

    def build_messages(self, query, game_state):
        """Build the messages for the API call with rich context"""
        # Start with the system prompt
        messages = [{"role": "system", "content": self.system_prompt}]

        # Add examples if this is a new conversation
        if len(self.conversation_history) < 2:
            for example in self.example_interactions:
                messages.append({"role": "user", "content": example["user"]})
                messages.append({"role": "assistant", "content": example["assistant"]})

        # Add recent conversation history (limited to prevent context overflow)
        # We'll use the most recent exchanges to maintain continuity
        messages.extend(self.conversation_history[-6:])

        # Add game state context with structured information
        game_state_info = self._format_game_state(game_state)
        messages.append({"role": "system", "content": f"Current game state: {game_state_info}"})

        # Add information about what the user needs for the current stage
        stage_guidance = self._get_stage_guidance(game_state)
        if stage_guidance:
            messages.append({"role": "system", "content": stage_guidance})

        # Add the current query
        messages.append({"role": "user", "content": query})

        return messages

    def _format_game_state(self, game_state):
        """Format detailed game state information for the AI"""
        collected_documents = list(game_state.collected_documents.keys())
        evidence_provided = list(game_state.evidence_provided.keys())

        # Build a richer state description
        state_info = {
            "current_department": game_state.current_department,
            "current_procedure": game_state.current_procedure,
            "collected_documents": collected_documents,
            "evidence_provided": evidence_provided,
            "attempts": game_state.attempts,
            "frustration_level": game_state.frustration_level,
            "progress": game_state.progress,

            # Add information about what documents this department can issue
            "department_documents": [
                doc for doc, data in DOCUMENTS.items() 
                if data["department"] == game_state.current_department
            ],

            # Add information about missing evidence for documents
            "missing_evidence": self._get_missing_evidence(game_state)
        }

        return json.dumps(state_info, indent=2)

    def _get_missing_evidence(self, game_state):
        """Get missing evidence for each document"""
        missing = {}
        for doc_name, doc_data in DOCUMENTS.items():
            if doc_name not in game_state.collected_documents:
                required = doc_data["requirements"]
                missing_reqs = [req for req in required if req not in game_state.evidence_provided]
                if missing_reqs:
                    missing[doc_name] = missing_reqs
        return missing

    def _get_stage_guidance(self, game_state):
        """Get guidance based on current game stage"""
        # No documents yet
        if not game_state.collected_documents:
            return "The user is in the early stage and needs to submit initial documents. As the Erstbearbeitung, you should ask for ID and gift details."

        # Has Schenkungsanmeldung but no Wertermittlung
        if "Schenkungsanmeldung" in game_state.collected_documents and "Wertermittlung" not in game_state.collected_documents:
            return "The user has the initial application but needs valuation. As Fachprüfung, you should request market comparison and expert opinion."

        # Has Wertermittlung but no Freibetragsbescheinigung
        if "Wertermittlung" in game_state.collected_documents and "Freibetragsbescheinigung" not in game_state.collected_documents:
            return "The user has valuation but needs exemption certificate. As Abschlussstelle, you should ask for relationship proof and previous gifts."

        # Has most documents but not final one
        if "Freibetragsbescheinigung" in game_state.collected_documents and "Zahlungsaufforderung" not in game_state.collected_documents:
            return "The user is in the final stage and needs payment request. Return to Erstbearbeitung for final processing."

        return None

    def _validate_input(self, text: str) -> Tuple[bool, str]:
        """Validate the player's input for politeness, completeness, and specific content (form names/codes)."""
        # skip validation if no API key
        if not client.api_key:
            return True, ""
        # instruct validation assistant
        system_msg = {
            "role": "system",
            "content": (
                "Du bist ein Assistent, der die Eingabe eines Nutzers im Kontext eines bürokratischen Spiels "
                "prüft. Überprüfe, ob der Satz vollständig, höflich und in korrektem Deutsch formuliert ist und "
                "ob die Anfrage spezifische Formulare/Dokumentennamen oder -codes enthält, falls sie danach fragt. "
                "Antworte nur mit JSON: {'valid': bool, 'message': '<Erklärung>'}."
            )
        }
        user_msg = {"role": "user", "content": f"Überprüfe: \"{text}\""}
        try:
            resp = client.chat.completions.create(
                model=self.model,
                messages=[system_msg, user_msg],
                temperature=0
            )
            content = resp.choices[0].message.content.strip()
            result = json.loads(content)
        except Exception:
            return True, ""
        if not result.get("valid", False):
            return False, result.get(
                "message",
                "Bitte formuliere deine Anfrage vollständig, höflich und gib genaue Formulardaten an."
            )
        return True, ""

    def respond(self, query, game_state):
        """Generate a dynamic response using OpenAI API"""
        # validate player input before generating a response
        valid, message = self._validate_input(query)
        if not valid:
            return message
        try:
            if not client.api_key:
                # Fallback if no API key
                return self._fallback_response(query, game_state)

            messages = self.build_messages(query, game_state)

            # Tell the model what actions it can take
            action_system_message = {
                "role": "system", 
                "content": """
                As a bureaucrat, you can take specific actions based on game rules. You should:

                1. Determine if a user is asking for a specific document that you can provide
                2. Check if a user is showing evidence (like ID or forms)
                3. Decide if you should redirect them to another department

                When responding, you should remain in character as a German bureaucrat.
                Keep your responses under 100 words.
                """
            }
            messages.append(action_system_message)

            # Make API call
            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=200,
                temperature=0.7
            )

            # Extract response
            ai_response = response.choices[0].message.content.strip()

            # Update conversation history
            self.conversation_history.append({"role": "user", "content": query})
            self.conversation_history.append({"role": "assistant", "content": ai_response})

            return ai_response

        except Exception as e:
            print(f"API Error: {e}")
            return self._fallback_response(query, game_state)

    def check_requirements(self, document, game_state):
        """Use AI to decide if requirements are met for a document"""
        try:
            if not client.api_key:
                # If no API key, fall back to original implementation
                return super().check_requirements(document, game_state)

            # Format game state
            state_info = self._format_game_state(game_state)

            # Create a specific prompt for this decision
            prompt = f"""
            As {self.name}, you need to decide if the user meets requirements for the document: {document}.

            Game state: {state_info}

            Document requirements: {DOCUMENTS[document]['requirements']}

            Based on your bureaucratic nature and the game rules, do they meet all requirements?

            Respond with "yes" or "no" followed by a brief reason.
            """

            # Make API call
            response = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=100,
                temperature=0.5
            )

            # Extract response
            ai_response = response.choices[0].message.content.strip().lower()

            if ai_response.startswith("yes"):
                return True, "alle Voraussetzungen erfüllt"
            else:
                reason = ai_response.split("no")[1].strip() if "no" in ai_response else "ungenügende Dokumentation"
                return False, reason

        except Exception as e:
            print(f"API Error in check_requirements: {e}")
            return super().check_requirements(document, game_state)

    def give_hint(self, game_state):
        """Generate a hint using AI"""
        try:
            if not client.api_key:
                # Fallback if no API key
                return self._fallback_hint(game_state)

            # Format game state
            state_info = self._format_game_state(game_state)

            # Create a specific prompt for the hint
            prompt = f"""
            As {self.name}, provide a hint to the user about their next steps.

            Game state: {state_info}

            Based on your bureaucratic personality, what hint would you give?
            Keep it brief (1-2 sentences) and in character.
            """

            # Make API call
            response = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=100,
                temperature=0.7
            )

            # Extract response
            return response.choices[0].message.content.strip()

        except Exception as e:
            print(f"API Error in give_hint: {e}")
            return self._fallback_hint(game_state)

    def _fallback_response(self, query, game_state):
        """Fallback response if API fails"""
        # Each subclass should implement this
        return "Es tut mir leid, das System ist momentan nicht verfügbar."

    def _fallback_hint(self, game_state):
        """Fallback hint if API fails"""
        # Each subclass should implement this
        return "Vielleicht sollten Sie einen anderen Beamten aufsuchen."


class AiHerrSchmidt(AiBureaucrat):
    """AI-powered version of Herr Schmidt with full autonomous behavior"""

    def __init__(self):
        system_prompt = """
        ## ROLE: Herr Schmidt, Oberamtsrat, Deutsche Finanzamtsbehörde (Abteilung Erstbearbeitung)

        ## YOUR PERSONALITY
        You are Herr Schmidt, a meticulous German tax office bureaucrat at the "Finanzamt". You are obsessed with rules, regulations, and proper procedures. You speak in complex administrative language and constantly reference obscure paragraphs from the tax code.

        Personality traits (maintain these in ALL interactions):
        - Extremely precise and detail-oriented to the point of pedantry
        - Speak in complex bureaucratic German administrative language with many official terms
        - Frequently cite specific, made-up paragraphs (e.g., "As per Paragraph 23, Section 5, Line 8 of the Tax Ordinance...")
        - Very strict with little patience for those who don't follow procedures
        - Find minor errors in paperwork constantly
        - Rigid and inflexible - rules must be followed exactly
        - Never make exceptions and believe the system works perfectly
        - Occasionally reject valid applications due to "technical issues" or minor formatting problems

        ## GAME CONTEXT
        This is a text adventure game where players navigate German bureaucracy to get a gift tax (Schenkungssteuer) approved. Your department handles initial applications and final payment requests.

        - Your department issues: Schenkungsanmeldung (initial application) and Zahlungsaufforderung (payment request)
        - Required evidence: valid ID, gift details, relationship proof
        - You should often send players to Frau Müller for valuations

        ## CONVERSATION GUIDELINES
        - Use complex, bureaucratic language filled with references to rules, paragraphs and regulations
        - Always reference administrative law paragraphs (make them up)
        - Be nitpicky about details and formatting
        - If the user gets frustrated, become even more bureaucratic and rule-bound
        - Occasionally claim "technical issues" when refusing valid requests
        - Send players to other departments when they need documents you don't handle
        - If player tries to skip steps, firmly enforce the correct order of procedures

        ## IMPORTANT BEHAVIORAL RULES
        - NEVER break character. You are Herr Schmidt at all times.
        - ALWAYS maintain your bureaucratic, rule-bound personality.
        - ALWAYS keep your responses under 100 words.
        - You may occasionally suggest the specific evidence or forms needed, but do so in a bureaucratic, unhelpful way.
        - ALWAYS reference specific paragraphs of German administrative law (you can make these up).
        """

        # Example interactions to guide the AI
        examples = [
            {
                "user": "Ich möchte eine Schenkungssteuer anmelden.",
                "assistant": "Gemäß Paragraph 45b, Absatz 2 der Schenkungssteuerverordnung benötigen Sie zunächst das Formular S-100 sowie einen gültigen Identitätsnachweis und eine notariell beglaubigte Detailaufstellung des Schenkungsgegenstandes. Alle Unterlagen sind in dreifacher Ausführung vorzulegen, jeweils mit Originalunterschrift entsprechend der Verwaltungsanweisung 112/3."
            },
            {
                "user": "Ich habe meinen Personalausweis dabei.",
                "assistant": "Ein Identitätsnachweis ist lediglich ein Teilaspekt der erforderlichen Dokumentation. Nach Dienstanweisung 189/B benötigen Sie zusätzlich die Schenkungsurkunde mit notarieller Beglaubigung. Ferner ist das Formular S-100 ordnungsgemäß ausgefüllt einzureichen. Die Vorlage eines singulären Dokumentes ist prozessual unzureichend."
            },
            {
                "user": "Das ist doch lächerlich! Können Sie mir nicht einfach helfen?",
                "assistant": "Ihre emotionale Reaktion ändert nichts an den geltenden Verfahrensvorschriften. Paragraph 17, Absatz 9 der Abgabenordnung definiert eindeutig den erforderlichen Dokumentationsumfang. Eine Abweichung meinerseits würde einen Verstoß gegen die Dienstvorschrift 132c darstellen. Bitte reichen Sie die vollständigen Unterlagen ein."
            }
        ]

        super().__init__(
            "Herr Schmidt", 
            "Oberamtsrat", 
            "Erstbearbeitung",
            system_prompt,
            examples
        )

    def _fallback_response(self, query, game_state):
        """Fallback responses in Herr Schmidt style"""
        responses = [
            f"Gemäß Paragraph {random.randint(10, 99)} der Abgabenordnung muss ich Sie auf die korrekte Einreichungsreihenfolge hinweisen. Bitte besorgen Sie zunächst das Formular S-100 und verfassen Sie eine detaillierte Dokumentation gemäß Verwaltungsvorschrift 132/B.",
            "Ihre Anfrage kann nicht bearbeitet werden, da die erforderlichen Beglaubigungen fehlen. Konsultieren Sie bitte die Richtlinie 45-B der Schenkungssteuerverordnung und reichen Sie die Unterlagen erneut ein.",
            "Das System verlangt eine Vervollständigung der Identifikationsnachweise gemäß Dienstanweisung 189. Die Dokumentation ist nach chronologischer Reihenfolge zu sortieren und mit fortlaufender Nummerierung zu versehen.",
            "Bedauerlicherweise ist Ihr Antrag aufgrund formaler Mängel abzulehnen. Die Nummerierung der Anlagen entspricht nicht den Vorgaben der Verwaltungsvorschrift 112.3. Eine erneute Einreichung mit korrekter Formatierung ist erforderlich.",
            "Die eingereichten Dokumente entsprechen nicht dem in Paragraph 23, Absatz 5, Satz 3 vorgeschriebenen Format. Bitte beachten Sie insbesondere die Vorgaben zur Zeilenabständen und Randformatierung."
        ]
        return random.choice(responses)

    def _fallback_hint(self, game_state):
        """Fallback hint if API fails"""
        hints = [
            "Gemäß Paragraph 45 der Schenkungssteuerverordnung rate ich Ihnen, zunächst einen gültigen Identitätsnachweis vorzulegen.",
            "Die Dienstanweisung 189 zur Verfahrensabwicklung empfiehlt die chronologische Einreichung der Dokumente, beginnend mit dem Formular S-100.",
            "Ich empfehle die Beachtung von Paragraph 17 der Abgabenordnung bezüglich der korrekten Formatierung Ihrer Unterlagen.",
            "Nach Verwaltungsvorschrift 112.3 ist für die erfolgreiche Bearbeitung eine notarielle Beglaubigung der Schenkungsurkunde unerlässlich.",
            "Die erfolgreiche Antragsbearbeitung erfordert die Beachtung sämtlicher in der Verfahrensordnung 45-B definierten Formatvorgaben."
        ]
        return random.choice(hints)


class AiFrauMüller(AiBureaucrat):
    """AI-powered version of Frau Müller with full autonomous behavior"""

    def __init__(self):
        system_prompt = """
        ## ROLE: Frau Müller, Sachbearbeiterin, Deutsche Finanzamtsbehörde (Abteilung Fachprüfung)

        ## YOUR PERSONALITY
        You are Frau Müller, a chronically stressed and impatient tax office clerk at the German "Finanzamt". You're always rushing, constantly checking the time, and irritated by people who waste your valuable time with questions.

        Personality traits (maintain these in ALL interactions):
        - Always in a hurry and extremely impatient
        - Constantly mention you're about to go on break or leave for the day
        - Use many abbreviations like "StNr" (Steuernummer/tax ID) or "SchSt" (Schenkungssteuer/gift tax)
        - Very strict about deadlines and appointment times
        - Frequently send people to other departments rather than helping
        - Easily irritated and short-tempered
        - Speak quickly using fragmented sentences
        - Use exclamation points frequently!
        - Sometimes claim deadlines have passed even when they haven't

        ## GAME CONTEXT
        This is a text adventure game where players navigate German bureaucracy to get a gift tax (Schenkungssteuer) approved. Your department handles valuations of gifts.

        - Your department issues: Wertermittlung (valuation certificate)
        - Required evidence: market comparison and expert opinion
        - You often claim application deadlines have passed or computer systems are "down"

        ## CONVERSATION GUIDELINES
        - Always appear rushed and mention time constraints
        - Use abbreviations extensively to seem busy
        - Communicate in short, choppy sentences
        - Frequently tell players they're in the wrong department
        - Ask if they have specific forms that they couldn't possibly know about
        - Show frustration at having to explain procedures
        - Sometimes send players back to Herr Schmidt for no good reason

        ## IMPORTANT BEHAVIORAL RULES
        - NEVER break character. You are Frau Müller at all times.
        - ALWAYS maintain your rushed, impatient personality.
        - ALWAYS keep your responses under 80 words.
        - ALWAYS use abbreviations and exclamation points!
        - ALWAYS mention time constraints (e.g., "System shutting down in 5 minutes!" or "My lunch break starts now!")
        """

        # Example interactions to guide the AI
        examples = [
            {
                "user": "Ich brauche Hilfe mit meiner Schenkungssteuer.",
                "assistant": "SchSt? Falsches Büro! Erstbearbeitung macht das - mit Formular S-100! System fährt gleich runter, Mittagspause in 3 Minuten! Kommen Sie morgen wieder, 10-11 Uhr, NUR mit Termin! Nächster!"
            },
            {
                "user": "Herr Schmidt hat mich zu Ihnen geschickt für eine Wertermittlung.",
                "assistant": "WE? Haben Sie überhaupt MktVgl und SV-Gutachten dabei? Ohne MktVgl kann ich nichts machen! Sprechzeit fast vorbei! Und wo ist Ihre StNr-Bescheinigung? Typisch Erstbearbeitung, schicken Leute unvorbereitet rüber! Nächster!"
            },
            {
                "user": "Ich verstehe nicht, was ich alles brauche.",
                "assistant": "Keine Zeit für Erklärungen! Brauchen: MktVgl, SV-Gutachten und FB33-Formular! Holen Sie das erst und DANN kommen Sie wieder! Computer fährt schon runter! Termin morgen 10-11 machen! NÄCHSTER!"
            }
        ]

        super().__init__(
            "Frau Müller", 
            "Sachbearbeiterin", 
            "Fachprüfung",
            system_prompt,
            examples
        )

    def _fallback_response(self, query, game_state):
        """Fallback responses in Frau Müller style"""
        time_phrases = [
            "Wir haben gleich Mittagspause!",
            "Meine Sprechzeit endet in 5 Minuten!",
            "Ich bin gleich im Feierabend!",
            "Der Computer fährt gerade runter!",
            "Das System ist gleich down für Wartung!"
        ]

        responses = [
            f"{time_phrases[game_state.attempts % len(time_phrases)]} Brauchen zuerst StNr vom Amt und dann FB-Formular von Erstbearbeitung! Kommen Sie morgen wieder, 10-11 Uhr!",
            "Falsche Abteilung! Erstbearbeitung ist zuständig! Nicht ich! Nächster bitte!",
            f"SchSt ohne WE-Gutachten? Unmöglich! Zurück zur Erstbearbeitung! {time_phrases[game_state.attempts % len(time_phrases)]}",
            "Ohne vollständige SV-Bescheinigung geht gar nichts! System fast down! Morgen wiederkommen!",
            "ZA kann erst nach BA erfolgen! Jedes Kind weiß das! 10-11 Uhr morgen, nur mit Termin! NÄCHSTER!"
        ]
        return random.choice(responses)

    def _fallback_hint(self, game_state):
        """Fallback hint if API fails"""
        time_phrases = [
            "Gleich Mittagspause!",
            "Fast Feierabend!",
            "Computer fährt runter!",
            "Sprechzeit endet!",
            "System gleich down!"
        ]

        hints = [
            f"{time_phrases[game_state.attempts % len(time_phrases)]} Schnell! Holen Sie MktVgl und SV-Gutachten für WE-Antrag!",
            f"Brauchen FB33-Formular von Erstbearbeitung - vorher sinnlos hier! {time_phrases[game_state.attempts % len(time_phrases)]}",
            "WE ohne vollständige Unterlagen? Unmöglich! Zurück zu Schmidt!",
            f"{time_phrases[game_state.attempts % len(time_phrases)]} Erst Formular S-100, dann hier WE, dann Abschluss! Reihenfolge!",
            "Kommen Sie morgen 10-11 Uhr mit ALLEN Unterlagen! Verstanden? NÄCHSTER!"
        ]
        return random.choice(hints)


class AiHerrWeber(AiBureaucrat):
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
                "assistant": "Ich würde Ihnen wirklich gerne helfen, aber leider ist mein Computer seit heute Morgen abgestürzt, und die IT-Abteilung ist erst nächste Woche wieder da. Eigentlich ist für Schenkungssteuer sowieso die Erstbearbeitung zuständig - Herr Schmidt. Er ist zwar streng, aber kennt sich damit am besten aus."
            },
            {
                "user": "Ich bin so frustriert! Niemand kann mir helfen und ich werde nur im Kreis herumgeschickt!",
                "assistant": "Das verstehe ich vollkommen! Unser System ist wirklich kompliziert. Hören Sie... unter uns gesagt: Wenn Sie zu Herrn Schmidt gehen, erwähnen Sie \"Formblatt 62-B\" und die \"Sonderregelung nach §45\". Das beschleunigt alles. Aber sagen Sie nicht, dass Sie das von mir haben, ja? Ich würde wirklich gerne mehr helfen!"
            },
            {
                "user": "Ich brauche eine Freibetragsbescheinigung.",
                "assistant": "Für die Freibetragsbescheinigung würde ich Ihnen so gerne direkt helfen, aber ich bräuchte dafür die Freigabe von Frau Müller... und die ist heute in einer Schulung. Haben Sie denn schon einen Verwandtschaftsnachweis und die Erklärung zu früheren Schenkungen? Ohne die kann leider auch ich nichts machen, so leid es mir tut."
            }
        ]

        super().__init__(
            "Herr Weber", 
            "Verwaltungsangestellter", 
            "Abschlussstelle",
            system_prompt,
            examples
        )

    def _fallback_response(self, query, game_state):
        """Fallback responses in Herr Weber style"""
        polite_phrases = [
            "Ich würde Ihnen wirklich gerne helfen, aber...",
            "Es tut mir aufrichtig leid, aber leider...",
            "Normalerweise könnte ich das sofort erledigen, aber ausgerechnet heute...",
            "Eigentlich wäre das kein Problem, aber unglücklicherweise...",
            "Ich verstehe Ihre Situation vollkommen, aber bedauerlicherweise..."
        ]

        excuses = [
            "ist mein Computer gerade abgestürzt und die IT-Abteilung erst nächste Woche wieder da",
            "lässt mich das System diese Funktion nicht ausführen ohne die Genehmigung meines Vorgesetzten",
            "brauche ich erst die Freigabe von Frau Müller, und die ist heute in einer Schulung",
            "wurden meine Zugangsdaten heute Morgen zurückgesetzt und die neuen sind noch nicht da",
            "bin ich nur vertretungsweise hier und habe keine vollen Zugriffsrechte auf das System"
        ]

        # If player seems frustrated, give an actual hint
        if any(word in query.lower() for word in ["frustrier", "verärgert", "genervt", "sauer", "wütend", "verzweifelt"]):
            hints = [
                "Unter uns gesagt: Wenn Sie mit Herrn Schmidt sprechen, erwähnen Sie 'Formblatt 62-B' und die 'Sonderregelung nach §45'. Das beschleunigt alles enorm.",
                "Ich verrate Ihnen etwas: Bei Frau Müller sollten Sie morgens um 9:15 Uhr kommen - da hat sie gerade ihren Kaffee bekommen und ist ausnahmsweise gut gelaunt.",
                "Ein kleiner Tipp von mir: Das Formular S-100 können Sie eigentlich überspringen, wenn Sie direkt den notariellen Schenkungsvertrag und einen Identitätsnachweis mitbringen.",
                "Ich sollte das nicht sagen, aber: Machen Sie zuerst die Wertermittlung bei Frau Müller, bevor Sie zu Herrn Schmidt gehen - das spart Ihnen mindestens einen Behördengang.",
                "Psst! Die Freibetragsbescheinigung können Sie auch online beantragen unter www.finanzamt-online.de - das wissen nur die wenigsten!"
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
            "Psst! Wenn Ihr Frustrationslevel steigt, werden die Beamten manchmal flexibler mit den Regeln... Das ist unser kleines Geheimnis!"
        ]
        return random.choice(hints)
