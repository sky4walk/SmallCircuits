# -----------------------------
# Eigene Datenstrukturen
# -----------------------------

class MyCounter:
    def __init__(self):
        self.data = {}

    def increment(self, key, value=1):
        if key not in self.data:
            self.data[key] = 0
        self.data[key] += value

    def items(self):
        return self.data.items()

    def __getitem__(self, key):
        return self.data.get(key, 0)

    def __setitem__(self, key, value):
        self.data[key] = value

    def __repr__(self):
        return f"MyCounter({self.data})"


class MyDefaultDict:
    def __init__(self, default_factory):
        self.default_factory = default_factory
        self.data = {}

    def __getitem__(self, key):
        if key not in self.data:
            self.data[key] = self.default_factory()
        return self.data[key]

    def __setitem__(self, key, value):
        self.data[key] = value

    def items(self):
        return self.data.items()

    def __repr__(self):
        return f"MyDefaultDict({self.data})"

class ByteLevelBPE:
    def __init__(self, num_merges=10, verbose=True):
        self.num_merges = num_merges
        self.verbose = verbose
        self.vocab = MyCounter()
        self.merges = []

    # -----------------------------
    # Text ↔ Byte-Symbole
    # -----------------------------
    def text_to_symbols(self, text):
        symbols = [str(b) for b in text.encode("utf-8")] + ["</w>"]
        if self.verbose:
            print(f"Text -> Symbols for '{text}': {symbols}")
        return symbols

    def symbols_to_text(self, symbols):
        bytes_list = [int(s) for s in symbols if s != "</w>"]
        return bytes(bytes_list).decode("utf-8", errors="replace")

    # -----------------------------
    # Training
    # -----------------------------
    def fit(self, texts):
        print("\n=== TRAINING START ===")

        # 1️⃣ Initiales Vokabular
        for text in texts:
            key = " ".join(self.text_to_symbols(text))
            self.vocab.increment(key)

        if self.verbose:
            print("\nInitial Vocab:")
            for k, v in self.vocab.items():
                print(f"{k} : {v}")

        # 2️⃣ Merges lernen
        for step in range(self.num_merges):
            print(f"\n--- Merge Step {step+1} ---")
            pair_counts = self.count_pairs()
            if not pair_counts.data:
                print("Keine Paare mehr vorhanden.")
                break

            # Häufigstes Paar finden
            best_pair = max(pair_counts.items(), key=lambda x: x[1])[0]
            print("Best pair:", best_pair)
            self.merges.append(best_pair)
            self.apply_merge(best_pair)

        print("\n=== TRAINING ENDE ===")

    # -----------------------------
    # Alle Paare zählen
    # -----------------------------
    def count_pairs(self):
        pairs = MyDefaultDict(int)
        for word, freq in self.vocab.items():
            symbols = word.split()
            for i in range(len(symbols)-1):
                pair = (symbols[i], symbols[i+1])
                pairs[pair] += freq
        if self.verbose:
            print("\nPair Counts:")
            for p, c in pairs.items():
                print(p, ":", c)
        return pairs

    # -----------------------------
    # Merge anwenden
    # -----------------------------
    def apply_merge(self, pair):
        print("Applying merge:", pair)
        new_vocab = MyCounter()
        for word, freq in self.vocab.items():
            symbols = word.split()
            new_symbols = []
            i = 0
            while i < len(symbols):
                if i < len(symbols)-1 and (symbols[i], symbols[i+1]) == pair:
                    new_symbols.append(symbols[i] + "_" + symbols[i+1])
                    i += 2
                else:
                    new_symbols.append(symbols[i])
                    i += 1
            new_word = " ".join(new_symbols)
            new_vocab.increment(new_word, freq)
            if self.verbose:
                print("Old:", word)
                print("New:", new_word)
        self.vocab = new_vocab

    # -----------------------------
    # Tokenisierung
    # -----------------------------
    def encode(self, text):
        print(f"\n=== TOKENISIERUNG: '{text}' ===")
        tokens = self.text_to_symbols(text)
        for merge in self.merges:
            print("\nApply merge:", merge)
            i = 0
            while i < len(tokens)-1:
                if (tokens[i], tokens[i+1]) == merge:
                    tokens[i:i+2] = [tokens[i] + "_" + tokens[i+1]]
                else:
                    i += 1
            if self.verbose:
                print("Tokens now:", tokens)
        return tokens

    # -----------------------------
    # Dekodierung
    # -----------------------------
    def decode(self, tokens):
        flat = []
        for tok in tokens:
            flat.extend(tok.split("_"))
        text = self.symbols_to_text(flat)
        print("\nDecoded:", text)
        return text

texts = ["low", "lower", "lowest", "hello"]

bpe = ByteLevelBPE(num_merges=5, verbose=True)
bpe.fit(texts)

new_word = "lowest"
tokens = bpe.encode(new_word)
bpe.decode(tokens)
