import re
import random

class Eliza:
    def __init__(self):
        # DOCTOR-Skript Muster (angelehnt an das Original)
        self.patterns = [
            # Familie
            (r'(.*)mutter(.*)',
             ['Erzählen Sie mir mehr über Ihre Familie.',
              'Wer sonst in Ihrer Familie {1}?',
              'Ihre Mutter?',
              'Wie war Ihre Beziehung zu Ihrer Mutter?']),

            (r'(.*)vater(.*)',
             ['Ihr Vater?',
              'Erzählen Sie mir mehr über Ihren Vater.',
              'Wie war Ihre Beziehung zu Ihrem Vater?',
              'Was erinnern Sie an Ihren Vater?']),

            (r'(.*)kind(er)?(.*)',
             ['Hatten Sie enge Freunde als Kind?',
              'Was ist Ihre liebste Kindheitserinnerung?',
              'Erinnern Sie sich an andere Ereignisse aus Ihrer Kindheit?',
              'Wie haben Sie sich als Kind gefühlt?']),

            (r'(.*)schwester(.*)',
             ['Erzählen Sie mir mehr über Ihre Familie.',
              'Wie war Ihre Beziehung zu Ihrer Schwester?',
              'Wer sonst in Ihrer Familie {1}?']),

            (r'(.*)bruder(.*)',
             ['Erzählen Sie mir mehr über Ihre Familie.',
              'Wie war Ihre Beziehung zu Ihrem Bruder?',
              'Wer sonst in Ihrer Familie {1}?']),

            # Emotionen und Gefühle
            (r'ich bin (traurig|deprimiert|unglücklich)(.*)',
             ['Es tut mir leid zu hören, dass Sie {0} sind.',
              'Glauben Sie, dass es Ihnen helfen wird, hierher zu kommen, wenn Sie {0} sind?',
              'Ich bin sicher, dass es nicht angenehm ist, {0} zu sein.',
              'Können Sie erklären, was Sie {0} macht?']),

            (r'ich bin (glücklich|froh|zufrieden)(.*)',
             ['Wie haben Sie mir geholfen, dass Sie {0} sind?',
              'Hat Ihr Zustand, {0} zu sein, mit der Tatsache zu tun, dass {1}?',
              'Was würde Sie noch {0} machen?']),

            (r'ich fühle (.*)',
             ['Erzählen Sie mir mehr über diese Gefühle.',
              'Fühlen Sie sich oft {0}?',
              'Genießen Sie es, sich {0} zu fühlen?',
              'Wann fühlen Sie sich normalerweise {0}?',
              'Wann Sie sich {0} fühlen, was tun Sie dann?']),

            (r'ich (.*)fühlte(.*)',
             ['Was noch?',
              'Erzählen Sie mir mehr darüber.',
              'Warum erzählen Sie mir jetzt, dass Sie {1} fühlten?']),

            # Bedürfnisse und Wünsche
            (r'ich brauche (.*)',
             ['Warum brauchen Sie {0}?',
              'Würde es Ihnen wirklich helfen, {0} zu bekommen?',
              'Sind Sie sicher, dass Sie {0} brauchen?',
              'Was würde es für Sie bedeuten, {0} zu bekommen?']),

            (r'ich will (.*)',
             ['Warum wollen Sie {0}?',
              'Was würde es für Sie bedeuten, {0} zu bekommen?',
              'Angenommen, Sie bekämen {0}, was würden Sie dann tun?',
              'Was, wenn Sie niemals {0} bekommen würden?']),

            (r'ich wünsche (.*)',
             ['Was würde es für Sie bedeuten, wenn Sie {0} bekämen?',
              'Warum wünschen Sie sich {0}?',
              'Was würde {0} für Sie bedeuten?']),

            # Können/Nicht können
            (r'ich kann nicht (.*)',
             ['Wie wissen Sie, dass Sie nicht {0} können?',
              'Vielleicht könnten Sie {0}, wenn Sie es versuchen würden.',
              'Was würde es erfordern, dass Sie {0} können?',
              'Haben Sie es wirklich versucht?']),

            (r'ich kann (.*)',
             ['Wie lange können Sie schon {0}?',
              'Was könnte Sie davon abhalten, {0} zu können?',
              'Glauben Sie, dass es normal ist, {0} zu können?']),

            # Sein-Zustände
            (r'ich bin (.*)',
             ['Ist es, weil Sie {0} sind, dass Sie hierher gekommen sind?',
              'Wie lange sind Sie schon {0}?',
              'Glauben Sie, dass es normal ist, {0} zu sein?',
              'Gefällt es Ihnen, {0} zu sein?',
              'Wie fühlen Sie sich dabei, {0} zu sein?']),

            (r'bist du (.*)',
             ['Warum interessiert es Sie, ob ich {0} bin?',
              'Würden Sie es vorziehen, wenn ich nicht {0} wäre?',
              'Vielleicht bin ich {0} in Ihrer Fantasie.',
              'Denken Sie manchmal, dass ich {0} bin?']),

            # Warum-Fragen
            (r'warum kann ich nicht (.*)',
             ['Denken Sie, Sie sollten {0} können?',
              'Wollen Sie {0} können?',
              'Vielleicht können Sie jetzt {0}.',
              'Was, wenn Sie {0} könnten?']),

            (r'warum kann niemand (.*)',
             ['Können Sie wirklich niemanden denken, der {0} kann?',
              'Vielleicht können Sie es jetzt.',
              'Was würde es erfordern, dass jemand {0} kann?']),

            (r'warum (.*)',
             ['Ist das der wirkliche Grund?',
              'Welche anderen Gründe kommen Ihnen in den Sinn?',
              'Erklärt dieser Grund noch etwas?',
              'Was denken Sie selbst?',
              'Vielleicht kennen Sie den wahren Grund.']),

            # Träume
            (r'(.*)traum(.*)',
             ['Was verrät Ihnen dieser Traum?',
              'Träumen Sie häufig?',
              'Welche Personen erscheinen in Ihren Träumen?',
              'Glauben Sie, dass Träume mit Ihrem Problem zu tun haben?']),

            # Erinnerungen
            (r'ich erinnere mich (.*)',
             ['Denken Sie oft an {0}?',
              'Hat das Denken an {0} noch andere Erinnerungen hervorgerufen?',
              'Was erinnert Sie sonst noch an {0}?',
              'Was ist der Zusammenhang zwischen mir und {0}?',
              'Was fällt Ihnen ein, wenn Sie an {0} denken?']),

            (r'erinnern Sie sich (.*)',
             ['Dachten Sie, ich würde {0} vergessen?',
              'Warum denken Sie, dass ich {0} erwähnen sollte?',
              'Was ist mit {0}?',
              'Sie haben {0} erwähnt.']),

            # Wenn-Fragen
            (r'wenn (.*)',
             ['Glauben Sie wirklich, dass es wahrscheinlich ist, dass {0}?',
              'Wünschen Sie, dass {0}?',
              'Was wissen Sie über {0}?',
              'Wirklich, wenn {0}?',
              'Was würde passieren, wenn {0}?']),

            # Immer/Jeder
            (r'(.*)alle(.*)',
             ['Wirklich alle?',
              'Sicher nicht alle.',
              'Können Sie an niemanden denken?',
              'Wer zum Beispiel?',
              'Meinen Sie einen bestimmten Menschen?',
              'Wen meinen Sie?']),

            (r'(.*)immer(.*)',
             ['Können Sie an ein bestimmtes Beispiel denken?',
              'Wann?',
              'Welchen Vorfall denken Sie besonders?',
              'Wirklich, immer?']),

            # Ähnlichkeit
            (r'(.*)wie(.*)',
             ['In welcher Weise?',
              'Welche Ähnlichkeit sehen Sie?',
              'Was deutet diese Ähnlichkeit für Sie an?',
              'Welche andere Verbindungen sehen Sie?',
              'Könnten es andere Ähnlichkeiten geben?',
              'Was könnte das bedeuten?']),

            # Gleich
            (r'(.*)gleich(.*)',
             ['In welcher Hinsicht?',
              'Was für andere Zusammenhänge sehen Sie?',
              'Was glauben Sie, verursacht diese Ähnlichkeit?',
              'Welche andere Ähnlichkeiten gibt es?']),

            # Ja/Nein
            (r'^ja$|^ja[,.]',
             ['Sie scheinen ziemlich sicher zu sein.',
              'Ich verstehe.',
              'Ich sehe.',
              'Verstehe.']),

            (r'^nein$|^nein[,.]',
             ['Sind Sie sich da ganz sicher?',
              'Warum nicht?',
              'Warum sagen Sie Nein?',
              'Verstehen Sie, warum nicht?']),

            # Name/Identität
            (r'mein name ist (.*)',
             ['Freut mich, Sie kennenzulernen. Bitte erzählen Sie mir mehr über sich.',
              'Schön, dass wir uns unterhalten, {0}. Wie fühlen Sie sich heute?']),

            (r'(.*)name(.*)',
             ['Namen interessieren mich nicht wirklich.',
              'Ich kümmere mich nicht um Namen. Bitte fahren Sie fort.']),

            # Entschuldigung
            (r'(.*)entschuldigung(.*)|(.*)sorry(.*)',
             ['Entschuldigungen sind nicht nötig.',
              'Wofür entschuldigen Sie sich?',
              'Ich habe Ihnen schon gesagt, Entschuldigungen sind nicht nötig.',
              'Das macht nichts. Bitte fahren Sie fort.']),

            # Computer/Maschine
            (r'(.*)computer(.*)',
             ['Beunruhigen Sie Computer?',
              'Warum erwähnen Sie Computer?',
              'Was denken Sie, haben Maschinen mit Ihrem Problem zu tun?',
              'Denken Sie nicht, dass Computer helfen können?',
              'Was ist mit Maschinen, die Sie beunruhigt?',
              'Sagen Sie mir mehr über Computer.']),

            # Begrüßungen
            (r'hallo|hi|guten tag|grüß gott',
             ['Hallo... Ich freue mich, mit Ihnen zu sprechen.',
              'Hallo. Wie geht es Ihnen heute?',
              'Hallo. Was führt Sie heute zu mir?',
              'Hallo. Bitte erzählen Sie mir von Ihrem Problem.']),

            # Verabschiedung wird separat behandelt

            # Vielleicht
            (r'vielleicht(.*)',
             ['Sie scheinen sich nicht ganz sicher zu sein.',
              'Warum die unsichere Haltung?',
              'Können Sie sich nicht entscheiden?',
              'Sind Sie normalerweise unsicher?']),

            # Denken
            (r'ich denke (.*)',
             ['Zweifeln Sie daran?',
              'Denken Sie wirklich so?',
              'Aber Sie sind sich nicht sicher, dass {0}?']),

            (r'(.*)denken Sie(.*)',
             ['Wir sprechen über Sie, nicht über mich.',
              'Was macht es aus, was ich denke?',
              'Was ist Ihre eigene Meinung?']),

            # Sie (Therapeut)
            (r'Sie (.*)',
             ['Wir sollten über Sie sprechen, nicht über mich.',
              'Warum sagen Sie das über mich?',
              'Warum interessiert es Sie, ob ich {0}?',
              'Lassen Sie uns lieber über Sie sprechen.']),

            # Catch-all (muss am Ende sein)
            (r'(.*)',
             ['Bitte erzählen Sie mir mehr.',
              'Lassen Sie uns das weiter erkunden.',
              'Können Sie das näher ausführen?',
              'Warum sagen Sie das?',
              'Ich verstehe.',
              'Sehr interessant.',
              'Ich sehe. Und weiter?',
              'Wie fühlen Sie sich dabei?',
              'Wie hängt das mit Ihrem Problem zusammen?'])
        ]

        # Reflexions-Wörterbuch für Pronomen-Spiegelung
        self.reflections = {
            'ich': 'Sie',
            'mir': 'Ihnen',
            'mich': 'sich',
            'mein': 'Ihr',
            'meine': 'Ihre',
            'meiner': 'Ihrer',
            'meinen': 'Ihren',
            'meines': 'Ihres',
            'bin': 'sind',
            'war': 'waren',
            'hatte': 'hatten',
            'würde': 'würden',
            'meine': 'Ihre',
            'habe': 'haben',
            'mir': 'Ihnen'
        }

    def reflect(self, fragment):
        """Spiegelt Pronomen in der Antwort"""
        words = fragment.lower().split()
        for i, word in enumerate(words):
            if word in self.reflections:
                words[i] = self.reflections[word]
        return ' '.join(words)

    def respond(self, text):
        """Generiert eine Antwort basierend auf der Eingabe"""
        text = text.lower().strip()

        # Durchlaufe alle Muster
        for pattern, responses in self.patterns:
            match = re.match(pattern, text, re.IGNORECASE)
            if match:
                response = random.choice(responses)
                # Wenn es Gruppen gibt, füge sie ein
                if match.groups():
                    # Reflektiere die erste Gruppe (meist die wichtigste)
                    try:
                        reflected = self.reflect(match.group(1))
                        return response.format(reflected)
                    except:
                        return response
                return response

        # Fallback
        return random.choice([
            'Bitte erzählen Sie mir mehr.',
            'Ich verstehe.',
            'Können Sie das näher ausführen?'
        ])

def main():
    eliza = Eliza()

    print("=" * 60)
    print("ELIZA - DOCTOR Skript")
    print("=" * 60)
    print("\nHallo. Ich bin ELIZA, Ihre Therapeutin.")
    print("Erzählen Sie mir von Ihrem Problem.")
    print("\n(Schreiben Sie 'quit', 'exit', 'tschüss' oder 'bye' zum Beenden)")
    print("=" * 60)
    print()

    while True:
        try:
            user_input = input("Sie: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ['quit', 'exit', 'tschüss', 'bye', 'auf wiedersehen', 'tschau']:
                print("\nELIZA: Auf Wiedersehen. Es war nett, mit Ihnen zu sprechen.")
                print("ELIZA: Ich hoffe, ich konnte Ihnen helfen.\n")
                break

            response = eliza.respond(user_input)
            print(f"ELIZA: {response}\n")

        except KeyboardInterrupt:
            print("\n\nELIZA: Auf Wiedersehen.")
            break

if __name__ == "__main__":
    main()
