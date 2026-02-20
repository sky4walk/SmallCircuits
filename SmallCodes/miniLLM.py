"""
Interaktives Mini-LLM mit PyTorch
Kombiniert unseren Tokenizer mit einem einfachen Transformer für Text-Generierung
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
#from TokenizerExampleA import SubwordTokenizer

# PIP vorbereiten
# sudo apt update
# sudo apt install python3-pip python3-venv -y
# Umgebungsvariable setzen
# python3 -m venv pytorch_env
# source pytorch_env/bin/activate
# pyTorch installieren
# pip install torch torchvision torchaudio

class SimpleLLM(nn.Module):
    """
    Ein einfaches LLM mit Transformer-Architektur
    """

    def __init__(self, vocab_size, embedding_dim=128, hidden_dim=256, num_heads=4, num_layers=2):
        super().__init__()

        self.vocab_size = vocab_size
        self.embedding_dim = embedding_dim

        # Token Embedding
        self.token_embedding = nn.Embedding(vocab_size, embedding_dim)

        # Positional Encoding (lernbar)
        self.positional_embedding = nn.Embedding(512, embedding_dim)

        # Transformer Decoder Layers
        decoder_layer = nn.TransformerDecoderLayer(
            d_model=embedding_dim,
            nhead=num_heads,
            dim_feedforward=hidden_dim,
            batch_first=True
        )
        self.transformer = nn.TransformerDecoder(decoder_layer, num_layers=num_layers)

        # Output Layer
        self.fc_out = nn.Linear(embedding_dim, vocab_size)

        print(f"Modell initialisiert:")
        print(f"  Vokabulargröße: {vocab_size}")
        print(f"  Embedding-Dimension: {embedding_dim}")
        print(f"  Anzahl Parameter: {sum(p.numel() for p in self.parameters()):,}")

    def forward(self, x, mask=None):
        """
        Forward pass

        Args:
            x: Token-IDs [batch_size, sequence_length]
            mask: Causal mask [sequence_length, sequence_length]
        """
        batch_size, seq_len = x.shape

        # Token Embeddings
        token_emb = self.token_embedding(x)  # [batch, seq_len, emb_dim]

        # Positional Embeddings
        positions = torch.arange(0, seq_len, device=x.device).unsqueeze(0)
        pos_emb = self.positional_embedding(positions)  # [1, seq_len, emb_dim]

        # Kombiniere Token + Position
        x = token_emb + pos_emb

        # Transformer (verwendet sich selbst als Memory)
        x = self.transformer(x, x, tgt_mask=mask)

        # Output Projektion
        logits = self.fc_out(x)  # [batch, seq_len, vocab_size]

        return logits

    def generate_causal_mask(self, size):
        """
        Erstellt eine Causal Attention Mask
        """
        mask = torch.triu(torch.ones(size, size), diagonal=1).bool()
        return mask


class LLMTrainer:
    """
    Trainer für das Mini-LLM
    """

    def __init__(self, model, tokenizer, learning_rate=0.001):
        self.model = model
        self.tokenizer = tokenizer
        self.optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
        self.criterion = nn.CrossEntropyLoss()

    def train_on_texts(self, texts, epochs=10, context_window=10):
        """
        Trainiert das Modell auf einer Liste von Texten
        """
        print(f"\n{'='*60}")
        print(f"TRAINING STARTET")
        print(f"{'='*60}")
        print(f"Anzahl Texte: {len(texts)}")
        print(f"Epochen: {epochs}")
        print(f"Kontextfenster: {context_window}")

        # Sammle alle Trainingspaare
        all_pairs = []
        for text in texts:
            token_ids = self.tokenizer.tokenize(text)

            # Erstelle Trainingspaare
            for i in range(len(token_ids) - context_window):
                context = token_ids[i:i + context_window]
                target = token_ids[i + 1:i + context_window + 1]
                all_pairs.append((context, target))

        print(f"Trainingspaare erstellt: {len(all_pairs)}")

        # Training Loop
        for epoch in range(epochs):
            total_loss = 0

            for context, target in all_pairs:
                # Zu Tensors konvertieren
                context_tensor = torch.tensor([context], dtype=torch.long)
                target_tensor = torch.tensor([target], dtype=torch.long)

                # Causal Mask
                mask = self.model.generate_causal_mask(len(context))

                # Forward pass
                logits = self.model(context_tensor, mask=mask)

                # Loss berechnen
                loss = self.criterion(
                    logits.view(-1, self.model.vocab_size),
                    target_tensor.view(-1)
                )

                # Backward pass
                self.optimizer.zero_grad()
                loss.backward()
                self.optimizer.step()

                total_loss += loss.item()

            avg_loss = total_loss / len(all_pairs)
            if (epoch + 1) % 2 == 0 or epoch == 0:
                print(f"Epoch {epoch + 1}/{epochs} - Loss: {avg_loss:.4f}")

        print(f"{'='*60}")
        print(f"TRAINING ABGESCHLOSSEN")
        print(f"{'='*60}\n")

    def generate_text(self, prompt, max_tokens=20, temperature=1.0):
        """
        Generiert Text basierend auf einem Prompt

        Args:
            prompt: Start-Text
            max_tokens: Maximale Anzahl zu generierender Tokens
            temperature: Höher = kreativer, Niedriger = deterministischer
        """
        print(f"\n{'='*60}")
        print(f"TEXT-GENERIERUNG")
        print(f"{'='*60}")
        print(f"Prompt: '{prompt}'")
        print(f"Max Tokens: {max_tokens}")
        print(f"Temperature: {temperature}")
        print(f"{'='*60}\n")

        # Tokenisiere Prompt
        token_ids = self.tokenizer.tokenize(prompt)

        self.model.eval()  # Evaluation mode

        with torch.no_grad():
            for i in range(max_tokens):
                # Aktueller Kontext
                context = torch.tensor([token_ids], dtype=torch.long)

                # Causal Mask
                mask = self.model.generate_causal_mask(len(token_ids))

                # Forward pass
                logits = self.model(context, mask=mask)

                # Nur das letzte Token interessiert uns
                last_logits = logits[0, -1, :]  # [vocab_size]

                # Temperature Scaling
                scaled_logits = last_logits / temperature

                # Softmax für Wahrscheinlichkeiten
                probs = F.softmax(scaled_logits, dim=0)

                # Sample nächstes Token
                next_token = torch.multinomial(probs, num_samples=1).item()

                # Füge zum Kontext hinzu
                token_ids.append(next_token)

                # Zeige Fortschritt
                current_text = self.tokenizer.detokenize(token_ids)
                print(f"Step {i+1}: {current_text}")

                # Stoppe bei End-Token (wenn vorhanden)
                if next_token == self.tokenizer.vocab.get('<EOS>', -1):
                    break

        # Finale Ausgabe
        final_text = self.tokenizer.detokenize(token_ids)
        print(f"\n{'='*60}")
        print(f"GENERIERTER TEXT:")
        print(f"{'='*60}")
        print(final_text)
        print(f"{'='*60}\n")

        return final_text


# ============================================================================
# HAUPTPROGRAMM - INTERAKTIVE DEMO
# ============================================================================

def main():
    print("="*60)
    print("MINI-LLM INTERAKTIVE DEMO")
    print("="*60)

    print("\nHINWEIS: Für echte Verwendung benötigst du:")
    print("1. Den SubwordTokenizer aus dem vorherigen Code")
    print("2. Training auf echten Texten")
    print("\nBeispiel-Code für echte Verwendung:\n")


# 1. Tokenizer trainieren
from TokenizerExampleA import SubwordTokenizer

tokenizer = SubwordTokenizer()

training_texts = [
    "Der Hund bellt laut",
    "Die Katze schläft",
    "Der Hund spielt im Garten",
    "Die Katze jagt eine Maus",
    "Ein schöner Tag heute",
    "Das Wetter ist gut"
]

tokenizer.train_bpe(training_texts, num_merges=20)

# 2. Modell erstellen
vocab_size = tokenizer.get_vocab_size()
model = SimpleLLM(
    vocab_size=vocab_size,
    embedding_dim=128,
    hidden_dim=256,
    num_heads=4,
    num_layers=2
)

# 3. Training
trainer = LLMTrainer(model, tokenizer, learning_rate=0.001)
trainer.train_on_texts(training_texts, epochs=500, context_window=8)

# 4. Interaktive Text-Generierung
while True:
    prompt = input("\\nGib einen Prompt ein (oder 'exit' zum Beenden): ")

    if prompt.lower() == 'exit':
        break

    # Generiere mit verschiedenen Temperaturen
    print("\\n--- Temperature 0.5 (konservativ) ---")
    trainer.generate_text(prompt, max_tokens=15, temperature=0.5)

    print("\\n--- Temperature 1.0 (balanced) ---")
    trainer.generate_text(prompt, max_tokens=15, temperature=1.0)

    print("\\n--- Temperature 1.5 (kreativ) ---")
    trainer.generate_text(prompt, max_tokens=15, temperature=1.5)

    print("\n" + "="*60)
    print("FEATURES DES INTERAKTIVEN LLMs:")
    print("="*60)
    print("""

PARAMETER-ERKLÄRUNG:

• embedding_dim: Größe der Token-Vektoren (128-768)
• hidden_dim: Größe der Feed-Forward-Layer (256-2048)
• num_heads: Anzahl Attention-Heads (4-16)
• num_layers: Tiefe des Transformers (2-12)
• temperature:
  - 0.5 = sehr vorhersagbar
  - 1.0 = ausgeglichen
  - 1.5+ = sehr kreativ/zufällig
""")


if __name__ == "__main__":
    main()
