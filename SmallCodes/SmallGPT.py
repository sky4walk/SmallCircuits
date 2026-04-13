"""
SmallGPT - Ein minimaler GPT-Transformer implementiert nur mit NumPy
Inspiriert von Andrej Karpathy's picoGPT und nanoGPT

Zeigt die Grundprinzipien eines Transformers ohne Framework-Magie

NEU: Hugging Face GPT-2 Gewichte laden mit load_from_huggingface()

Installation:
  python3 -m venv smallgpt_env
  source smallgpt_env/bin/activate
  pip install numpy transformers torch
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
    mean = np.mean(x, axis=-1, keepdims=True)
    variance = np.var(x, axis=-1, keepdims=True)
    normalized = (x - mean) / np.sqrt(variance + eps)
    return gamma * normalized + beta


def linear(x, weight, bias=None):
    output = x @ weight.T
    if bias is not None:
        output += bias
    return output


class MultiHeadAttention:
    def __init__(self, embedding_dim, num_heads):
        self.embedding_dim = embedding_dim
        self.num_heads = num_heads
        self.head_dim = embedding_dim // num_heads
        assert embedding_dim % num_heads == 0

    def split_heads(self, x):
        batch_size, seq_len, _ = x.shape
        x = x.reshape(batch_size, seq_len, self.num_heads, self.head_dim)
        return x.transpose(0, 2, 1, 3)

    def merge_heads(self, x):
        batch_size, _, seq_len, _ = x.shape
        x = x.transpose(0, 2, 1, 3)
        return x.reshape(batch_size, seq_len, self.embedding_dim)

    def forward(self, x, w_q, w_k, w_v, w_o, b_q=None, b_k=None, b_v=None, b_o=None, causal_mask=None):
        q = linear(x, w_q, b_q)
        k = linear(x, w_k, b_k)
        v = linear(x, w_v, b_v)

        q = self.split_heads(q)
        k = self.split_heads(k)
        v = self.split_heads(v)

        attention_scores = np.matmul(q, k.transpose(0, 1, 3, 2))
        attention_scores = attention_scores / np.sqrt(self.head_dim)

        if causal_mask is not None:
            attention_scores = attention_scores + causal_mask

        attention_weights = softmax(attention_scores)
        attention_output = np.matmul(attention_weights, v)
        attention_output = self.merge_heads(attention_output)
        output = linear(attention_output, w_o, b_o)

        return output, attention_weights


class FeedForward:
    def __init__(self, embedding_dim, hidden_dim):
        self.embedding_dim = embedding_dim
        self.hidden_dim = hidden_dim

    def forward(self, x, w1, b1, w2, b2):
        hidden = linear(x, w1, b1)
        hidden = gelu(hidden)
        output = linear(hidden, w2, b2)
        return output


class TransformerBlock:
    def __init__(self, embedding_dim, num_heads, hidden_dim):
        self.attention = MultiHeadAttention(embedding_dim, num_heads)
        self.ffn = FeedForward(embedding_dim, hidden_dim)

    def forward(self, x, params, causal_mask=None):
        # Attention mit Residual
        normed_x = layer_norm(x, params['ln1_gamma'], params['ln1_beta'])
        attention_out, attn_weights = self.attention.forward(
            normed_x,
            params['attn_wq'], params['attn_wk'],
            params['attn_wv'], params['attn_wo'],
            params.get('attn_bq'), params.get('attn_bk'),
            params.get('attn_bv'), params.get('attn_bo'),
            causal_mask
        )
        x = x + attention_out

        # Feed-Forward mit Residual
        normed_x = layer_norm(x, params['ln2_gamma'], params['ln2_beta'])
        ffn_out = self.ffn.forward(
            normed_x,
            params['ffn_w1'], params['ffn_b1'],
            params['ffn_w2'], params['ffn_b2']
        )
        x = x + ffn_out

        return x, attn_weights


class SmallGPT:
    """
    Ein minimales GPT-Modell - nur mit NumPy implementiert.
    Kann mit zufälligen Gewichten oder mit GPT-2 Gewichten von
    Hugging Face verwendet werden.
    """

    def __init__(self, vocab_size, embedding_dim, num_heads, num_layers, max_seq_len=1024):
        self.vocab_size = vocab_size
        self.embedding_dim = embedding_dim
        self.num_heads = num_heads
        self.num_layers = num_layers
        self.max_seq_len = max_seq_len

        print(f"\n{'='*60}")
        print(f"SMALLGPT INITIALISIERUNG")
        print(f"{'='*60}")
        print(f"Vokabulargröße:      {vocab_size}")
        print(f"Embedding-Dimension: {embedding_dim}")
        print(f"Anzahl Heads:        {num_heads}")
        print(f"Anzahl Layer:        {num_layers}")
        print(f"Max. Sequenzlänge:   {max_seq_len}")

        self.params = self._initialize_parameters()

        self.blocks = []
        for i in range(num_layers):
            block = TransformerBlock(
                embedding_dim,
                num_heads,
                hidden_dim=4 * embedding_dim
            )
            self.blocks.append(block)

        total_params = self._count_parameters()
        print(f"Parameter (zufällig): {total_params:,}")
        print(f"{'='*60}\n")

    def _initialize_parameters(self):
        """Initialisiert alle Parameter zufällig"""
        params = {}
        params['token_emb'] = np.random.randn(self.vocab_size, self.embedding_dim) * 0.02
        params['pos_emb']   = np.random.randn(self.max_seq_len, self.embedding_dim) * 0.02

        for i in range(self.num_layers):
            p = f'layer{i}_'
            ffn_hidden = 4 * self.embedding_dim

            params[p+'attn_wq'] = np.random.randn(self.embedding_dim, self.embedding_dim) * 0.02
            params[p+'attn_wk'] = np.random.randn(self.embedding_dim, self.embedding_dim) * 0.02
            params[p+'attn_wv'] = np.random.randn(self.embedding_dim, self.embedding_dim) * 0.02
            params[p+'attn_wo'] = np.random.randn(self.embedding_dim, self.embedding_dim) * 0.02
            params[p+'attn_bq'] = np.zeros(self.embedding_dim)
            params[p+'attn_bk'] = np.zeros(self.embedding_dim)
            params[p+'attn_bv'] = np.zeros(self.embedding_dim)
            params[p+'attn_bo'] = np.zeros(self.embedding_dim)

            params[p+'ln1_gamma'] = np.ones(self.embedding_dim)
            params[p+'ln1_beta']  = np.zeros(self.embedding_dim)
            params[p+'ln2_gamma'] = np.ones(self.embedding_dim)
            params[p+'ln2_beta']  = np.zeros(self.embedding_dim)

            params[p+'ffn_w1'] = np.random.randn(ffn_hidden, self.embedding_dim) * 0.02
            params[p+'ffn_b1'] = np.zeros(ffn_hidden)
            params[p+'ffn_w2'] = np.random.randn(self.embedding_dim, ffn_hidden) * 0.02
            params[p+'ffn_b2'] = np.zeros(self.embedding_dim)

        params['ln_final_gamma'] = np.ones(self.embedding_dim)
        params['ln_final_beta']  = np.zeros(self.embedding_dim)
        params['output_w']       = np.random.randn(self.vocab_size, self.embedding_dim) * 0.02
        params['output_b']       = np.zeros(self.vocab_size)

        return params

    def _count_parameters(self):
        return sum(p.size for p in self.params.values())

    def _create_causal_mask(self, seq_len):
        mask = np.triu(np.ones((seq_len, seq_len)), k=1)
        return mask * -1e9

    def forward(self, token_ids):
        batch_size, seq_len = token_ids.shape

        x = self.params['token_emb'][token_ids]
        positions = np.arange(seq_len)
        x = x + self.params['pos_emb'][positions]

        causal_mask = self._create_causal_mask(seq_len)

        all_attention_weights = []
        for layer_idx, block in enumerate(self.blocks):
            p = f'layer{layer_idx}_'
            layer_params = {k[len(p):]: v for k, v in self.params.items() if k.startswith(p)}
            x, attn_weights = block.forward(x, layer_params, causal_mask)
            all_attention_weights.append(attn_weights)

        x = layer_norm(x, self.params['ln_final_gamma'], self.params['ln_final_beta'])
        logits = linear(x, self.params['output_w'], self.params['output_b'])

        return logits, all_attention_weights

    def generate(self, start_tokens, max_new_tokens=20, temperature=1.0, eos_token_id=None):
        current_tokens = start_tokens.copy()

        for _ in range(max_new_tokens):
            logits, _ = self.forward(current_tokens)
            last_logits = logits[0, -1, :] / temperature
            probs = softmax(last_logits)
            next_token = np.random.choice(self.vocab_size, p=probs)
            current_tokens = np.append(current_tokens, [[next_token]], axis=1)

            # Stopp bei EOS-Token
            if eos_token_id is not None and next_token == eos_token_id:
                break

        return current_tokens

    # =========================================================================
    # HUGGING FACE GPT-2 LOADER
    # =========================================================================

    @classmethod
    def from_pretrained(cls, model_name="gpt2"):
        """
        Lädt ein vortrainiertes GPT-2 Modell von Hugging Face
        und gibt eine fertige SmallGPT-Instanz zurück.

        Verfügbare Modelle:
            "gpt2"        → 117M Parameter (klein, schnell)
            "gpt2-medium" → 345M Parameter
            "gpt2-large"  → 774M Parameter
            "gpt2-xl"     → 1.5B Parameter (braucht viel RAM!)

        Verwendung:
            model, tokenizer = SmallGPT.from_pretrained("gpt2")
            token_ids = tokenizer.encode("Der Hund bellt")
            output = model.generate(np.array([token_ids]), max_new_tokens=20)
            print(tokenizer.decode(output[0]))
        """
        try:
            from transformers import GPT2Model, GPT2Config, GPT2Tokenizer
        except ImportError:
            raise ImportError(
                "Hugging Face transformers nicht installiert.\n"
                "Bitte installieren mit: pip install transformers torch"
            )

        print(f"\n{'='*60}")
        print(f"LADE GPT-2 GEWICHTE VON HUGGING FACE")
        print(f"Modell: {model_name}")
        print(f"{'='*60}")

        # Lade Konfiguration und Gewichte
        print("Lade Konfiguration...")
        config = GPT2Config.from_pretrained(model_name)

        print("Lade Tokenizer...")
        tokenizer = GPT2Tokenizer.from_pretrained(model_name)

        print("Lade Modell-Gewichte...")
        hf_model = GPT2Model.from_pretrained(model_name)
        sd = hf_model.state_dict()

        # SmallGPT mit GPT-2 Dimensionen erstellen
        print("Erstelle SmallGPT mit GPT-2 Dimensionen...")
        model = cls(
            vocab_size   = config.vocab_size,      # 50257
            embedding_dim= config.n_embd,          # 768 (gpt2)
            num_heads    = config.n_head,          # 12  (gpt2)
            num_layers   = config.n_layer,         # 12  (gpt2)
            max_seq_len  = config.n_positions,     # 1024
        )

        # Gewichte übertragen
        print("Übertrage Gewichte...")

        # Embeddings
        model.params['token_emb']      = sd['wte.weight'].detach().numpy()
        model.params['pos_emb']        = sd['wpe.weight'].detach().numpy()

        # Finale Layer Norm
        model.params['ln_final_gamma'] = sd['ln_f.weight'].detach().numpy()
        model.params['ln_final_beta']  = sd['ln_f.bias'].detach().numpy()

        # Output Projektion — GPT-2 teilt diese Matrix mit token_emb (weight tying)
        model.params['output_w']       = sd['wte.weight'].detach().numpy()
        model.params['output_b']       = np.zeros(config.vocab_size)

        # Pro Transformer-Layer
        for i in range(config.n_layer):
            p = f'layer{i}_'   # SmallGPT Namensschema
            h = f'h.{i}.'      # Hugging Face Namensschema

            # Layer Norms
            model.params[p+'ln1_gamma'] = sd[h+'ln_1.weight'].detach().numpy()
            model.params[p+'ln1_beta']  = sd[h+'ln_1.bias'].detach().numpy()
            model.params[p+'ln2_gamma'] = sd[h+'ln_2.weight'].detach().numpy()
            model.params[p+'ln2_beta']  = sd[h+'ln_2.bias'].detach().numpy()

            # Attention
            # GPT-2 speichert Q, K, V zusammen in c_attn: [emb_dim, 3*emb_dim]
            # Wir müssen sie aufteilen
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

        print(f"\n✅ Alle Gewichte erfolgreich geladen!")
        print(f"{'='*60}\n")

        return model, tokenizer

    def save_weights(self, path="smallgpt_weights.npz"):
        """Speichert die aktuellen Gewichte als .npz Datei"""
        np.savez(path, **self.params)
        print(f"✅ Gewichte gespeichert: {path}")

    def load_weights(self, path="smallgpt_weights.npz"):
        """Lädt Gewichte aus einer .npz Datei"""
        data = np.load(path, allow_pickle=True)
        self.params = dict(data)
        print(f"✅ Gewichte geladen: {path}")


# =============================================================================
# DEMO
# =============================================================================
def chat_loop(model, tokenizer):
    """
    Interaktiver Chat mit Kontextspeicher.
    Der gesamte Gesprächsverlauf wird bei jeder Anfrage mitgeschickt.
    """
    context_ids = []

    print("\n" + "="*60)
    print("CHAT GESTARTET")
    print("Tippe 'exit' zum Beenden, 'reset' für neues Gespräch")
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

        # Neue Tokens an bisherigen Kontext anhängen
        # EOS-Token anhängen damit DialoGPT weiß wo die Runde endet
        new_tokens = tokenizer.encode(user_input + tokenizer.eos_token)
        context_ids = context_ids + new_tokens

        # Context Window prüfen — max 1024 Tokens bei GPT-2!
        if len(context_ids) > 900:
            print("(Kontext wird gekürzt — ältere Teile vergessen...)")
            context_ids = context_ids[-900:]

        # Generieren mit vollem Kontext
        input_array = np.array([context_ids])
        output = model.generate(
            input_array,
            max_new_tokens=50,
            temperature=0.8,
            eos_token_id=tokenizer.eos_token_id
        )

        # Nur die neu generierten Tokens extrahieren — ohne EOS-Token
        new_token_ids = output[0][len(context_ids):]
        new_token_ids = [t for t in new_token_ids if t != tokenizer.eos_token_id]
        response = tokenizer.decode(new_token_ids)

        # Antwort ebenfalls zum Kontext hinzufügen (mit EOS-Token als Trenner)
        context_ids = context_ids + new_token_ids + [tokenizer.eos_token_id]

        print(f"Modell: {response}")
        print(f"(Kontext: {len(context_ids)}/1024 Tokens)")


def select_model():
    """Interaktive Modellauswahl beim Programmstart"""

    models = {
        "1": ("gpt2",                        "GPT-2 Small       ~500MB  Text-Completion"),
        "2": ("gpt2-medium",                  "GPT-2 Medium     ~1.5GB  Text-Completion, besser"),
        "3": ("gpt2-large",                  "GPT-2 Large     ~3.0GB  Text-Completion, besser"),
        "4": ("gpt2-xl",                  "GPT-2 XL        ~6.0GB  Text-Completion, am besten"),
        "5": ("microsoft/DialoGPT-small",     "DialoGPT Small   ~500MB  Gespräche"),
        "6": ("microsoft/DialoGPT-medium",    "DialoGPT Medium  ~1.5GB  Gespräche, besser"),
        "7": ("microsoft/DialoGPT-large",     "DialoGPT Large   ~3GB    Gespräche, am besten"),
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
            print(f"\n→ Gewählt: {description.strip()}")
            model, tokenizer = SmallGPT.from_pretrained(model_name)
            chat_loop(model, tokenizer)
            return

        print("Ungültige Eingabe, bitte 1-7 eingeben.")


if __name__ == "__main__":
    select_model()
