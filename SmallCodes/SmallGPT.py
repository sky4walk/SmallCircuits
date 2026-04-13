"""
SmallGPT - Ein minimaler GPT-Transformer implementiert nur mit NumPy
Inspiriert von Andrej Karpathy's picoGPT und nanoGPT

Zeigt die Grundprinzipien eines Transformers ohne Framework-Magie.
Gewichte werden von Hugging Face geladen (GPT-2 oder DialoGPT).

Installation:
  python3 -m venv smallgpt_env
  source smallgpt_env/bin/activate
  pip install numpy transformers torch

Verbose-Modus:
  chat_loop(model, tokenizer, verbose=True)
  -> Zeigt jeden Berechnungsschritt im Detail
"""

# =============================================================================
# NUMPY SWITCH
# Zum Umschalten zwischen NumPy und eigener Implementierung
# einfach die gewünschte Zeile einkommentieren:
# =============================================================================
import numpy as np            # Original NumPy (schnell, empfohlen)
# import my_numpy as np       # Eigene Implementierung (langsam, transparent)


# =============================================================================
# HILFSFUNKTIONEN
# =============================================================================

def softmax(x, verbose=False):
    """
    Wandelt beliebige Zahlen in Wahrscheinlichkeiten um (Summe = 1).
    Numerisch stabil durch Subtraktion des Maximums.
    """
    if verbose:
        print(f"    softmax: Input-Shape {x.shape}")
        print(f"    softmax: Max-Wert (wird subtrahiert für Stabilität): {np.max(x, axis=-1).mean():.4f}")

    exp_x = np.exp(x - np.max(x, axis=-1, keepdims=True))
    result = exp_x / np.sum(exp_x, axis=-1, keepdims=True)

    if verbose:
        print(f"    softmax: Wahrscheinlichkeiten summieren zu: {result.sum(axis=-1).mean():.4f}")

    return result


def gelu(x, verbose=False):
    """
    GELU Aktivierungsfunktion (Gaussian Error Linear Unit).
    Entscheidet welche Neuronen 'feuern' — sanfter als ReLU.
    Dieselbe Funktion die auch GPT-4 verwendet.
    """
    if verbose:
        print(f"    gelu: Input-Shape {x.shape}, Mittelwert: {x.mean():.4f}")

    result = 0.5 * x * (1 + np.tanh(np.sqrt(2 / np.pi) * (x + 0.044715 * x**3)))

    if verbose:
        print(f"    gelu: Output-Shape {result.shape}, Mittelwert: {result.mean():.4f}")

    return result


def layer_norm(x, gamma, beta, eps=1e-5, verbose=False):
    """
    Layer Normalization: hält Zahlen auf einer einheitlichen Skala.
    Verhindert dass Werte ins Unendliche wachsen oder gegen Null schrumpfen.

    Args:
        x:     Input  [batch, seq_len, dim]
        gamma: Lernbarer Skalierungsfaktor [dim]
        beta:  Lernbarer Offset [dim]
    """
    if verbose:
        print(f"    layer_norm: Input-Shape {x.shape}")
        print(f"    layer_norm: Mittelwert vor Norm: {x.mean():.4f}, Varianz: {x.var():.4f}")

    mean = np.mean(x, axis=-1, keepdims=True)
    variance = np.var(x, axis=-1, keepdims=True)
    normalized = (x - mean) / np.sqrt(variance + eps)
    result = gamma * normalized + beta

    if verbose:
        print(f"    layer_norm: Mittelwert nach Norm: {result.mean():.4f}, Varianz: {result.var():.4f}")

    return result


def linear(x, weight, bias=None, verbose=False):
    """
    Lineare Transformation: x @ weight.T + bias
    Entspricht einem vollverbundenen Layer (Fully Connected).

    Args:
        x:      Input      [..., in_features]
        weight: Gewichte   [out_features, in_features]
        bias:   Bias-Vektor [out_features]
    """
    if verbose:
        print(f"    linear: {x.shape} @ {weight.T.shape} = {(*x.shape[:-1], weight.shape[0])}")

    output = x @ weight.T
    if bias is not None:
        output += bias

    return output


# =============================================================================
# TRANSFORMER KOMPONENTEN
# =============================================================================

class MultiHeadAttention:
    """
    Multi-Head Self-Attention — das Herzstück des Transformers.

    Beantwortet: Welche Wörter im Satz sind füreinander relevant?
    Läuft mehrfach parallel (num_heads), jeder Head lernt andere Beziehungen.

    Kernformel: Attention(Q, K, V) = softmax(Q * K^T / sqrt(d_k)) * V
        Q (Query): "Wonach suche ich?"
        K (Key):   "Was biete ich an?"
        V (Value): "Was ist mein Inhalt?"
    """

    def __init__(self, embedding_dim, num_heads):
        self.embedding_dim = embedding_dim
        self.num_heads = num_heads
        self.head_dim = embedding_dim // num_heads
        assert embedding_dim % num_heads == 0, \
            "embedding_dim muss durch num_heads teilbar sein"

    def split_heads(self, x, verbose=False):
        """
        Teilt Embedding in mehrere Attention-Heads auf.
        [batch, seq_len, embedding_dim] -> [batch, num_heads, seq_len, head_dim]
        """
        batch_size, seq_len, _ = x.shape
        x = x.reshape(batch_size, seq_len, self.num_heads, self.head_dim)
        result = x.transpose(0, 2, 1, 3)

        if verbose:
            print(f"    split_heads: -> {result.shape} ({self.num_heads} Heads, je {self.head_dim} Dimensionen)")

        return result

    def merge_heads(self, x, verbose=False):
        """
        Kombiniert Heads wieder zurück.
        [batch, num_heads, seq_len, head_dim] -> [batch, seq_len, embedding_dim]
        """
        batch_size, _, seq_len, _ = x.shape
        x = x.transpose(0, 2, 1, 3)
        result = x.reshape(batch_size, seq_len, self.embedding_dim)

        if verbose:
            print(f"    merge_heads: -> {result.shape}")

        return result

    def forward(self, x, w_q, w_k, w_v, w_o,
                b_q=None, b_k=None, b_v=None, b_o=None,
                causal_mask=None, verbose=False):

        if verbose:
            print(f"  MultiHeadAttention: Input {x.shape}")

        # 1. Lineare Projektionen: Q, K, V berechnen
        q = linear(x, w_q, b_q, verbose)
        k = linear(x, w_k, b_k, verbose)
        v = linear(x, w_v, b_v, verbose)

        if verbose:
            print(f"  Q/K/V berechnet: je {q.shape}")

        # 2. In mehrere Heads aufteilen
        q = self.split_heads(q, verbose)
        k = self.split_heads(k, verbose)
        v = self.split_heads(v, verbose)

        # 3. Attention Scores: Q * K^T / sqrt(d_k)
        attention_scores = np.matmul(q, k.transpose(0, 1, 3, 2))
        attention_scores = attention_scores / np.sqrt(self.head_dim)

        if verbose:
            print(f"  Attention Scores: {attention_scores.shape}, Mittelwert: {attention_scores.mean():.4f}")

        # 4. Causal Mask: verhindert Blick in die Zukunft
        if causal_mask is not None:
            attention_scores = attention_scores + causal_mask
            if verbose:
                print(f"  Causal Mask angewendet: Zukunft wird auf -1e9 gesetzt")

        # 5. Softmax -> Attention Weights (Wahrscheinlichkeiten)
        attention_weights = softmax(attention_scores, verbose)

        if verbose:
            print(f"  Attention Weights: {attention_weights.shape}")
            print(f"  Stärkstes Attention-Gewicht: {attention_weights.max():.4f}")

        # 6. Gewichtete Summe der Values
        attention_output = np.matmul(attention_weights, v)

        # 7. Heads zusammenführen und Output-Projektion
        attention_output = self.merge_heads(attention_output, verbose)
        output = linear(attention_output, w_o, b_o, verbose)

        if verbose:
            print(f"  MultiHeadAttention Output: {output.shape}")

        return output, attention_weights


class FeedForward:
    """
    Position-wise Feed-Forward Network.
    Zwei lineare Layer mit GELU dazwischen.

    Wenn Attention bestimmt *welche* Wörter relevant sind,
    verarbeitet FeedForward *was* damit zu tun ist.
    Hier ist das eigentliche Sprachwissen gespeichert.
    """

    def __init__(self, embedding_dim, hidden_dim):
        self.embedding_dim = embedding_dim
        self.hidden_dim = hidden_dim  # typisch 4x embedding_dim

    def forward(self, x, w1, b1, w2, b2, verbose=False):
        if verbose:
            print(f"  FeedForward: Input {x.shape}")

        # Erste Layer: aufweiten (z.B. 768 -> 3072)
        hidden = linear(x, w1, b1, verbose)
        if verbose:
            print(f"  Nach erster Layer: {hidden.shape} (aufgeweitet auf {self.hidden_dim})")

        hidden = gelu(hidden, verbose)

        # Zweite Layer: zurück auf embedding_dim (3072 -> 768)
        output = linear(hidden, w2, b2, verbose)
        if verbose:
            print(f"  FeedForward Output: {output.shape} (zurück auf {self.embedding_dim})")

        return output


class TransformerBlock:
    """
    Ein vollständiger Transformer Block.

    Ablauf in forward():
        Schritt 1: layer_norm()
        Schritt 2: MultiHeadAttention.forward()  <- + Residual Connection
        Schritt 3: layer_norm()
        Schritt 4: FeedForward.forward()         <- + Residual Connection

    Residual Connections (x = x + output):
        Das Original-Signal wird immer durchgeleitet und addiert.
        Verhindert Informationsverlust und stabilisiert das Training.
    """

    def __init__(self, embedding_dim, num_heads, hidden_dim):
        self.attention = MultiHeadAttention(embedding_dim, num_heads)
        self.ffn = FeedForward(embedding_dim, hidden_dim)

    def forward(self, x, params, causal_mask=None, verbose=False):
        if verbose:
            print(f" Schritt 1: layer_norm()")
        normed_x = layer_norm(x, params['ln1_gamma'], params['ln1_beta'], verbose=verbose)

        if verbose:
            print(f" Schritt 2: MultiHeadAttention()")
        attention_out, attn_weights = self.attention.forward(
            normed_x,
            params['attn_wq'], params['attn_wk'],
            params['attn_wv'], params['attn_wo'],
            params.get('attn_bq'), params.get('attn_bk'),
            params.get('attn_bv'), params.get('attn_bo'),
            causal_mask, verbose
        )
        x = x + attention_out  # Residual Connection
        if verbose:
            print(f" Residual Connection: x = x + attention_out -> {x.shape}")

        if verbose:
            print(f" Schritt 3: layer_norm()")
        normed_x = layer_norm(x, params['ln2_gamma'], params['ln2_beta'], verbose=verbose)

        if verbose:
            print(f" Schritt 4: FeedForward()")
        ffn_out = self.ffn.forward(
            normed_x,
            params['ffn_w1'], params['ffn_b1'],
            params['ffn_w2'], params['ffn_b2'],
            verbose
        )
        x = x + ffn_out  # Residual Connection
        if verbose:
            print(f" Residual Connection: x = x + ffn_out -> {x.shape}")

        return x, attn_weights


# =============================================================================
# SMALLGPT MODELL
# =============================================================================

class SmallGPT:
    """
    Minimales GPT-Modell — nur mit NumPy implementiert.
    Gewichte werden von Hugging Face geladen (kein eigenes Training).

    Unterstützte Modelle:
        GPT-2:     "gpt2", "gpt2-medium", "gpt2-large", "gpt2-xl"
        DialoGPT:  "microsoft/DialoGPT-small/medium/large"
    """

    def __init__(self, vocab_size, embedding_dim, num_heads, num_layers, max_seq_len=1024):
        self.vocab_size = vocab_size
        self.embedding_dim = embedding_dim
        self.num_heads = num_heads
        self.num_layers = num_layers
        self.max_seq_len = max_seq_len

        # Leeres params-Dictionary — wird von from_pretrained() befüllt
        self.params = {}

        # Transformer Blöcke erstellen (Architektur, noch ohne Gewichte)
        self.blocks = [
            TransformerBlock(embedding_dim, num_heads, hidden_dim=4 * embedding_dim)
            for _ in range(num_layers)
        ]

        print(f"\n{'='*60}")
        print(f"SMALLGPT INITIALISIERT")
        print(f"{'='*60}")
        print(f"Vokabulargröße:      {vocab_size:,}")
        print(f"Embedding-Dimension: {embedding_dim}")
        print(f"Anzahl Heads:        {num_heads}")
        print(f"Anzahl Layer:        {num_layers}")
        print(f"Max. Sequenzlänge:   {max_seq_len}")
        print(f"{'='*60}\n")

    def _create_causal_mask(self, seq_len, verbose=False):
        """
        Causal Mask: verhindert dass das Modell in die Zukunft schaut.
        Obere Dreiecksmatrix mit -1e9 -> nach Softmax praktisch 0.
        """
        mask = np.triu(np.ones((seq_len, seq_len)), k=1)
        result = mask * -1e9

        if verbose:
            print(f" Causal Mask erstellt: {result.shape}")
            print(f" {int(mask.sum())} von {seq_len*seq_len} Positionen blockiert")

        return result

    def forward(self, token_ids, verbose=False):
        """
        Forward Pass durch das gesamte Modell.

        Args:
            token_ids: Token-IDs [batch_size, seq_len]
            verbose:   True = zeigt jeden Berechnungsschritt

        Returns:
            logits:               Rohe Vorhersagen [batch, seq_len, vocab_size]
            all_attention_weights: Attention-Gewichte aller Layer
        """
        batch_size, seq_len = token_ids.shape

        if verbose:
            print(f"\n{'='*60}")
            print(f"FORWARD PASS")
            print(f"{'='*60}")
            print(f"Input: {token_ids.shape} ({seq_len} Tokens)")

        # 1. Token Embeddings: IDs -> Vektoren
        x = self.params['token_emb'][token_ids]
        if verbose:
            print(f"\n[1] Token Embeddings:")
            print(f"    IDs {token_ids.shape} -> Vektoren {x.shape}")
            print(f"    Jede ID wird zu einem {self.embedding_dim}-dim Vektor")

        # 2. Positional Embeddings: Position im Satz kodieren
        positions = np.arange(seq_len)
        x = x + self.params['pos_emb'][positions]
        if verbose:
            print(f"\n[2] Positional Embeddings addiert:")
            print(f"    Jeder Vektor kennt jetzt seine Position im Satz")
            print(f"    Shape bleibt: {x.shape}")

        # 3. Causal Mask erstellen
        if verbose:
            print(f"\n[3] Causal Mask:")
        causal_mask = self._create_causal_mask(seq_len, verbose)

        # 4. Durch alle Transformer Blöcke
        all_attention_weights = []
        for layer_idx, block in enumerate(self.blocks):
            if verbose:
                print(f"\n[4.{layer_idx+1}] Transformer Block {layer_idx+1}/{self.num_layers}:")

            p = f'layer{layer_idx}_'
            layer_params = {k[len(p):]: v for k, v in self.params.items() if k.startswith(p)}
            x, attn_weights = block.forward(x, layer_params, causal_mask, verbose)
            all_attention_weights.append(attn_weights)

            if verbose:
                print(f" Block {layer_idx+1} Output: {x.shape}")

        # 5. Finale Layer Norm
        if verbose:
            print(f"\n[5] Finale Layer Norm:")
        x = layer_norm(x, self.params['ln_final_gamma'], self.params['ln_final_beta'], verbose=verbose)

        # 6. Output-Projektion: Vektoren -> Wahrscheinlichkeiten über Vokabular
        logits = linear(x, self.params['output_w'], self.params['output_b'], verbose)
        if verbose:
            print(f"\n[6] Output-Projektion:")
            print(f"    {x.shape} -> Logits {logits.shape}")
            print(f"    Für jedes Token: {self.vocab_size} Wahrscheinlichkeiten")

        return logits, all_attention_weights

    def generate(self, start_tokens, max_new_tokens=20, temperature=1.0,
                 eos_token_id=None, verbose=False):
        """
        Generiert Text autoregressiv — Token für Token.

        Args:
            start_tokens:   Start-Sequenz [1, seq_len]
            max_new_tokens: Maximale Anzahl neuer Tokens
            temperature:    Höher = kreativer, Niedriger = deterministischer
            eos_token_id:   Stoppzeichen (Generation endet hier)
            verbose:        True = zeigt jeden Berechnungsschritt
        """
        current_tokens = start_tokens.copy()

        for step in range(max_new_tokens):
            if verbose:
                print(f"\n{'='*60}")
                print(f"GENERIERUNGS-SCHRITT {step+1}")
                print(f"Aktueller Kontext: {current_tokens.shape[1]} Tokens")

            # Forward Pass mit aktuellem Kontext
            logits, _ = self.forward(current_tokens, verbose)

            # Nur das letzte Token interessiert uns
            last_logits = logits[0, -1, :] / temperature
            if verbose:
                print(f"\nTemperature Scaling: /{temperature}")
                print(f"Top-5 Logits: {np.sort(last_logits)[-5:][::-1].round(3)}")

            # Softmax -> Wahrscheinlichkeiten -> Sample nächstes Token
            probs = softmax(last_logits)
            next_token = np.random.choice(self.vocab_size, p=probs)

            if verbose:
                print(f"Höchste Wahrscheinlichkeit: {probs.max():.4f}")
                print(f"Gewähltes Token: ID {next_token}")

            # Token an Kontext anhängen
            current_tokens = np.append(current_tokens, [[next_token]], axis=1)

            # Stopp bei EOS-Token
            if eos_token_id is not None and next_token == eos_token_id:
                if verbose:
                    print(f"EOS-Token erreicht — Generierung gestoppt")
                break

        return current_tokens

    # =========================================================================
    # HUGGING FACE LOADER
    # =========================================================================

    @classmethod
    def from_pretrained(cls, model_name="gpt2"):
        """
        Lädt vortrainierte GPT-2 Gewichte von Hugging Face.
        Gibt eine fertige SmallGPT-Instanz + Tokenizer zurück.

        Beim ersten Aufruf werden die Gewichte heruntergeladen
        und automatisch im Cache gespeichert (~/.cache/huggingface/).
        Danach startet das Modell sofort aus dem Cache.
        """
        try:
            from transformers import GPT2Model, GPT2Config, GPT2Tokenizer
        except ImportError:
            raise ImportError(
                "Hugging Face transformers nicht installiert.\n"
                "Bitte installieren mit: pip install transformers torch"
            )

        print(f"\n{'='*60}")
        print(f"LADE GEWICHTE VON HUGGING FACE")
        print(f"Modell: {model_name}")
        print(f"{'='*60}")

        print("Lade Konfiguration...")
        config = GPT2Config.from_pretrained(model_name)

        print("Lade Tokenizer...")
        tokenizer = GPT2Tokenizer.from_pretrained(model_name)

        print("Lade Modell-Gewichte...")
        hf_model = GPT2Model.from_pretrained(model_name)
        sd = hf_model.state_dict()

        print("Erstelle SmallGPT...")
        model = cls(
            vocab_size    = config.vocab_size,   # 50257
            embedding_dim = config.n_embd,       # 768 bei gpt2
            num_heads     = config.n_head,       # 12  bei gpt2
            num_layers    = config.n_layer,      # 12  bei gpt2
            max_seq_len   = config.n_positions,  # 1024
        )

        print("Übertrage Gewichte...")

        # Token + Positional Embeddings
        model.params['token_emb']      = sd['wte.weight'].detach().numpy()
        model.params['pos_emb']        = sd['wpe.weight'].detach().numpy()

        # Finale Layer Norm
        model.params['ln_final_gamma'] = sd['ln_f.weight'].detach().numpy()
        model.params['ln_final_beta']  = sd['ln_f.bias'].detach().numpy()

        # Output-Projektion teilt sich die Matrix mit token_emb (weight tying)
        model.params['output_w']       = sd['wte.weight'].detach().numpy()
        model.params['output_b']       = np.zeros(config.vocab_size)

        # Pro Transformer-Layer
        for i in range(config.n_layer):
            p = f'layer{i}_'  # SmallGPT Namensschema
            h = f'h.{i}.'     # Hugging Face Namensschema

            # Layer Norms
            model.params[p+'ln1_gamma'] = sd[h+'ln_1.weight'].detach().numpy()
            model.params[p+'ln1_beta']  = sd[h+'ln_1.bias'].detach().numpy()
            model.params[p+'ln2_gamma'] = sd[h+'ln_2.weight'].detach().numpy()
            model.params[p+'ln2_beta']  = sd[h+'ln_2.bias'].detach().numpy()

            # Attention — GPT-2 speichert Q, K, V zusammen in c_attn [emb_dim, 3*emb_dim]
            d = config.n_embd
            c_attn_w = sd[h+'attn.c_attn.weight'].detach().numpy()  # [768, 2304]
            c_attn_b = sd[h+'attn.c_attn.bias'].detach().numpy()    # [2304]

            model.params[p+'attn_wq'] = c_attn_w[:, :d].T
            model.params[p+'attn_wk'] = c_attn_w[:, d:2*d].T
            model.params[p+'attn_wv'] = c_attn_w[:, 2*d:].T
            model.params[p+'attn_bq'] = c_attn_b[:d]
            model.params[p+'attn_bk'] = c_attn_b[d:2*d]
            model.params[p+'attn_bv'] = c_attn_b[2*d:]

            model.params[p+'attn_wo'] = sd[h+'attn.c_proj.weight'].detach().numpy().T
            model.params[p+'attn_bo'] = sd[h+'attn.c_proj.bias'].detach().numpy()

            # Feed-Forward
            model.params[p+'ffn_w1'] = sd[h+'mlp.c_fc.weight'].detach().numpy().T
            model.params[p+'ffn_b1'] = sd[h+'mlp.c_fc.bias'].detach().numpy()
            model.params[p+'ffn_w2'] = sd[h+'mlp.c_proj.weight'].detach().numpy().T
            model.params[p+'ffn_b2'] = sd[h+'mlp.c_proj.bias'].detach().numpy()

            if (i + 1) % 3 == 0:
                print(f"  Layer {i+1}/{config.n_layer} geladen...")

        print(f"\n Alle Gewichte erfolgreich geladen!")
        print(f"{'='*60}\n")

        return model, tokenizer

    def save_weights(self, path="smallgpt_weights.npz"):
        """Speichert Gewichte als .npz — beim nächsten Start kein Download nötig."""
        np.savez(path, **self.params)
        print(f" Gewichte gespeichert: {path}")

    def load_weights(self, path="smallgpt_weights.npz"):
        """Lädt Gewichte aus einer .npz Datei."""
        data = np.load(path, allow_pickle=True)
        self.params = dict(data)
        print(f" Gewichte geladen: {path}")


# =============================================================================
# CHAT
# =============================================================================

def chat_loop(model, tokenizer, verbose=False):
    """
    Interaktiver Chat mit Kontextspeicher.

    Bei jeder Eingabe wird der gesamte bisherige Gesprächsverlauf
    mitgeschickt — genau wie bei ChatGPT & Co.

    Args:
        verbose: True = zeigt jeden Berechnungsschritt im Detail

    Befehle:
        exit    -> Chat beenden
        reset   -> Kontext löschen, neues Gespräch starten
        verbose -> Verbose-Modus umschalten
    """
    context_ids = []

    print("\n" + "="*60)
    print("CHAT GESTARTET")
    print("Befehle: 'exit' = Beenden, 'reset' = Neues Gespräch")
    print("         'verbose' = Berechnungen ein/ausblenden")
    print(f"Verbose-Modus: {'AN' if verbose else 'AUS'}")
    print("="*60)

    while True:
        user_input = input("\nDu: ")

        if user_input.lower() == "exit":
            print("Chat beendet.")
            break

        if user_input.lower() == "reset":
            context_ids = []
            print("(Kontext zurückgesetzt — neues Gespräch)")
            continue

        if user_input.lower() == "verbose":
            verbose = not verbose
            print(f"(Verbose-Modus: {'AN' if verbose else 'AUS'})")
            continue

        # Eingabe tokenisieren + EOS-Token anhängen
        # EOS-Token zeigt DialoGPT wo die Gesprächsrunde endet
        new_tokens = tokenizer.encode(user_input + tokenizer.eos_token)
        context_ids = context_ids + new_tokens

        if verbose:
            print(f"\n[Tokenizer] '{user_input}' -> {len(new_tokens)} Tokens: {new_tokens[:5]}...")

        # Context Window prüfen — GPT-2 max 1024 Tokens
        if len(context_ids) > 900:
            print("(Kontext wird gekürzt — ältere Teile vergessen...)")
            context_ids = context_ids[-900:]

        # Generieren mit vollem Kontext
        input_array = np.array([context_ids])
        output = model.generate(
            input_array,
            max_new_tokens=50,
            temperature=0.8,
            eos_token_id=tokenizer.eos_token_id,
            verbose=verbose
        )

        # Nur neue Tokens extrahieren — EOS-Token aus Antwort entfernen
        new_token_ids = output[0][len(context_ids):]
        new_token_ids = [t for t in new_token_ids if t != tokenizer.eos_token_id]
        response = tokenizer.decode(new_token_ids)

        if verbose:
            print(f"\n[Tokenizer] {len(new_token_ids)} neue Token-IDs -> '{response}'")

        # Antwort zum Kontext hinzufügen (mit EOS als Trenner für nächste Runde)
        context_ids = context_ids + new_token_ids + [tokenizer.eos_token_id]

        print(f"\nModell: {response}")
        print(f"(Kontext: {len(context_ids)}/1024 Tokens)")


# =============================================================================
# MODELLAUSWAHL
# =============================================================================

def select_model():
    """Interaktive Modellauswahl beim Programmstart."""

    models = {
        "1": ("gpt2",                       "GPT-2 Small      ~500MB   Text-Completion"),
        "2": ("gpt2-medium",                "GPT-2 Medium    ~1.5GB   Text-Completion, besser"),
        "3": ("gpt2-large",                 "GPT-2 Large     ~3.0GB   Text-Completion, noch besser"),
        "4": ("gpt2-xl",                    "GPT-2 XL        ~6.0GB   Text-Completion, am besten"),
        "5": ("microsoft/DialoGPT-small",   "DialoGPT Small  ~500MB   Gespräche"),
        "6": ("microsoft/DialoGPT-medium",  "DialoGPT Medium ~1.5GB   Gespräche, besser"),
        "7": ("microsoft/DialoGPT-large",   "DialoGPT Large  ~3.0GB   Gespräche, am besten"),
    }

    print("\n" + "="*60)
    print("SMALLGPT - MODELLAUSWAHL")
    print("="*60)
    print("Verfügbare Modelle:\n")
    for key, (_, description) in models.items():
        print(f"  [{key}] {description}")
    print("="*60)

    while True:
        choice = input("\nModell wählen (1-7): ").strip()

        if choice in models:
            model_name, description = models[choice]
            print(f"\n-> Gewählt: {description.strip()}")
            model, tokenizer = SmallGPT.from_pretrained(model_name)

            verbose_choice = input("\nVerbose-Modus aktivieren? (j/n): ").strip().lower()
            verbose = verbose_choice == "j"

            chat_loop(model, tokenizer, verbose=verbose)
            return

        print("Ungültige Eingabe, bitte 1-7 eingeben.")


if __name__ == "__main__":
    select_model()
