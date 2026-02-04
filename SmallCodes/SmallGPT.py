"""
SmallGPT - Ein minimaler GPT-Transformer implementiert nur mit NumPy
Inspiriert von Andrej Karpathy's picoGPT und nanoGPT

Zeigt die Grundprinzipien eines Transformers ohne Framework-Magie
"""

import numpy as np


def softmax(x):
    """Numerisch stabile Softmax-Funktion"""
    exp_x = np.exp(x - np.max(x, axis=-1, keepdims=True))
    return exp_x / np.sum(exp_x, axis=-1, keepdims=True)


def gelu(x):
    """GELU Aktivierungsfunktion (Gaussian Error Linear Unit)"""
    return 0.5 * x * (1 + np.tanh(np.sqrt(2 / np.pi) * (x + 0.044715 * x**3)))


def layer_norm(x, gamma, beta, eps=1e-5):
    """
    Layer Normalization

    Args:
        x: Input [batch, seq_len, dim]
        gamma: Skalierungsfaktor [dim]
        beta: Offset [dim]
    """
    mean = np.mean(x, axis=-1, keepdims=True)
    variance = np.var(x, axis=-1, keepdims=True)
    normalized = (x - mean) / np.sqrt(variance + eps)
    return gamma * normalized + beta


def linear(x, weight, bias=None):
    """
    Lineare Transformation (Fully Connected Layer)

    Args:
        x: Input [..., in_features]
        weight: Gewichtsmatrix [out_features, in_features]
        bias: Bias-Vektor [out_features]
    """
    output = x @ weight.T
    if bias is not None:
        output += bias
    return output


class MultiHeadAttention:
    """
    Multi-Head Self-Attention Mechanismus
    Das Herzstück des Transformers
    """

    def __init__(self, embedding_dim, num_heads):
        self.embedding_dim = embedding_dim
        self.num_heads = num_heads
        self.head_dim = embedding_dim // num_heads

        assert embedding_dim % num_heads == 0, "embedding_dim muss durch num_heads teilbar sein"

        print(f"Multi-Head Attention:")
        print(f"  Embedding-Dim: {embedding_dim}")
        print(f"  Anzahl Heads: {num_heads}")
        print(f"  Head-Dimension: {self.head_dim}")

    def split_heads(self, x):
        """
        Teilt Embedding in mehrere Attention-Heads
        [batch, seq_len, embedding_dim] → [batch, num_heads, seq_len, head_dim]
        """
        batch_size, seq_len, _ = x.shape
        x = x.reshape(batch_size, seq_len, self.num_heads, self.head_dim)
        return x.transpose(0, 2, 1, 3)  # [batch, heads, seq, head_dim]

    def merge_heads(self, x):
        """
        Kombiniert Heads wieder zurück
        [batch, num_heads, seq_len, head_dim] → [batch, seq_len, embedding_dim]
        """
        batch_size, _, seq_len, _ = x.shape
        x = x.transpose(0, 2, 1, 3)  # [batch, seq, heads, head_dim]
        return x.reshape(batch_size, seq_len, self.embedding_dim)

    def forward(self, x, w_q, w_k, w_v, w_o, causal_mask=None):
        """
        Forward Pass der Multi-Head Attention

        Args:
            x: Input [batch, seq_len, embedding_dim]
            w_q, w_k, w_v: Query, Key, Value Gewichte
            w_o: Output Projektion
            causal_mask: Verhindert Blick in die Zukunft
        """
        batch_size, seq_len, _ = x.shape

        # 1. Linear Projektionen: Q, K, V
        q = linear(x, w_q)  # Query
        k = linear(x, w_k)  # Key
        v = linear(x, w_v)  # Value

        # 2. Split in multiple Heads
        q = self.split_heads(q)  # [batch, heads, seq, head_dim]
        k = self.split_heads(k)
        v = self.split_heads(v)

        # 3. Scaled Dot-Product Attention
        # Attention(Q, K, V) = softmax(Q * K^T / sqrt(d_k)) * V

        # Q * K^T
        attention_scores = np.matmul(q, k.transpose(0, 1, 3, 2))
        # [batch, heads, seq, seq]

        # Scale
        attention_scores = attention_scores / np.sqrt(self.head_dim)

        # 4. Causal Mask anwenden (für autoregressives Generieren)
        if causal_mask is not None:
            attention_scores = attention_scores + causal_mask

        # 5. Softmax → Attention Weights
        attention_weights = softmax(attention_scores)

        # 6. Weighted Sum of Values
        attention_output = np.matmul(attention_weights, v)
        # [batch, heads, seq, head_dim]

        # 7. Merge Heads zurück
        attention_output = self.merge_heads(attention_output)
        # [batch, seq, embedding_dim]

        # 8. Output Projektion
        output = linear(attention_output, w_o)

        return output, attention_weights


class FeedForward:
    """
    Position-wise Feed-Forward Network
    Zwei lineare Layers mit GELU Aktivierung
    """

    def __init__(self, embedding_dim, hidden_dim):
        self.embedding_dim = embedding_dim
        self.hidden_dim = hidden_dim

        print(f"Feed-Forward Network:")
        print(f"  Input/Output Dim: {embedding_dim}")
        print(f"  Hidden Dim: {hidden_dim}")

    def forward(self, x, w1, b1, w2, b2):
        """
        Forward Pass

        Args:
            x: Input [batch, seq_len, embedding_dim]
            w1, b1: Erste Layer Gewichte
            w2, b2: Zweite Layer Gewichte
        """
        # Erste Layer mit GELU
        hidden = linear(x, w1, b1)
        hidden = gelu(hidden)

        # Zweite Layer
        output = linear(hidden, w2, b2)

        return output


class TransformerBlock:
    """
    Ein vollständiger Transformer Block
    = Multi-Head Attention + Feed-Forward + Layer Norms + Residual Connections
    """

    def __init__(self, embedding_dim, num_heads, hidden_dim):
        self.attention = MultiHeadAttention(embedding_dim, num_heads)
        self.ffn = FeedForward(embedding_dim, hidden_dim)

        print(f"\nTransformer Block initialisiert")

    def forward(self, x, params, causal_mask=None):
        """
        Forward Pass durch den Transformer Block

        Args:
            x: Input [batch, seq_len, embedding_dim]
            params: Dictionary mit allen Gewichten
            causal_mask: Causal Mask für Attention
        """
        # 1. Multi-Head Self-Attention mit Residual Connection
        # Layer Norm vor Attention (Pre-LN Transformer)
        normed_x = layer_norm(x, params['ln1_gamma'], params['ln1_beta'])

        attention_out, attn_weights = self.attention.forward(
            normed_x,
            params['attn_wq'],
            params['attn_wk'],
            params['attn_wv'],
            params['attn_wo'],
            causal_mask
        )

        # Residual Connection
        x = x + attention_out

        # 2. Feed-Forward Network mit Residual Connection
        # Layer Norm vor FFN
        normed_x = layer_norm(x, params['ln2_gamma'], params['ln2_beta'])

        ffn_out = self.ffn.forward(
            normed_x,
            params['ffn_w1'],
            params['ffn_b1'],
            params['ffn_w2'],
            params['ffn_b2']
        )

        # Residual Connection
        x = x + ffn_out

        return x, attn_weights


class SmallGPT:
    """
    Ein minimales GPT-Modell
    Nur mit NumPy implementiert
    """

    def __init__(self, vocab_size, embedding_dim, num_heads, num_layers, max_seq_len=512):
        self.vocab_size = vocab_size
        self.embedding_dim = embedding_dim
        self.num_heads = num_heads
        self.num_layers = num_layers
        self.max_seq_len = max_seq_len

        print(f"\n{'='*60}")
        print(f"SMALLGPT INITIALISIERUNG")
        print(f"{'='*60}")
        print(f"Vokabulargröße: {vocab_size}")
        print(f"Embedding-Dimension: {embedding_dim}")
        print(f"Anzahl Heads: {num_heads}")
        print(f"Anzahl Layer: {num_layers}")
        print(f"Max. Sequenzlänge: {max_seq_len}")

        # Initialisiere Gewichte
        self.params = self._initialize_parameters()

        # Erstelle Transformer Blocks
        self.blocks = []
        for i in range(num_layers):
            print(f"\nLayer {i+1}:")
            block = TransformerBlock(
                embedding_dim,
                num_heads,
                hidden_dim=4 * embedding_dim  # Standard: 4x größer
            )
            self.blocks.append(block)

        print(f"\n{'='*60}")
        total_params = self._count_parameters()
        print(f"Gesamte Parameter: {total_params:,}")
        print(f"{'='*60}\n")

    def _initialize_parameters(self):
        """Initialisiert alle Modell-Parameter zufällig"""
        params = {}

        # Token Embeddings
        params['token_emb'] = np.random.randn(self.vocab_size, self.embedding_dim) * 0.02

        # Positional Embeddings
        params['pos_emb'] = np.random.randn(self.max_seq_len, self.embedding_dim) * 0.02

        # Parameter für jeden Layer
        for layer_idx in range(self.num_layers):
            prefix = f'layer{layer_idx}_'

            # Attention Gewichte
            params[prefix + 'attn_wq'] = np.random.randn(self.embedding_dim, self.embedding_dim) * 0.02
            params[prefix + 'attn_wk'] = np.random.randn(self.embedding_dim, self.embedding_dim) * 0.02
            params[prefix + 'attn_wv'] = np.random.randn(self.embedding_dim, self.embedding_dim) * 0.02
            params[prefix + 'attn_wo'] = np.random.randn(self.embedding_dim, self.embedding_dim) * 0.02

            # Layer Norm Parameter
            params[prefix + 'ln1_gamma'] = np.ones(self.embedding_dim)
            params[prefix + 'ln1_beta'] = np.zeros(self.embedding_dim)
            params[prefix + 'ln2_gamma'] = np.ones(self.embedding_dim)
            params[prefix + 'ln2_beta'] = np.zeros(self.embedding_dim)

            # Feed-Forward Gewichte
            ffn_hidden = 4 * self.embedding_dim
            params[prefix + 'ffn_w1'] = np.random.randn(ffn_hidden, self.embedding_dim) * 0.02
            params[prefix + 'ffn_b1'] = np.zeros(ffn_hidden)
            params[prefix + 'ffn_w2'] = np.random.randn(self.embedding_dim, ffn_hidden) * 0.02
            params[prefix + 'ffn_b2'] = np.zeros(self.embedding_dim)

        # Finale Layer Norm
        params['ln_final_gamma'] = np.ones(self.embedding_dim)
        params['ln_final_beta'] = np.zeros(self.embedding_dim)

        # Output Projektion (zum Vokabular)
        params['output_w'] = np.random.randn(self.vocab_size, self.embedding_dim) * 0.02
        params['output_b'] = np.zeros(self.vocab_size)

        return params

    def _count_parameters(self):
        """Zählt die Gesamtzahl der Parameter"""
        total = 0
        for param in self.params.values():
            total += param.size
        return total

    def _create_causal_mask(self, seq_len):
        """
        Erstellt Causal Mask: verhindert Blick in die Zukunft
        """
        mask = np.triu(np.ones((seq_len, seq_len)), k=1)
        mask = mask * -1e9  # Große negative Zahl = nach Softmax ~0
        return mask

    def forward(self, token_ids):
        """
        Forward Pass durch das gesamte Modell

        Args:
            token_ids: Token-IDs [batch_size, seq_len]

        Returns:
            logits: Vorhersagen [batch_size, seq_len, vocab_size]
        """
        batch_size, seq_len = token_ids.shape

        # 1. Token Embeddings
        x = self.params['token_emb'][token_ids]  # [batch, seq, emb_dim]

        # 2. Positional Embeddings hinzufügen
        positions = np.arange(seq_len)
        pos_emb = self.params['pos_emb'][positions]
        x = x + pos_emb

        # 3. Causal Mask erstellen
        causal_mask = self._create_causal_mask(seq_len)

        # 4. Durch alle Transformer Blocks
        all_attention_weights = []
        for layer_idx, block in enumerate(self.blocks):
            # Hole Parameter für diesen Layer
            prefix = f'layer{layer_idx}_'
            layer_params = {
                'attn_wq': self.params[prefix + 'attn_wq'],
                'attn_wk': self.params[prefix + 'attn_wk'],
                'attn_wv': self.params[prefix + 'attn_wv'],
                'attn_wo': self.params[prefix + 'attn_wo'],
                'ln1_gamma': self.params[prefix + 'ln1_gamma'],
                'ln1_beta': self.params[prefix + 'ln1_beta'],
                'ln2_gamma': self.params[prefix + 'ln2_gamma'],
                'ln2_beta': self.params[prefix + 'ln2_beta'],
                'ffn_w1': self.params[prefix + 'ffn_w1'],
                'ffn_b1': self.params[prefix + 'ffn_b1'],
                'ffn_w2': self.params[prefix + 'ffn_w2'],
                'ffn_b2': self.params[prefix + 'ffn_b2'],
            }

            x, attn_weights = block.forward(x, layer_params, causal_mask)
            all_attention_weights.append(attn_weights)

        # 5. Finale Layer Norm
        x = layer_norm(x, self.params['ln_final_gamma'], self.params['ln_final_beta'])

        # 6. Output Projektion (zum Vokabular)
        logits = linear(x, self.params['output_w'], self.params['output_b'])

        return logits, all_attention_weights

    def generate(self, start_tokens, max_new_tokens=20, temperature=1.0):
        """
        Generiert Text autoregressiv (Token für Token)

        Args:
            start_tokens: Start-Sequenz [1, seq_len]
            max_new_tokens: Anzahl neuer Tokens
            temperature: Sampling-Temperature
        """
        current_tokens = start_tokens.copy()

        for i in range(max_new_tokens):
            # Forward Pass
            logits, _ = self.forward(current_tokens)

            # Nur letztes Token interessiert uns
            last_logits = logits[0, -1, :]  # [vocab_size]

            # Temperature Scaling
            scaled_logits = last_logits / temperature

            # Softmax
            probs = softmax(scaled_logits)

            # Sample nächstes Token
            next_token = np.random.choice(self.vocab_size, p=probs)

            # Füge zum Kontext hinzu
            current_tokens = np.append(current_tokens, [[next_token]], axis=1)

        return current_tokens


# ============================================================================
# DEMO
# ============================================================================

# ============================================================================
# DEMO
# ============================================================================

def demo_with_tokenizer():
    """
    Demo die zeigt, wie SubwordTokenizer + SmallGPT zusammenarbeiten
    """
    print("\n" + "="*60)
    print("KOMPLETTE PIPELINE: TOKENIZER + SMALLGPT")
    print("="*60)

    # HINWEIS: SubwordTokenizer muss aus dem vorherigen Artifact importiert werden
    print("\nFür echte Verwendung:")
    print("from tokenizer_code import SubwordTokenizer")
    print("\nHier zeigen wir die konzeptuelle Integration:\n")

    print("""
# ============================================================================
# SCHRITT 1: TOKENIZER TRAINIEREN
# ============================================================================

from tokenizer_code import SubwordTokenizer

# Tokenizer erstellen und trainieren
tokenizer = SubwordTokenizer()

training_texts = [
    "Der Hund bellt laut",
    "Die Katze schläft",
    "Der Hund spielt im Garten",
    "Die Katze jagt eine Maus"
]

tokenizer.train_bpe(training_texts, num_merges=50)

vocab_size = tokenizer.get_vocab_size()
print(f"Vokabulargröße: {vocab_size}")


# ============================================================================
# SCHRITT 2: SMALLGPT ERSTELLEN
# ============================================================================

model = SmallGPT(
    vocab_size=vocab_size,      # ← Vom Tokenizer!
    embedding_dim=128,
    num_heads=8,
    num_layers=4,
    max_seq_len=512
)


# ============================================================================
# SCHRITT 3: TEXT VERARBEITEN
# ============================================================================

# Text → Token-IDs (via Tokenizer)
text = "Der Hund bellt"
token_ids = tokenizer.tokenize(text)
print(f"Text: '{text}'")
print(f"Token-IDs: {token_ids}")

# Token-IDs → NumPy Array für SmallGPT
token_array = np.array([token_ids])  # [1, seq_len]

# Forward Pass durch SmallGPT
logits, attention_weights = model.forward(token_array)
print(f"Output Logits Shape: {logits.shape}")

# Nächstes Token vorhersagen
last_logits = logits[0, -1, :]  # Letztes Token
probs = softmax(last_logits)
next_token_id = np.argmax(probs)  # Greedy Sampling

print(f"Vorhergesagtes nächstes Token-ID: {next_token_id}")

# Token-ID → Text (via Tokenizer)
next_token_text = tokenizer.id_to_token.get(next_token_id, "<UNK>")
print(f"Vorhergesagtes Wort: '{next_token_text}'")


# ============================================================================
# SCHRITT 4: TEXT GENERIEREN (KOMPLETT)
# ============================================================================

def generate_text(model, tokenizer, prompt, max_tokens=20, temperature=1.0):
    '''
    Generiert Text autoregressiv

    Args:
        model: SmallGPT Modell
        tokenizer: SubwordTokenizer
        prompt: Start-Text
        max_tokens: Anzahl zu generierender Tokens
        temperature: Sampling-Temperature
    '''
    print(f"\\nGeneriere Text für Prompt: '{prompt}'")

    # 1. Tokenisiere Prompt
    token_ids = tokenizer.tokenize(prompt)
    current_tokens = np.array([token_ids])

    generated_text = prompt

    # 2. Generiere Token für Token
    for i in range(max_tokens):
        # Forward Pass
        logits, _ = model.forward(current_tokens)

        # Letztes Token
        last_logits = logits[0, -1, :]

        # Temperature Scaling
        scaled_logits = last_logits / temperature

        # Softmax
        probs = softmax(scaled_logits)

        # Sample nächstes Token
        next_token = np.random.choice(len(probs), p=probs)

        # Füge zum Kontext hinzu
        current_tokens = np.append(current_tokens, [[next_token]], axis=1)

        # Dekodiere Token zu Text
        if next_token in tokenizer.id_to_token:
            token_text = tokenizer.id_to_token[next_token]
            generated_text += " " + token_text

        print(f"  Step {i+1}: {generated_text}")

    return generated_text


# Beispiel-Verwendung
generated = generate_text(model, tokenizer, "Der Hund", max_tokens=10)
print(f"\\nFinaler Text: '{generated}'")


# ============================================================================
# SCHRITT 5: TRAINING (KONZEPTIONELL)
# ============================================================================

print("\\n--- Training würde so aussehen: ---\\n")

def train_step(model, tokenizer, text, learning_rate=0.001):
    '''
    Ein einzelner Training-Schritt (konzeptionell)
    '''
    # 1. Tokenisiere Text
    token_ids = tokenizer.tokenize(text)

    # 2. Erstelle Trainingspaare
    for i in range(len(token_ids) - 1):
        input_ids = token_ids[:i+1]
        target_id = token_ids[i+1]

        # 3. Forward Pass
        input_array = np.array([input_ids])
        logits, _ = model.forward(input_array)

        # 4. Loss berechnen (Cross-Entropy)
        last_logits = logits[0, -1, :]
        probs = softmax(last_logits)
        loss = -np.log(probs[target_id] + 1e-10)

        print(f"  Input: {input_ids} → Target: {target_id}, Loss: {loss:.4f}")

        # 5. Backpropagation (würde hier passieren)
        # 6. Parameter-Update (würde hier passieren)

# Beispiel
train_step(model, tokenizer, "Der Hund bellt")
""")

    print("\n" + "="*60)
    print("ZUSAMMENFASSUNG DER INTEGRATION")
    print("="*60)
    print("""
┌─────────────────────────────────────────────────────────┐
│                    TEXT INPUT                            │
│                  "Der Hund bellt"                        │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
         ┌───────────────────────┐
         │  SubwordTokenizer     │
         │  .tokenize()          │
         └───────────┬───────────┘
                     │
                     ▼
              [10, 20, 30, 40]  ← Token-IDs
                     │
                     ▼
         ┌───────────────────────┐
         │  NumPy Array          │
         │  np.array([[10,20,30,40]]) │
         └───────────┬───────────┘
                     │
                     ▼
         ┌───────────────────────┐
         │   SmallGPT            │
         │   .forward()          │
         │                       │
         │   • Token Embedding   │
         │   • Positional Enc.   │
         │   • Transformer       │
         │   • Attention         │
         │   • Feed-Forward      │
         │   • Output Layer      │
         └───────────┬───────────┘
                     │
                     ▼
    Logits: [1, seq_len, vocab_size]
                     │
                     ▼
         ┌───────────────────────┐
         │   Softmax + Sampling  │
         └───────────┬───────────┘
                     │
                     ▼
              Next Token-ID: 45
                     │
                     ▼
         ┌───────────────────────┐
         │  SubwordTokenizer     │
         │  .detokenize() oder   │
         │  .id_to_token[45]     │
         └───────────┬───────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                   TEXT OUTPUT                           │
│                     "laut"                              │
└─────────────────────────────────────────────────────────┘

WICHTIG:
1. Tokenizer definiert vocab_size für picoGPT
2. Tokenizer wandelt Text ↔ IDs
3. picoGPT arbeitet nur mit IDs
4. Beide müssen das GLEICHE Vokabular teilen!
""")


def demo():
    print("\n" + "="*60)
    print("SMALLGPT DEMO - TRANSFORMER NUR MIT NUMPY")
    print("="*60)

    # Hyperparameter
    vocab_size = 100  # Klein für Demo
    embedding_dim = 64
    num_heads = 4
    num_layers = 2

    # Erstelle Modell
    model = SmallGPT(
        vocab_size=vocab_size,
        embedding_dim=embedding_dim,
        num_heads=num_heads,
        num_layers=num_layers,
        max_seq_len=128
    )

    # Test: Forward Pass
    print("\n" + "="*60)
    print("TEST: FORWARD PASS")
    print("="*60)

    # Beispiel-Input
    batch_size = 1
    seq_len = 10
    test_tokens = np.random.randint(0, vocab_size, size=(batch_size, seq_len))

    print(f"\nInput Tokens: {test_tokens[0]}")
    print(f"Shape: {test_tokens.shape}")

    # Forward Pass
    logits, attention_weights = model.forward(test_tokens)

    print(f"\nOutput Logits Shape: {logits.shape}")
    print(f"Erwartet: [{batch_size}, {seq_len}, {vocab_size}]")

    # Zeige Attention Weights vom ersten Layer
    print(f"\nAttention Weights (Layer 1):")
    print(f"  Shape: {attention_weights[0].shape}")
    print(f"  [batch, heads, seq_len, seq_len]")

    # Test: Text-Generierung
    print("\n" + "="*60)
    print("TEST: TEXT-GENERIERUNG")
    print("="*60)

    start_tokens = np.array([[1, 2, 3]])  # Start mit 3 Tokens
    print(f"\nStart Tokens: {start_tokens[0]}")

    generated = model.generate(start_tokens, max_new_tokens=10, temperature=1.0)
    print(f"Generierte Sequenz: {generated[0]}")
    print(f"Länge: {len(generated[0])} Tokens")

    print("\n" + "="*60)
    print("ZUSAMMENFASSUNG")
    print("="*60)
    print("""
✅ Kompletter Transformer nur mit NumPy
✅ Multi-Head Self-Attention
✅ Feed-Forward Networks
✅ Layer Normalization
✅ Residual Connections
✅ Causal Masking
✅ Positional Embeddings
✅ Autoregressives Generieren

KEINE externen ML-Frameworks benötigt!
Nur NumPy für Matrix-Operationen.

Das ist die Essenz eines GPT-Modells.
""")


if __name__ == "__main__":
    # Zeige Integration mit Tokenizer
    demo_with_tokenizer()

    print("\n" + "="*60)
    print("STANDALONE DEMO (ohne Tokenizer)")
    print("="*60)

    # Standalone Demo
    demo()
