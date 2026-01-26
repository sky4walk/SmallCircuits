class SubwordTokenizer:
    """
    Ein Tokenizer mit Subword-Tokenisierung (Byte-Pair Encoding - BPE).
    Kann unbekannte Wörter in kleinere Teile zerlegen.
    """

    def __init__(self):
        # Vokabular: Wort -> ID
        self.vocab = {}
        # Reverse-Mapping: ID -> Wort
        self.id_to_token = {}
        # Zähler für Häufigkeiten
        self.token_counts = {}
        # BPE-Merge-Regeln (welche Paare wurden zusammengefügt)
        self.merges = []
        # Nächste freie ID
        self.next_id = 0

        # Initialisiere mit Spezial-Tokens
        self._add_token("<PAD>")  # Padding
        self._add_token("<UNK>")  # Unknown
        self._add_token("<BOS>")  # Begin of Sequence
        self._add_token("<EOS>")  # End of Sequence

        # Füge alle Kleinbuchstaben a-z hinzu
        print("Initialisiere Basis-Vokabular mit a-z...")
        for char in 'abcdefghijklmnopqrstuvwxyz':
            self._add_token(char, 0)
            self._add_token(char + '</w>', 0)  # Auch mit Wortende-Marker

        # Füge häufige Satzzeichen hinzu
        for punct in '.,!?;:-\'\"':
            self._add_token(punct, 0)
            self._add_token(punct + '</w>', 0)

        # Füge Leerzeichen und Zahlen hinzu
        for digit in '0123456789':
            self._add_token(digit, 0)
            self._add_token(digit + '</w>', 0)

        print(f"Basis-Vokabular initialisiert: {len(self.vocab)} Tokens")

    def _split_into_words(self, text):
        """
        Teilt einen Text in Wörter und Satzzeichen auf.
        Ersetzt: re.findall(r'\w+|[^\w\s]', text.lower())

        Beispiel: "Hallo Welt!" -> ['hallo', 'welt', '!']
        """
        words = []
        current_word = ""

        for char in text.lower():
            if char.isalnum():  # Buchstabe (a-z) oder Zahl (0-9)
                current_word += char
            else:
                # Wir sind bei einem Nicht-Buchstaben angekommen
                if current_word:
                    words.append(current_word)
                    current_word = ""

                # Füge Satzzeichen hinzu (aber keine Leerzeichen)
                if not char.isspace():
                    words.append(char)

        # Vergiss nicht das letzte Wort
        if current_word:
            words.append(current_word)

        return words

    def _is_word_char(self, token):
        """
        Prüft, ob ein Token ein Wort ist (nicht Satzzeichen).
        Ersetzt: re.match(r'\w+', token)
        """
        if not token:
            return False
        return token[0].isalnum()

    def _replace_pair_in_string(self, text, pair, replacement):
        """
        Ersetzt ein Zeichenpaar in einem String.
        Ersetzt: re.sub(pattern, replacement, text)

        Beispiel: "a b c" mit pair=('a', 'b') -> "ab c"
        """
        search_pattern = ' '.join(pair)

        # Einfacher String-Replace
        result = text.replace(search_pattern, replacement)

        return result

    def _add_token(self, token, count=1):
        """Fügt ein Token zum Vokabular hinzu."""
        if token not in self.vocab:
            self.vocab[token] = self.next_id
            self.id_to_token[self.next_id] = token
            self.token_counts[token] = count
            self.next_id += 1
        else:
            self.token_counts[token] += count

    def _get_word_characters(self, word):
        """
        Zerlegt ein Wort in einzelne Zeichen mit Endmarker.
        'hallo' -> ['h', 'a', 'l', 'l', 'o</w>']
        </w> markiert das Wortende
        """
        chars = list(word)
        chars[-1] = chars[-1] + '</w>'  # Markiere Wortende
        return chars

    def _get_pairs(self, chars):
        """
        Findet alle benachbarten Zeichenpaare.
        ['h', 'a', 'l'] -> {('h', 'a'), ('a', 'l')}
        """
        pairs = set()
        for i in range(len(chars) - 1):
            pairs.add((chars[i], chars[i + 1]))
        return pairs

    def train_bpe(self, texts, num_merges=10):
        """
        Trainiert BPE auf einer Liste von Texten.

        Args:
            texts: Liste von Trainingstexten
            num_merges: Anzahl der BPE-Merge-Operationen
        """
        print(f"\n{'='*60}")
        print(f"TRAINING BPE mit {num_merges} Merges")
        print(f"{'='*60}")

        # Schritt 1: Sammle alle Wörter
        # Statt defaultdict(int) nutzen wir ein normales Dictionary
        word_freqs = {}
        for text in texts:
            words = self._split_into_words(text)
            for word in words:
                # Prüfe, ob das Wort schon existiert
                if word in word_freqs:
                    word_freqs[word] += 1
                else:
                    word_freqs[word] = 1

        print(f"\nGefundene einzigartige Wörter: {len(word_freqs)}")
        print(f"Wort-Häufigkeiten: {word_freqs}")

        # Schritt 2: Initialisiere mit einzelnen Zeichen
        vocab = {}
        for word, freq in word_freqs.items():
            chars = self._get_word_characters(word)
            vocab[' '.join(chars)] = freq
            # Zeichen sind bereits im Vokabular (a-z wurde in __init__ hinzugefügt)

        print(f"\nStart-Vokabular (Zeichen-Ebene):")
        print(f"  {list(vocab.keys())[:3]}...")

        # Schritt 3: BPE-Training - Merge die häufigsten Paare
        for merge_step in range(num_merges):
            # Zähle alle Paare - nutze normales Dictionary statt defaultdict
            pairs_count = {}
            for word, freq in vocab.items():
                chars = word.split()
                for pair in self._get_pairs(chars):
                    # Prüfe, ob das Paar schon existiert
                    if pair in pairs_count:
                        pairs_count[pair] += freq
                    else:
                        pairs_count[pair] = freq

            if not pairs_count:
                print(f"\nKeine weiteren Paare zum Mergen gefunden.")
                break

            # Finde das häufigste Paar
            best_pair = max(pairs_count, key=pairs_count.get)
            print(f"\nMerge {merge_step + 1}: '{best_pair[0]}' + '{best_pair[1]}' -> '{best_pair[0]}{best_pair[1]}' (Häufigkeit: {pairs_count[best_pair]})")

            # Speichere Merge-Regel
            self.merges.append(best_pair)

            # Merge das Paar im Vokabular
            new_vocab = {}
            search_pattern = ' '.join(best_pair)
            replacement = ''.join(best_pair)

            for word, freq in vocab.items():
                new_word = self._replace_pair_in_string(word, best_pair, replacement)
                new_vocab[new_word] = freq

            vocab = new_vocab

            # Füge das neue Subword-Token hinzu
            self._add_token(replacement, 0)

        print(f"\n{'='*60}")
        print(f"Training abgeschlossen!")
        print(f"Finale Vokabulargröße: {len(self.vocab)}")
        print(f"{'='*60}")

    def _apply_bpe(self, word):
        """
        Wendet BPE-Merges auf ein Wort an.
        """
        chars = self._get_word_characters(word)

        # Wende alle gelernten Merges an
        for merge_pair in self.merges:
            i = 0
            while i < len(chars) - 1:
                if (chars[i], chars[i + 1]) == merge_pair:
                    # Merge die beiden Zeichen
                    chars[i] = chars[i] + chars[i + 1]
                    chars.pop(i + 1)
                else:
                    i += 1

        return chars

    def tokenize(self, text):
        """
        Tokenisiert Text mit BPE.
        """
        print(f"\n{'='*60}")
        print(f"Tokenisiere: '{text}'")
        print(f"{'='*60}")

        words = self._split_into_words(text)
        all_tokens = []

        for word in words:
            # Wende BPE an
            subwords = self._apply_bpe(word)
            print(f"  '{word}' -> {subwords}")
            all_tokens.extend(subwords)

        # Konvertiere zu IDs
        token_ids = []
        for token in all_tokens:
            if token in self.vocab:
                token_ids.append(self.vocab[token])
            else:
                # Unbekanntes Token
                token_ids.append(self.vocab["<UNK>"])

        print(f"Tokens: {all_tokens}")
        print(f"Token-IDs: {token_ids}")
        return token_ids

    def detokenize(self, token_ids):
        """
        Rekonstruiert Text aus Token-IDs.
        """
        print(f"\nDetokenisiere: {token_ids}")

        tokens = []
        for token_id in token_ids:
            if token_id in self.id_to_token:
                tokens.append(self.id_to_token[token_id])
            else:
                tokens.append("<UNK>")

        # Entferne </w> Marker und füge Leerzeichen ein
        text = ''.join(tokens).replace('</w>', ' ').strip()
        print(f"Rekonstruiert: '{text}'")
        return text

    def show_vocabulary(self):
        """Zeigt das Vokabular."""
        print(f"\n{'='*60}")
        print("VOKABULAR")
        print(f"{'='*60}")
        for token, token_id in sorted(self.vocab.items(), key=lambda x: x[1]):
            count = self.token_counts.get(token, 0)
            print(f"  ID {token_id:3d}: '{token}' (Häufigkeit: {count})")

    def show_merges(self):
        """Zeigt die gelernten BPE-Merges."""
        print(f"\n{'='*60}")
        print("BPE MERGE-REGELN")
        print(f"{'='*60}")
        for i, (a, b) in enumerate(self.merges):
            print(f"  {i + 1}. '{a}' + '{b}' -> '{a}{b}'")

    def incremental_train(self, new_text, num_merges=5):
        """
        Trainiert den Tokenizer auf neuem Text nach.
        Erweitert das Vokabular um neue Zeichen und Subwords.

        Args:
            new_text: Neuer Text zum Nachtrainieren
            num_merges: Anzahl zusätzlicher BPE-Merges
        """
        print(f"\n{'='*60}")
        print(f"NACHTRAINING mit neuem Text: '{new_text}'")
        print(f"{'='*60}")

        # Extrahiere Wörter
        words = self._split_into_words(new_text)

        # Sammle Wort-Häufigkeiten
        word_freqs = {}
        for word in words:
            if word in word_freqs:
                word_freqs[word] += 1
            else:
                word_freqs[word] = 1

        print(f"Neue Wörter: {word_freqs}")

        # Initialisiere Vokabular mit Zeichen-Ebene
        vocab = {}
        for word, freq in word_freqs.items():
            chars = self._get_word_characters(word)

            # Prüfe auf unbekannte Zeichen (sollte nicht passieren bei a-z)
            for char in chars:
                if char not in self.vocab:
                    print(f"  WARNUNG: Unbekanntes Zeichen '{char}' - füge hinzu")
                    self._add_token(char, 0)

            # Wende bereits gelernte Merges an
            current_chars = chars[:]
            for merge_pair in self.merges:
                i = 0
                while i < len(current_chars) - 1:
                    if (current_chars[i], current_chars[i + 1]) == merge_pair:
                        current_chars[i] = current_chars[i] + current_chars[i + 1]
                        current_chars.pop(i + 1)
                    else:
                        i += 1

            vocab[' '.join(current_chars)] = freq

        print(f"\nVokabular nach Anwendung alter Merges:")
        for v in vocab.keys():
            print(f"  {v}")

        # Führe zusätzliche Merges durch
        initial_merges = len(self.merges)
        for merge_step in range(num_merges):
            # Zähle Paare
            pairs_count = {}
            for word, freq in vocab.items():
                chars = word.split()
                for pair in self._get_pairs(chars):
                    if pair in pairs_count:
                        pairs_count[pair] += freq
                    else:
                        pairs_count[pair] = freq

            if not pairs_count:
                print(f"\nKeine weiteren Paare zum Mergen.")
                break

            # Finde häufigstes Paar
            best_pair = max(pairs_count, key=pairs_count.get)

            # Prüfe, ob dieser Merge schon existiert
            if best_pair in self.merges:
                print(f"\nMerge '{best_pair[0]}' + '{best_pair[1]}' existiert bereits, überspringe.")
                continue

            print(f"\nNeuer Merge {len(self.merges) - initial_merges + 1}: '{best_pair[0]}' + '{best_pair[1]}' -> '{best_pair[0]}{best_pair[1]}' (Häufigkeit: {pairs_count[best_pair]})")

            # Speichere Merge
            self.merges.append(best_pair)

            # Merge im Vokabular
            new_vocab = {}
            search_pattern = ' '.join(best_pair)
            replacement = ''.join(best_pair)

            for word, freq in vocab.items():
                new_word = self._replace_pair_in_string(word, best_pair, replacement)
                new_vocab[new_word] = freq

            vocab = new_vocab

            # Füge Token hinzu
            self._add_token(replacement, 0)

        print(f"\n{'='*60}")
        print(f"Nachtraining abgeschlossen!")
        print(f"Neue Vokabulargröße: {len(self.vocab)}")
        print(f"Anzahl Merges: {len(self.merges)}")
        print(f"{'='*60}")


# Beispielverwendung
if __name__ == "__main__":
    tokenizer = SubwordTokenizer()

    # Trainiere auf Beispieltexten
    training_texts = [
        "hallo welt",
        "hallo nochmal",
        "welt der wunder",
        "test test test"
    ]

    tokenizer.train_bpe(training_texts, num_merges=15)

    # Zeige Ergebnisse
    tokenizer.show_merges()
    tokenizer.show_vocabulary()

    # Tokenisiere neue Texte
    tokens1 = tokenizer.tokenize("hallo welt")
    text1 = tokenizer.detokenize(tokens1)

    print("\n" + "="*60)

    # Teste mit vorher unbekanntem Wort - jetzt sollte es funktionieren!
    print("TESTE MIT VORHER UNBEKANNTEM WORT:")
    tokens2 = tokenizer.tokenize("hallo super")
    text2 = tokenizer.detokenize(tokens2)

    print("\n" + "="*60)
    print("TESTE MIT KOMPLETT NEUEM WORT:")
    tokens3 = tokenizer.tokenize("python programmierung")
    text3 = tokenizer.detokenize(tokens3)
