"""
Komplettes LLM-System - VERBESSERTE VERSION
Mit größerem Datensatz und besserer Konfiguration

Verwendung:
    python complete_llm.py
"""

import torch
import torch.nn as nn
import torch.nn.functional as F


# ============================================================================
# TEIL 1: SUBWORD TOKENIZER
# ============================================================================

class SubwordTokenizer:
    """BPE Subword-Tokenizer"""

    def __init__(self):
        self.vocab = {}
        self.id_to_token = {}
        self.token_counts = {}
        self.merges = []
        self.next_id = 0

        # Spezial-Tokens
        self._add_token("<PAD>")
        self._add_token("<UNK>")
        self._add_token("<BOS>")
        self._add_token("<EOS>")

        # Basis-Vokabular
        for char in 'abcdefghijklmnopqrstuvwxyzäöü':
            self._add_token(char, 0)
            self._add_token(char + '</w>', 0)

        for punct in ' .,!?;:-\'"':
            self._add_token(punct, 0)
            self._add_token(punct + '</w>', 0)

        for digit in '0123456789':
            self._add_token(digit, 0)
            self._add_token(digit + '</w>', 0)

    def _add_token(self, token, count=1):
        if token not in self.vocab:
            self.vocab[token] = self.next_id
            self.id_to_token[self.next_id] = token
            self.token_counts[token] = count
            self.next_id += 1
        else:
            self.token_counts[token] += count

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
                if i < len(chars) - 1 and (chars[i], chars[i + 1]) == merge_pair:
                    chars[i] = chars[i] + chars[i + 1]
                    chars.pop(i + 1)
                else:
                    i += 1

        return chars

    def train_bpe(self, texts, num_merges=200):
        print(f"\nTrainiere BPE mit {num_merges} Merges...")

        word_freqs = {}
        for text in texts:
            words = self._split_into_words(text)
            for word in words:
                word_freqs[word] = word_freqs.get(word, 0) + 1

        print(f"Gefundene Wörter: {len(word_freqs)}")

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
            self._add_token(replacement, 0)

            if (merge_step + 1) % 50 == 0:
                print(f"  Merge {merge_step + 1}/{num_merges}")

        print(f"BPE Training abgeschlossen. Vokabular: {len(self.vocab)} Tokens")

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
# TEIL 2: PYTORCH LLM MODELL
# ============================================================================

class SimpleLLM(nn.Module):
    """Einfaches LLM mit Transformer"""

    def __init__(self, vocab_size, embedding_dim=128, hidden_dim=256, num_heads=4, num_layers=3):
        super().__init__()

        self.vocab_size = vocab_size
        self.embedding_dim = embedding_dim

        self.token_embedding = nn.Embedding(vocab_size, embedding_dim)
        self.positional_embedding = nn.Embedding(512, embedding_dim)

        decoder_layer = nn.TransformerDecoderLayer(
            d_model=embedding_dim,
            nhead=num_heads,
            dim_feedforward=hidden_dim,
            batch_first=True,
            dropout=0.1
        )
        self.transformer = nn.TransformerDecoder(decoder_layer, num_layers=num_layers)

        self.fc_out = nn.Linear(embedding_dim, vocab_size)

        print(f"\nModell initialisiert:")
        print(f"  Vokabulargröße: {vocab_size}")
        print(f"  Embedding-Dimension: {embedding_dim}")
        print(f"  Anzahl Parameter: {sum(p.numel() for p in self.parameters()):,}")

    def forward(self, x, mask=None):
        batch_size, seq_len = x.shape

        token_emb = self.token_embedding(x)
        positions = torch.arange(0, seq_len, device=x.device).unsqueeze(0)
        pos_emb = self.positional_embedding(positions)

        x = token_emb + pos_emb
        x = self.transformer(x, x, tgt_mask=mask)
        logits = self.fc_out(x)

        return logits

    def generate_causal_mask(self, size):
        mask = torch.triu(torch.ones(size, size), diagonal=1).bool()
        return mask


# ============================================================================
# TEIL 3: TRAINER
# ============================================================================

class LLMTrainer:
    """Trainer für das LLM"""

    def __init__(self, model, tokenizer, learning_rate=0.003):
        self.model = model
        self.tokenizer = tokenizer
        self.optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
        self.criterion = nn.CrossEntropyLoss()

    def train_on_texts(self, texts, epochs=500, context_window=6):
        print(f"\n{'='*60}")
        print(f"TRAINING STARTET")
        print(f"{'='*60}")

        # Sammle Trainingspaare
        all_pairs = []
        for text in texts:
            token_ids = self.tokenizer.tokenize(text)

            # Mehr Trainingspaare durch verschiedene Fenstergrößen
            for win_size in range(2, min(context_window + 1, len(token_ids))):
                for i in range(len(token_ids) - win_size):
                    context = token_ids[i:i + win_size]
                    target = token_ids[i + 1:i + win_size + 1]
                    all_pairs.append((context, target))

        print(f"Trainingspaare: {len(all_pairs)}")
        print(f"Epochen: {epochs}")

        self.model.train()

        for epoch in range(epochs):
            total_loss = 0

            for context, target in all_pairs:
                context_tensor = torch.tensor([context], dtype=torch.long)
                target_tensor = torch.tensor([target], dtype=torch.long)

                mask = self.model.generate_causal_mask(len(context))

                logits = self.model(context_tensor, mask=mask)

                loss = self.criterion(
                    logits.view(-1, self.model.vocab_size),
                    target_tensor.view(-1)
                )

                self.optimizer.zero_grad()
                loss.backward()

                # Gradient Clipping
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)

                self.optimizer.step()

                total_loss += loss.item()

            avg_loss = total_loss / len(all_pairs)

            if (epoch + 1) % 50 == 0 or epoch == 0:
                print(f"Epoch {epoch + 1}/{epochs} - Loss: {avg_loss:.4f}")

        print(f"{'='*60}")
        print(f"TRAINING ABGESCHLOSSEN - Finale Loss: {avg_loss:.4f}")
        print(f"{'='*60}\n")

    def generate_text(self, prompt, max_tokens=15, temperature=0.3, top_k=5):
        """Text-Generierung mit Top-K Sampling"""
        token_ids = self.tokenizer.tokenize(prompt)

        self.model.eval()

        with torch.no_grad():
            for i in range(max_tokens):
                context = torch.tensor([token_ids], dtype=torch.long)
                mask = self.model.generate_causal_mask(len(token_ids))

                logits = self.model(context, mask=mask)
                last_logits = logits[0, -1, :]

                # Temperature Scaling
                scaled_logits = last_logits / temperature

                # Top-K Filtering
                top_k_logits, top_k_indices = torch.topk(scaled_logits, top_k)
                probs = F.softmax(top_k_logits, dim=0)

                # Sample from top-k
                next_idx = torch.multinomial(probs, num_samples=1).item()
                next_token = top_k_indices[next_idx].item()

                token_ids.append(next_token)

        return self.tokenizer.detokenize(token_ids)

    def generate_greedy(self, prompt, max_tokens=15):
        """Greedy Decoding - immer bestes Token"""
        token_ids = self.tokenizer.tokenize(prompt)

        self.model.eval()

        with torch.no_grad():
            for i in range(max_tokens):
                context = torch.tensor([token_ids], dtype=torch.long)
                mask = self.model.generate_causal_mask(len(token_ids))

                logits = self.model(context, mask=mask)
                next_token = logits[0, -1, :].argmax().item()

                token_ids.append(next_token)

        return self.tokenizer.detokenize(token_ids)


# ============================================================================
# TEIL 4: GRÖßERER DATENSATZ
# ============================================================================

def get_training_data():
    """Gibt einen größeren Trainings-Datensatz zurück"""
    return [
        # Hunde - viele Variationen
        "der hund bellt laut",
        "der hund bellt sehr laut",
        "der kleine hund bellt",
        "der große hund bellt laut",
        "der hund bellt im garten",
        "der hund bellt im park",

        "der hund rennt schnell",
        "der hund rennt sehr schnell",
        "der kleine hund rennt",
        "der hund rennt im garten",
        "der hund rennt im park",
        "der hund rennt im wald",

        "der hund spielt ball",
        "der hund spielt gerne",
        "der hund spielt im garten",
        "der hund spielt im park",
        "der kleine hund spielt",
        "der hund spielt mit dem ball",

        "der hund schläft tief",
        "der hund schläft im haus",
        "der müde hund schläft",
        "der hund schläft gerne",

        "der hund ist braun",
        "der hund ist groß",
        "der hund ist klein",
        "der hund ist süß",

        # Katzen - viele Variationen
        "die katze schläft",
        "die katze schläft tief",
        "die katze schläft im haus",
        "die kleine katze schläft",
        "die müde katze schläft",
        "die katze schläft gerne",

        "die katze jagt mäuse",
        "die katze jagt im garten",
        "die schnelle katze jagt",
        "die katze jagt gerne",

        "die katze spielt",
        "die katze spielt ball",
        "die katze spielt gerne",
        "die katze spielt im haus",

        "die katze rennt schnell",
        "die katze rennt im garten",
        "die kleine katze rennt",

        "die katze ist schwarz",
        "die katze ist klein",
        "die katze ist süß",

        # Orte
        "im garten wachsen blumen",
        "im garten spielen kinder",
        "im garten ist es schön",
        "der garten ist groß",
        "der garten ist grün",
        "im schönen garten wachsen blumen",

        "im park spielen kinder",
        "im park ist es schön",
        "der park ist groß",
        "der park ist grün",
        "im großen park spielen kinder",

        "im wald leben tiere",
        "im wald ist es dunkel",
        "der wald ist groß",
        "im großen wald leben tiere",

        "im haus ist es warm",
        "das haus ist groß",
        "das schöne haus ist groß",

        # Wetter
        "das wetter ist schön",
        "das wetter ist gut",
        "das wetter ist heute schön",
        "heute ist das wetter schön",

        "der tag ist sonnig",
        "der tag ist schön",
        "heute ist ein schöner tag",
        "ein schöner tag heute",

        "die sonne scheint hell",
        "die sonne scheint heute",
        "die sonne ist warm",

        "es regnet heute",
        "es regnet stark",
        "heute regnet es",

        "der himmel ist blau",
        "der himmel ist klar",
        "der schöne himmel ist blau",

        # Allgemein
        "die welt ist schön",
        "die welt ist groß",
        "die schöne welt ist groß",

        "das leben ist gut",
        "das leben ist schön",
        "das schöne leben ist gut",

        "ich bin glücklich",
        "ich bin sehr glücklich",
        "heute bin ich glücklich",

        "alles ist gut",
        "alles ist schön",
        "alles ist wunderbar",
        "heute ist alles gut",
    ]


# ============================================================================
# TEIL 5: HAUPTPROGRAMM
# ============================================================================

def main():
    print("="*60)
    print("KOMPLETTES LLM-SYSTEM - VERBESSERTE VERSION")
    print("="*60)

    # Training-Daten
    training_texts = get_training_data()
    print(f"\nAnzahl Training-Texte: {len(training_texts)}")

    # Tokenizer trainieren
    print("\n--- Tokenizer Training ---")
    tokenizer = SubwordTokenizer()
    tokenizer.train_bpe(training_texts, num_merges=300)

    vocab_size = tokenizer.get_vocab_size()
    print(f"\nFinale Vokabulargröße: {vocab_size}")

    # Test
    test = "der hund spielt im garten"
    tokens = tokenizer.tokenize(test)
    print(f"\nTest: '{test}'")
    print(f"Tokens: {tokenizer.detokenize(tokens)}")

    # Modell erstellen
    print("\n--- Modell erstellen ---")
    model = SimpleLLM(
        vocab_size=vocab_size,
        embedding_dim=128,
        hidden_dim=256,
        num_heads=4,
        num_layers=3
    )

    # Training
    print("\n--- Training ---")
    trainer = LLMTrainer(model, tokenizer, learning_rate=0.003)
    trainer.train_on_texts(training_texts, epochs=500, context_window=6)

    # Tests
    print("\n" + "="*60)
    print("TEXT-GENERIERUNG - TESTS")
    print("="*60)

    test_prompts = [
        "der hund",
        "die katze",
        "im garten",
        "das wetter",
        "heute ist"
    ]

    for prompt in test_prompts:
        print(f"\n--- Prompt: '{prompt}' ---")

        # Greedy (sehr stabil)
        greedy = trainer.generate_greedy(prompt, max_tokens=8)
        print(f"Greedy:  {greedy}")

        # Low temperature (konservativ)
        low_temp = trainer.generate_text(prompt, max_tokens=8, temperature=0.2, top_k=3)
        print(f"Temp 0.2: {low_temp}")

    # Interaktiver Modus
    print("\n" + "="*60)
    print("INTERAKTIVER MODUS")
    print("="*60)
    print("Gib einen Prompt ein (oder 'exit')")

    while True:
        prompt = input("\nPrompt: ").strip()

        if prompt.lower() in ['exit', 'quit', 'q']:
            print("Auf Wiedersehen!")
            break

        if not prompt:
            continue

        try:
            greedy = trainer.generate_greedy(prompt, max_tokens=10)
            print(f"→ {greedy}")
        except Exception as e:
            print(f"Fehler: {e}")


if __name__ == "__main__":
    main()
