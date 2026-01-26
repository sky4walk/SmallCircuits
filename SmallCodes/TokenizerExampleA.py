# https://claude.ai/public/artifacts/c3b85be8-4ec2-44db-90d4-413851a73ae5
class EmbeddingLayer:
    """
    Embedding-Layer: Wandelt Token-IDs in Vektoren um.
    Jedes Token bekommt einen gelernten Vektor mit embedding_dim Dimensionen.
    """

    def __init__(self, vocab_size, embedding_dim=64):
        """
        Args:
            vocab_size: Anzahl der unterschiedlichen Tokens
            embedding_dim: Dimensionalität der Embedding-Vektoren
        """
        self.vocab_size = vocab_size
        self.embedding_dim = embedding_dim

        # Initialisiere Embedding-Matrix zufällig
        # Jede Zeile ist der Vektor für ein Token
        print(f"\nInitialisiere Embedding-Layer:")
        print(f"  Vokabulargröße: {vocab_size}")
        print(f"  Embedding-Dimension: {embedding_dim}")

        self.embeddings = self._initialize_embeddings()

    def _initialize_embeddings(self):
        """
        Erstellt zufällige Embedding-Vektoren für jedes Token.
        Verwendet kleine Zufallswerte zwischen -0.1 und 0.1
        """
        import random

        embeddings = []
        for token_id in range(self.vocab_size):
            # Erstelle einen Vektor mit embedding_dim Dimensionen
            vector = []
            for _ in range(self.embedding_dim):
                # Kleine Zufallswerte
                value = (random.random() - 0.5) * 0.2  # Bereich: -0.1 bis 0.1
                vector.append(value)
            embeddings.append(vector)

        return embeddings

    def embed(self, token_id):
        """
        Wandelt eine einzelne Token-ID in einen Vektor um.

        Args:
            token_id: ID des Tokens

        Returns:
            Embedding-Vektor (Liste von Zahlen)
        """
        if token_id < 0 or token_id >= self.vocab_size:
            print(f"WARNUNG: Token-ID {token_id} außerhalb des Vokabulars!")
            return [0.0] * self.embedding_dim

        return self.embeddings[token_id]

    def embed_sequence(self, token_ids):
        """
        Wandelt eine Sequenz von Token-IDs in Vektoren um.

        Args:
            token_ids: Liste von Token-IDs

        Returns:
            Liste von Embedding-Vektoren
        """
        embedded_sequence = []
        for token_id in token_ids:
            vector = self.embed(token_id)
            embedded_sequence.append(vector)

        return embedded_sequence

    def show_embedding(self, token_id, token_str=None):
        """
        Zeigt das Embedding für ein Token an.
        """
        if token_id < self.vocab_size:
            vector = self.embeddings[token_id]

            print(f"\nEmbedding für Token-ID {token_id}", end="")
            if token_str:
                print(f" ('{token_str}')", end="")
            print(":")

            # Zeige ersten Teil des Vektors
            preview = vector[:8] if len(vector) > 8 else vector
            print(f"  Vektor (erste 8 Dimensionen): {[round(v, 4) for v in preview]}")
            print(f"  Gesamt-Dimensionen: {len(vector)}")

    def cosine_similarity(self, vec1, vec2):
        """
        Berechnet die Kosinus-Ähnlichkeit zwischen zwei Vektoren.
        Wert zwischen -1 (komplett unterschiedlich) und 1 (identisch).
        """
        # Skalarprodukt (dot product)
        dot_product = 0.0
        for i in range(len(vec1)):
            dot_product += vec1[i] * vec2[i]

        # Länge (Magnitude) der Vektoren
        mag1 = 0.0
        mag2 = 0.0
        for i in range(len(vec1)):
            mag1 += vec1[i] ** 2
            mag2 += vec2[i] ** 2

        mag1 = mag1 ** 0.5  # Quadratwurzel
        mag2 = mag2 ** 0.5

        # Verhindere Division durch Null
        if mag1 == 0.0 or mag2 == 0.0:
            return 0.0

        return dot_product / (mag1 * mag2)


class PositionalEncoding:
    """
    Positional Encoding: Fügt Information über die Position im Text hinzu.
    Verwendet Sinus- und Kosinus-Funktionen (wie im Original Transformer).
    """

    def __init__(self, embedding_dim, max_sequence_length=512):
        """
        Args:
            embedding_dim: Dimensionalität der Embeddings
            max_sequence_length: Maximale Sequenzlänge
        """
        self.embedding_dim = embedding_dim
        self.max_sequence_length = max_sequence_length

        print(f"\nInitialisiere Positional Encoding:")
        print(f"  Embedding-Dimension: {embedding_dim}")
        print(f"  Max. Sequenzlänge: {max_sequence_length}")

        # Berechne Positional Encodings vorher
        self.positional_encodings = self._create_positional_encodings()

    def _create_positional_encodings(self):
        """
        Erstellt Positional Encoding Vektoren mit Sinus/Kosinus.
        Formel aus "Attention is All You Need" Paper.
        """
        import math

        encodings = []

        for pos in range(self.max_sequence_length):
            encoding = []

            for i in range(self.embedding_dim):
                # Berechne Frequenz
                freq = 1.0 / (10000 ** (2 * (i // 2) / self.embedding_dim))

                # Wechsel zwischen sin und cos
                if i % 2 == 0:
                    value = math.sin(pos * freq)
                else:
                    value = math.cos(pos * freq)

                encoding.append(value)

            encodings.append(encoding)

        return encodings

    def add_positional_encoding(self, embedded_sequence):
        """
        Fügt Positional Encoding zu einer embedded Sequenz hinzu.

        Args:
            embedded_sequence: Liste von Embedding-Vektoren

        Returns:
            Sequenz mit hinzugefügtem Positional Encoding
        """
        result = []

        for pos, embedding_vector in enumerate(embedded_sequence):
            if pos >= self.max_sequence_length:
                print(f"WARNUNG: Position {pos} überschreitet max_sequence_length!")
                break

            # Addiere Positional Encoding zum Embedding
            pos_encoding = self.positional_encodings[pos]
            combined = []

            for i in range(len(embedding_vector)):
                combined.append(embedding_vector[i] + pos_encoding[i])

            result.append(combined)

        return result

    def show_positional_encoding(self, position):
        """
        Zeigt das Positional Encoding für eine bestimmte Position.
        """
        if position < len(self.positional_encodings):
            encoding = self.positional_encodings[position]
            preview = encoding[:8] if len(encoding) > 8 else encoding

            print(f"\nPositional Encoding für Position {position}:")
            print(f"  Vektor (erste 8 Dimensionen): {[round(v, 4) for v in preview]}")


class SubwordTokenizer:
    """
    Ein Tokenizer mit Subword-Tokenisierung (Byte-Pair Encoding - BPE).
    Kann unbekannte Wörter in kleinere Teile zerlegen.
    Komplett ohne externe Bibliotheken wie 're' implementiert.
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
        word_freqs = {}
        for text in texts:
            words = self._split_into_words(text)
            for word in words:
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

        print(f"\nStart-Vokabular (Zeichen-Ebene):")
        print(f"  {list(vocab.keys())[:3]}...")

        # Schritt 3: BPE-Training - Merge die häufigsten Paare
        for merge_step in range(num_merges):
            # Zähle alle Paare
            pairs_count = {}
            for word, freq in vocab.items():
                chars = word.split()
                for pair in self._get_pairs(chars):
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

        # Fügt Leerzeichen zwischen Wörtern ein, aber nicht vor Satzzeichen
        result = []
        for i in range(len(tokens)):
            token = tokens[i]
            # Füge Leerzeichen vor Wörtern hinzu (aber nicht am Anfang)
            if i > 0 and self._is_word_char(token):
                result.append(' ')
            result.append(token)

        # Entferne </w> Marker
        text = ''.join(result).replace('</w>', ' ').strip()
        print(f"Rekonstruiert: '{text}'")
        return text

    def get_vocab_size(self):
        """Gibt die Größe des Vokabulars zurück."""
        return len(self.vocab)

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

    def create_training_pairs(self, token_ids, context_window=4, method='sliding'):
        """
        Erstellt Trainingspaare für LLM-Training aus Token-IDs.

        Args:
            token_ids: Liste von Token-IDs
            context_window: Größe des Kontextfensters
            method: 'sliding' (Sliding Window) oder 'autoregressive' (wachsend)

        Returns:
            Liste von (Eingabe, Ziel) Paaren
        """
        print(f"\n{'='*60}")
        print(f"ERSTELLE TRAININGSPAARE")
        print(f"Methode: {method}, Kontextfenster: {context_window}")
        print(f"{'='*60}")

        training_pairs = []

        if method == 'sliding':
            # Sliding Window: Festes Fenster gleitet über den Text
            for i in range(len(token_ids) - context_window):
                context = token_ids[i:i + context_window]
                target = token_ids[i + context_window]
                training_pairs.append((context, target))
                print(f"  {context} → {target}")

        elif method == 'autoregressive':
            # Autoregressive: Fenster wächst von 1 bis context_window
            for i in range(1, min(len(token_ids), context_window + 1)):
                context = token_ids[:i]
                target = token_ids[i]
                training_pairs.append((context, target))
                print(f"  {context} → {target}")

            # Dann sliding für den Rest
            for i in range(context_window, len(token_ids)):
                context = token_ids[i - context_window:i]
                target = token_ids[i]
                training_pairs.append((context, target))
                print(f"  {context} → {target}")

        else:
            print(f"Unbekannte Methode: {method}")
            return []

        print(f"\nAnzahl Trainingspaare: {len(training_pairs)}")
        return training_pairs

    def create_causal_mask(self, sequence_length):
        """
        Erstellt eine Causal Attention Mask für Transformer.
        Verhindert, dass das Modell in die Zukunft schauen kann.

        Args:
            sequence_length: Länge der Sequenz

        Returns:
            2D-Liste (Matrix) mit 0 (maskiert) und 1 (sichtbar)
        """
        print(f"\n{'='*60}")
        print(f"CAUSAL ATTENTION MASK (Sequenz-Länge: {sequence_length})")
        print(f"{'='*60}")

        # Erstelle Matrix: 1 = sichtbar, 0 = maskiert
        mask = []
        for i in range(sequence_length):
            row = []
            for j in range(sequence_length):
                # Token kann nur sich selbst und vorherige Tokens sehen
                if j <= i:
                    row.append(1)
                else:
                    row.append(0)
            mask.append(row)

        # Visualisiere die Mask
        print("\n1 = sichtbar, 0 = maskiert (kann nicht gesehen werden)")
        print("Zeilen = aktuelle Position, Spalten = zu welchen Positionen geschaut wird\n")

        # Header
        print("    ", end="")
        for j in range(sequence_length):
            print(f"T{j} ", end="")
        print()

        # Matrix ausgeben
        for i, row in enumerate(mask):
            print(f"T{i}: ", end="")
            for val in row:
                print(f" {val}  ", end="")
            print()

        return mask

    def prepare_batch(self, texts, context_window=4, batch_size=2):
        """
        Bereitet einen Batch von Texten für das Training vor.
        Tokenisiert, erstellt Trainingspaare und padded auf gleiche Länge.

        Args:
            texts: Liste von Texten
            context_window: Größe des Kontextfensters
            batch_size: Anzahl der Samples pro Batch

        Returns:
            Liste von Batches mit (Eingabe, Ziel) Paaren
        """
        print(f"\n{'='*60}")
        print(f"BATCH-VORBEREITUNG")
        print(f"Batch-Größe: {batch_size}, Kontextfenster: {context_window}")
        print(f"{'='*60}")

        all_pairs = []

        # Tokenisiere alle Texte und erstelle Trainingspaare
        for text in texts:
            print(f"\nVerarbeite: '{text}'")
            token_ids = self.tokenize(text)
            pairs = self.create_training_pairs(token_ids, context_window, method='sliding')
            all_pairs.extend(pairs)

        # Erstelle Batches
        batches = []
        for i in range(0, len(all_pairs), batch_size):
            batch = all_pairs[i:i + batch_size]

            # Padding: Bringe alle Eingaben auf gleiche Länge
            max_len = max(len(pair[0]) for pair in batch)
            padded_batch = []

            for context, target in batch:
                # Padde mit <PAD> Token (ID 0)
                padded_context = context + [self.vocab["<PAD>"]] * (max_len - len(context))
                padded_batch.append((padded_context, target))

            batches.append(padded_batch)

        print(f"\n{'='*60}")
        print(f"Batch-Übersicht:")
        print(f"  Gesamte Trainingspaare: {len(all_pairs)}")
        print(f"  Anzahl Batches: {len(batches)}")
        print(f"{'='*60}")

        # Zeige ersten Batch als Beispiel
        if batches:
            print(f"\nBeispiel - Batch 1:")
            for i, (context, target) in enumerate(batches[0]):
                print(f"  Sample {i+1}: {context} → {target}")

        return batches

    def load_training_texts_from_file(self, filepath, encoding='utf-8'):
        """
        Lädt Trainingstexte aus einer Datei.
        Jede Zeile in der Datei wird als separater Text behandelt.

        Args:
            filepath: Pfad zur Textdatei
            encoding: Zeichenkodierung der Datei (Standard: utf-8)

        Returns:
            Liste von Texten
        """
        print(f"\n{'='*60}")
        print(f"LADE TRAININGSDATEN AUS DATEI")
        print(f"Datei: {filepath}")
        print(f"{'='*60}")

        try:
            with open(filepath, 'r', encoding=encoding) as file:
                texts = []
                line_number = 0

                for line in file:
                    line_number += 1
                    # Entferne Zeilenumbrüche und Leerzeichen am Anfang/Ende
                    cleaned_line = line.strip()

                    # Überspringe leere Zeilen
                    if cleaned_line:
                        texts.append(cleaned_line)
                        if line_number <= 3:  # Zeige erste 3 Zeilen
                            print(f"  Zeile {line_number}: '{cleaned_line[:50]}...'")

                print(f"\n{'='*60}")
                print(f"Erfolgreich geladen:")
                print(f"  Gesamte Zeilen: {line_number}")
                print(f"  Nicht-leere Zeilen: {len(texts)}")
                print(f"{'='*60}")

                return texts

        except FileNotFoundError:
            print(f"\nFEHLER: Datei '{filepath}' wurde nicht gefunden!")
            print("Bitte überprüfe den Dateipfad.")
            return []

        except UnicodeDecodeError:
            print(f"\nFEHLER: Datei konnte nicht mit Encoding '{encoding}' gelesen werden!")
            print("Versuche ein anderes Encoding wie 'latin-1' oder 'cp1252'.")
            return []

        except Exception as e:
            print(f"\nFEHLER beim Laden der Datei: {e}")
            return []

    def train_from_file(self, filepath, num_merges=10, encoding='utf-8'):
        """
        Lädt Trainingsdaten aus einer Datei und trainiert BPE darauf.

        Args:
            filepath: Pfad zur Textdatei
            num_merges: Anzahl der BPE-Merge-Operationen
            encoding: Zeichenkodierung der Datei
        """
        texts = self.load_training_texts_from_file(filepath, encoding)

        if texts:
            self.train_bpe(texts, num_merges)
        else:
            print("Kein Training möglich - keine Texte geladen.")


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

    print("\n" + "="*60)
    print("=" * 60)
    print("LLM TRAINING VORBEREITUNG")
    print("=" * 60)
    print("="*60)

    # 1. Erstelle Trainingspaare mit Sliding Window
    print("\n1. SLIDING WINDOW METHODE:")
    test_tokens = tokenizer.tokenize("hallo welt test")
    pairs_sliding = tokenizer.create_training_pairs(test_tokens, context_window=3, method='sliding')

    print("\n" + "="*60)

    # 2. Erstelle Trainingspaare mit Autoregressive Methode
    print("\n2. AUTOREGRESSIVE METHODE (wachsendes Fenster):")
    pairs_auto = tokenizer.create_training_pairs(test_tokens, context_window=3, method='autoregressive')

    print("\n" + "="*60)

    # 3. Zeige Causal Attention Mask
    print("\n3. CAUSAL ATTENTION MASK:")
    mask = tokenizer.create_causal_mask(sequence_length=5)

    print("\n" + "="*60)

    # 4. Batch-Vorbereitung
    print("\n4. BATCH-VORBEREITUNG:")
    training_texts = ["hallo welt", "test example", "python code"]
    batches = tokenizer.prepare_batch(training_texts, context_window=3, batch_size=4)

    print("\n" + "="*60)
    print("TRAINING-PIPELINE KOMPLETT!")
    print("="*60)
    print("\nDiese Daten können jetzt verwendet werden, um ein LLM zu trainieren:")
    print("- Eingabe-Tokens werden durch Embedding-Layer gejagt")
    print("- Transformer verarbeitet mit Causal Mask")
    print("- Modell lernt, nächstes Token vorherzusagen")
    print("- Loss wird zwischen Vorhersage und echtem Ziel-Token berechnet")

    print("\n" + "="*60)
    print("="*60)
    print("TRAINING AUS DATEI (BEISPIEL)")
    print("="*60)
    print("="*60)

    # Beispiel: Training aus Datei
    # Wenn du eine Datei hast, kannst du sie so laden:

    # Option 1: Direkt trainieren
    # tokenizer2 = SubwordTokenizer()
    # tokenizer2.train_from_file('training_data.txt', num_merges=20)

    # Option 2: Nur Texte laden
    # training_texts = tokenizer.load_training_texts_from_file('training_data.txt')
    # tokenizer.train_bpe(training_texts, num_merges=20)

    print("\nBeispiel-Dateiformat (training_data.txt):")
    print("=" * 60)
    print("Das ist die erste Trainingszeile")
    print("Hier kommt eine zweite Zeile")
    print("Und noch mehr Text zum Trainieren")
    print("Jede Zeile ist ein separater Text")
    print("=" * 60)

    print("\nVerwendung:")
    print("  tokenizer.train_from_file('meine_datei.txt', num_merges=50)")
    print("\nODER für Batch-Training:")
    print("  texts = tokenizer.load_training_texts_from_file('meine_datei.txt')")
    print("  batches = tokenizer.prepare_batch(texts, context_window=4, batch_size=8)")

    print("\n" + "="*60)
    print("="*60)
    print("EMBEDDING LAYER - TOKEN IDs → VEKTOREN")
    print("="*60)
    print("="*60)

    # Erstelle Embedding Layer
    vocab_size = tokenizer.get_vocab_size()
    embedding_layer = EmbeddingLayer(vocab_size=vocab_size, embedding_dim=8)

    # Beispiel: Embedde einzelnes Token
    print("\n1. EINZELNES TOKEN EMBEDDEN:")
    test_token_id = tokenizer.vocab.get('hallo', 0)
    embedding_layer.show_embedding(test_token_id, 'hallo')

    # Beispiel: Embedde eine Sequenz
    print("\n2. SEQUENZ EMBEDDEN:")
    test_text = "hallo welt"
    test_token_ids = tokenizer.tokenize(test_text)
    embedded_seq = embedding_layer.embed_sequence(test_token_ids)

    print(f"\nEingebettete Sequenz:")
    print(f"  Anzahl Tokens: {len(embedded_seq)}")
    print(f"  Jeder Vektor hat {len(embedded_seq[0])} Dimensionen")
    print(f"  Erster Vektor: {[round(v, 4) for v in embedded_seq[0]]}")

    # Berechne Ähnlichkeit zwischen zwei Tokens
    if len(embedded_seq) >= 2:
        print("\n3. ÄHNLICHKEIT ZWISCHEN TOKENS:")
        similarity = embedding_layer.cosine_similarity(embedded_seq[0], embedded_seq[1])
        print(f"  Kosinus-Ähnlichkeit zwischen Token 0 und 1: {round(similarity, 4)}")
        print(f"  (Wert zwischen -1 und 1, höher = ähnlicher)")

    print("\n" + "="*60)
    print("="*60)
    print("POSITIONAL ENCODING - POSITION IM TEXT")
    print("="*60)
    print("="*60)

    # Erstelle Positional Encoding
    pos_encoding = PositionalEncoding(embedding_dim=8, max_sequence_length=100)

    # Zeige Positional Encoding für erste Positionen
    print("\n1. POSITIONAL ENCODINGS:")
    pos_encoding.show_positional_encoding(0)
    pos_encoding.show_positional_encoding(1)
    pos_encoding.show_positional_encoding(10)

    # Füge Positional Encoding zu Embeddings hinzu
    print("\n2. EMBEDDINGS + POSITIONAL ENCODING:")
    embedded_with_pos = pos_encoding.add_positional_encoding(embedded_seq)

    print(f"\nVorher (nur Embedding):")
    print(f"  Position 0: {[round(v, 4) for v in embedded_seq[0][:8]]}")
    print(f"\nNachher (Embedding + Position):")
    print(f"  Position 0: {[round(v, 4) for v in embedded_with_pos[0][:8]]}")

    print("\n" + "="*60)
    print("KOMPLETTE PIPELINE: TEXT → VEKTOREN")
    print("="*60)

    final_text = "test beispiel"
    print(f"\n1. Input-Text: '{final_text}'")

    final_tokens = tokenizer.tokenize(final_text)
    print(f"\n2. Tokenisiert: {final_tokens}")

    final_embedded = embedding_layer.embed_sequence(final_tokens)
    print(f"\n3. Embedded: {len(final_embedded)} Vektoren à {len(final_embedded[0])} Dimensionen")

    final_with_pos = pos_encoding.add_positional_encoding(final_embedded)
    print(f"\n4. Mit Positional Encoding: Bereit für Transformer!")
    print(f"   Shape: {len(final_with_pos)} Tokens × {len(final_with_pos[0])} Dimensionen")

    print("\n" + "="*60)
    print("FERTIG! NÄCHSTER SCHRITT: TRANSFORMER-ARCHITEKTUR")
    print("="*60)
    print("\nDie Vektoren können jetzt in ein Transformer-Modell eingespeist werden:")
    print("  → Multi-Head Self-Attention")
    print("  → Feed-Forward Netzwerk")
    print("  → Layer Normalization")
    print("  → Output-Projektion auf Vokabular")
    print("  → Softmax für Wahrscheinlichkeiten")
