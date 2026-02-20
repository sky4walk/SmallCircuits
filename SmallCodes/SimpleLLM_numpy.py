"""
Komplettes LLM-System - NUR MIT NUMPY
Training, Backpropagation, Text-Generierung - alles selbst implementiert

Verwendung:
    python complete_llm_numpy.py
"""

import numpy as np
import pickle


# ============================================================================
# HILFSFUNKTIONEN
# ============================================================================

def softmax(x):
    """Numerisch stabile Softmax"""
    exp_x = np.exp(x - np.max(x, axis=-1, keepdims=True))
    return exp_x / np.sum(exp_x, axis=-1, keepdims=True)


def relu(x):
    """ReLU Aktivierung"""
    return np.maximum(0, x)


def relu_derivative(x):
    """ReLU Ableitung"""
    return (x > 0).astype(float)


# ============================================================================
# TEIL 1: SUBWORD TOKENIZER
# ============================================================================

class SubwordTokenizer:
    """BPE Subword-Tokenizer"""

    def __init__(self):
        self.vocab = {}
        self.id_to_token = {}
        self.merges = []
        self.next_id = 0

        # Spezial-Tokens
        self._add_token("<PAD>")
        self._add_token("<UNK>")

        # Basis-Vokabular
        for char in 'abcdefghijklmnopqrstuvwxyzäöü':
            self._add_token(char)
            self._add_token(char + '</w>')

        for punct in ' .,!?;:-\'"':
            self._add_token(punct)
            self._add_token(punct + '</w>')

    def _add_token(self, token):
        if token not in self.vocab:
            self.vocab[token] = self.next_id
            self.id_to_token[self.next_id] = token
            self.next_id += 1

    def _split_into_words(self, text):
        words = []
        current_word = ""

        for char in text.lower():
            if char.isalnum() or char in 'äöü':
                current_word += char
            else:
                if current_word:
                    words.append(current_word)
                    current_word = ""
                if not char.isspace():
                    words.append(char)

        if current_word:
            words.append(current_word)

        return words

    def _get_word_characters(self, word):
        chars = list(word)
        if chars:
            chars[-1] = chars[-1] + '</w>'
        return chars

    def _get_pairs(self, chars):
        pairs = set()
        for i in range(len(chars) - 1):
            pairs.add((chars[i], chars[i + 1]))
        return pairs

    def _apply_bpe(self, word):
        chars = self._get_word_characters(word)

        for merge_pair in self.merges:
            i = 0
            while i < len(chars) - 1:
                if (chars[i], chars[i + 1]) == merge_pair:
                    chars[i] = chars[i] + chars[i + 1]
                    chars.pop(i + 1)
                else:
                    i += 1

        return chars

    def train_bpe(self, texts, num_merges=150):
        print(f"Trainiere BPE mit {num_merges} Merges...")

        word_freqs = {}
        for text in texts:
            words = self._split_into_words(text)
            for word in words:
                word_freqs[word] = word_freqs.get(word, 0) + 1

        vocab = {}
        for word, freq in word_freqs.items():
            chars = self._get_word_characters(word)
            vocab[' '.join(chars)] = freq

        for merge_step in range(num_merges):
            pairs_count = {}
            for word, freq in vocab.items():
                chars = word.split()
                for pair in self._get_pairs(chars):
                    pairs_count[pair] = pairs_count.get(pair, 0) + freq

            if not pairs_count:
                break

            best_pair = max(pairs_count, key=pairs_count.get)
            self.merges.append(best_pair)

            new_vocab = {}
            search_pattern = ' '.join(best_pair)
            replacement = ''.join(best_pair)

            for word, freq in vocab.items():
                new_word = word.replace(search_pattern, replacement)
                new_vocab[new_word] = freq

            vocab = new_vocab
            self._add_token(replacement)

        print(f"BPE Training fertig. Vokabular: {len(self.vocab)} Tokens")

    def tokenize(self, text):
        words = self._split_into_words(text)
        all_tokens = []

        for word in words:
            subwords = self._apply_bpe(word)
            all_tokens.extend(subwords)

        token_ids = []
        for token in all_tokens:
            token_ids.append(self.vocab.get(token, self.vocab["<UNK>"]))

        return token_ids

    def detokenize(self, token_ids):
        tokens = []
        for token_id in token_ids:
            tokens.append(self.id_to_token.get(token_id, "<UNK>"))

        text = ''.join(tokens).replace('</w>', ' ').strip()
        return text

    def get_vocab_size(self):
        return len(self.vocab)


# ============================================================================
# TEIL 2: EINFACHES NEURALES NETZ (KEIN TRANSFORMER)
# ============================================================================

class SimpleNeuralLM:
    """
    Einfaches Neural Language Model mit NumPy
    Verwendet Feed-Forward Netzwerk statt Transformer
    (Transformer mit Backprop in NumPy wäre sehr komplex)
    """

    def __init__(self, vocab_size, embedding_dim=64, hidden_dim=128, context_size=4):
        self.vocab_size = vocab_size
        self.embedding_dim = embedding_dim
        self.hidden_dim = hidden_dim
        self.context_size = context_size

        # Parameter initialisieren
        self.params = {}

        # Embedding Matrix
        self.params['embed'] = np.random.randn(vocab_size, embedding_dim) * 0.01

        # Hidden Layer
        input_size = embedding_dim * context_size
        self.params['W1'] = np.random.randn(input_size, hidden_dim) * np.sqrt(2.0 / input_size)
        self.params['b1'] = np.zeros(hidden_dim)

        # Output Layer
        self.params['W2'] = np.random.randn(hidden_dim, vocab_size) * np.sqrt(2.0 / hidden_dim)
        self.params['b2'] = np.zeros(vocab_size)

        # Für Adam Optimizer
        self.m = {k: np.zeros_like(v) for k, v in self.params.items()}
        self.v = {k: np.zeros_like(v) for k, v in self.params.items()}
        self.t = 0

        print(f"\nModell initialisiert:")
        print(f"  Vokabular: {vocab_size}")
        print(f"  Embedding: {embedding_dim}")
        print(f"  Hidden: {hidden_dim}")
        print(f"  Context: {context_size}")

        total_params = sum(p.size for p in self.params.values())
        print(f"  Parameter: {total_params:,}")

    def forward(self, context_ids):
        """
        Forward Pass

        Args:
            context_ids: Array von Token-IDs [context_size]

        Returns:
            logits, cache
        """
        cache = {}

        # 1. Embedding Lookup
        embeddings = self.params['embed'][context_ids]  # [context_size, embedding_dim]
        cache['embeddings'] = embeddings
        cache['context_ids'] = context_ids

        # 2. Flatten
        x = embeddings.flatten()  # [context_size * embedding_dim]
        cache['x'] = x

        # 3. Hidden Layer
        z1 = x @ self.params['W1'] + self.params['b1']
        cache['z1'] = z1

        h1 = relu(z1)
        cache['h1'] = h1

        # 4. Output Layer
        logits = h1 @ self.params['W2'] + self.params['b2']
        cache['logits'] = logits

        return logits, cache

    def backward(self, cache, target_id, learning_rate=0.01):
        """
        Backward Pass mit Adam Optimizer

        Args:
            cache: Forward pass cache
            target_id: Ziel Token-ID
            learning_rate: Lernrate

        Returns:
            loss
        """
        # Softmax und Loss
        logits = cache['logits']
        probs = softmax(logits)

        # Cross-Entropy Loss
        loss = -np.log(probs[target_id] + 1e-10)

        # Gradienten
        grads = {}

        # Output Layer
        dlogits = probs.copy()
        dlogits[target_id] -= 1  # Softmax + Cross-Entropy Gradient

        grads['W2'] = np.outer(cache['h1'], dlogits)
        grads['b2'] = dlogits

        # Hidden Layer
        dh1 = dlogits @ self.params['W2'].T
        dz1 = dh1 * relu_derivative(cache['z1'])

        grads['W1'] = np.outer(cache['x'], dz1)
        grads['b1'] = dz1

        # Embedding Layer
        dx = dz1 @ self.params['W1'].T
        dx_reshaped = dx.reshape(self.context_size, self.embedding_dim)

        grads['embed'] = np.zeros_like(self.params['embed'])
        for i, token_id in enumerate(cache['context_ids']):
            grads['embed'][token_id] += dx_reshaped[i]

        # Adam Optimizer Update
        self.t += 1
        beta1, beta2 = 0.9, 0.999
        eps = 1e-8

        for key in self.params:
            # Update moving averages
            self.m[key] = beta1 * self.m[key] + (1 - beta1) * grads[key]
            self.v[key] = beta2 * self.v[key] + (1 - beta2) * (grads[key] ** 2)

            # Bias correction
            m_hat = self.m[key] / (1 - beta1 ** self.t)
            v_hat = self.v[key] / (1 - beta2 ** self.t)

            # Update parameters
            self.params[key] -= learning_rate * m_hat / (np.sqrt(v_hat) + eps)

        return loss

    def predict(self, context_ids):
        """Vorhersage für nächstes Token"""
        logits, _ = self.forward(context_ids)
        probs = softmax(logits)
        return probs

    def save(self, filepath):
        """Speichere Modell"""
        with open(filepath, 'wb') as f:
            pickle.dump(self.params, f)
        print(f"Modell gespeichert: {filepath}")

    def load(self, filepath):
        """Lade Modell"""
        with open(filepath, 'rb') as f:
            self.params = pickle.load(f)
        print(f"Modell geladen: {filepath}")


# ============================================================================
# TEIL 3: TRAINER
# ============================================================================

class NumpyLMTrainer:
    """Trainer für das NumPy Language Model"""

    def __init__(self, model, tokenizer):
        self.model = model
        self.tokenizer = tokenizer

    def train(self, texts, epochs=100, learning_rate=0.01):
        print(f"\n{'='*60}")
        print(f"TRAINING STARTET")
        print(f"{'='*60}")

        # Erstelle Trainingspaare
        training_pairs = []

        for text in texts:
            token_ids = self.tokenizer.tokenize(text)

            # Erstelle Context → Target Paare
            for i in range(len(token_ids) - self.model.context_size):
                context = token_ids[i:i + self.model.context_size]
                target = token_ids[i + self.model.context_size]
                training_pairs.append((np.array(context), target))

        print(f"Trainingspaare: {len(training_pairs)}")
        print(f"Epochen: {epochs}")
        print(f"Lernrate: {learning_rate}")

        # Training Loop
        for epoch in range(epochs):
            total_loss = 0

            # Shuffle
            np.random.shuffle(training_pairs)

            for context, target in training_pairs:
                # Forward
                logits, cache = self.model.forward(context)

                # Backward
                loss = self.model.backward(cache, target, learning_rate)

                total_loss += loss

            avg_loss = total_loss / len(training_pairs)

            if (epoch + 1) % 10 == 0 or epoch == 0:
                print(f"Epoch {epoch + 1}/{epochs} - Loss: {avg_loss:.4f}")

        print(f"{'='*60}")
        print(f"TRAINING ABGESCHLOSSEN")
        print(f"{'='*60}\n")

    def generate_text(self, prompt, max_tokens=15, temperature=0.5):
        """Text-Generierung"""
        token_ids = self.tokenizer.tokenize(prompt)

        # Stelle sicher, dass wir genug Context haben
        if len(token_ids) < self.model.context_size:
            # Padding mit <PAD>
            pad_id = self.tokenizer.vocab.get("<PAD>", 0)
            token_ids = [pad_id] * (self.model.context_size - len(token_ids)) + token_ids

        for i in range(max_tokens):
            # Nimm letzten Context
            context = np.array(token_ids[-self.model.context_size:])

            # Vorhersage
            probs = self.model.predict(context)

            # Temperature Scaling
            if temperature != 1.0:
                logits = np.log(probs + 1e-10)
                logits = logits / temperature
                probs = softmax(logits)

            # Sample
            next_token = np.random.choice(len(probs), p=probs)
            token_ids.append(next_token)

        return self.tokenizer.detokenize(token_ids)

    def generate_greedy(self, prompt, max_tokens=15):
        """Greedy Decoding"""
        token_ids = self.tokenizer.tokenize(prompt)

        if len(token_ids) < self.model.context_size:
            pad_id = self.tokenizer.vocab.get("<PAD>", 0)
            token_ids = [pad_id] * (self.model.context_size - len(token_ids)) + token_ids

        for i in range(max_tokens):
            context = np.array(token_ids[-self.model.context_size:])
            probs = self.model.predict(context)
            next_token = np.argmax(probs)
            token_ids.append(next_token)

        return self.tokenizer.detokenize(token_ids)


# ============================================================================
# TEIL 4: TRAINING-DATEN
# ============================================================================

def get_training_data():
    """Trainings-Datensatz"""
    return [
        # Einfache, sich wiederholende Muster
        "der hund bellt",
        "der hund bellt laut",
        "der hund rennt",
        "der hund rennt schnell",
        "der hund spielt",
        "der hund schläft",

        "die katze schläft",
        "die katze jagt",
        "die katze rennt",
        "die katze spielt",

        "im garten spielen",
        "im park spielen",
        "im wald leben",

        "das wetter ist schön",
        "das wetter ist gut",
        "der tag ist schön",

        # Mehr Variationen
        "der kleine hund bellt",
        "der große hund rennt",
        "die kleine katze schläft",

        "im großen garten spielen",
        "im schönen park spielen",

        "heute ist schön",
        "heute ist gut",

        # Kombinationen
        "der hund bellt im garten",
        "die katze schläft im haus",
        "im park ist es schön",
    ]


# ============================================================================
# TEIL 5: HAUPTPROGRAMM
# ============================================================================

def main():
    print("="*60)
    print("KOMPLETTES LLM - NUR MIT NUMPY")
    print("="*60)
    print("\nHINWEIS: Dies ist ein einfaches Feed-Forward Netzwerk,")
    print("kein Transformer. Transformer mit Backprop in NumPy wäre")
    print("sehr komplex. Aber das Prinzip ist das Gleiche!\n")

    # Seed für Reproduzierbarkeit
    np.random.seed(42)

    # Training-Daten
    training_texts = get_training_data()
    print(f"Training-Texte: {len(training_texts)}")

    # Tokenizer
    print("\n--- Tokenizer Training ---")
    tokenizer = SubwordTokenizer()
    tokenizer.train_bpe(training_texts, num_merges=100)

    vocab_size = tokenizer.get_vocab_size()

    # Test
    test = "der hund bellt"
    tokens = tokenizer.tokenize(test)
    print(f"\nTest: '{test}'")
    print(f"Detokenized: '{tokenizer.detokenize(tokens)}'")

    # Modell
    print("\n--- Modell erstellen ---")
    model = SimpleNeuralLM(
        vocab_size=vocab_size,
        embedding_dim=32,
        hidden_dim=64,
        context_size=3
    )

    # Training
    print("\n--- Training ---")
    trainer = NumpyLMTrainer(model, tokenizer)
    trainer.train(training_texts, epochs=100, learning_rate=0.01)

    # Tests
    print("\n" + "="*60)
    print("TEXT-GENERIERUNG")
    print("="*60)

    test_prompts = [
        "der hund",
        "die katze",
        "im garten",
        "das wetter"
    ]

    for prompt in test_prompts:
        print(f"\n--- '{prompt}' ---")
        greedy = trainer.generate_greedy(prompt, max_tokens=6)
        print(f"Greedy: {greedy}")

        sampled = trainer.generate_text(prompt, max_tokens=6, temperature=0.3)
        print(f"Sample: {sampled}")

    # Interaktiv
    print("\n" + "="*60)
    print("INTERAKTIVER MODUS")
    print("="*60)

    while True:
        prompt = input("\nPrompt (oder 'exit'): ").strip()

        if prompt.lower() in ['exit', 'quit', 'q']:
            print("Tschüss!")
            break

        if not prompt:
            continue

        try:
            result = trainer.generate_greedy(prompt, max_tokens=8)
            print(f"→ {result}")
        except Exception as e:
            print(f"Fehler: {e}")


if __name__ == "__main__":
    main()
