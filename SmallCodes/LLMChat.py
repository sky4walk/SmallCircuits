"""
chat_llm.py - Interaktiver Chat mit verschiedenen LLMs via Hugging Face

Unterstützte Modelle:
    GPT-2, DialoGPT, GPT-Neo, TinyLlama, Mistral und mehr

Installation:
    python3 -m venv llm_env
    source llm_env/bin/activate
    pip install torch transformers accelerate

Verwendung:
    python chat_llm.py
"""

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


# =============================================================================
# MODELL-KONFIGURATIONEN
# Chat-Format und Parameter je nach Modell
# =============================================================================

MODELS = {
    "1": {
        "name":        "gpt2",
        "label":       "GPT-2 Small         ~1GB    Text-Completion",
        "format":      "gpt2",
        "max_context": 900,
    },
    "2": {
        "name":        "gpt2-medium",
        "label":       "GPT-2 Medium        ~3GB    Text-Completion, besser",
        "format":      "gpt2",
        "max_context": 900,
    },
    "3": {
        "name":        "microsoft/DialoGPT-small",
        "label":       "DialoGPT Small      ~1GB    Gespräche",
        "format":      "dialogpt",
        "max_context": 900,
    },
    "4": {
        "name":        "microsoft/DialoGPT-medium",
        "label":       "DialoGPT Medium     ~3GB    Gespräche, besser",
        "format":      "dialogpt",
        "max_context": 900,
    },
    "5": {
        "name":        "EleutherAI/gpt-neo-125m",
        "label":       "GPT-Neo 125M        ~1GB    Text-Completion, moderner",
        "format":      "gpt2",
        "max_context": 1900,
    },
    "6": {
        "name":        "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
        "label":       "TinyLlama 1.1B      ~4GB    Chat, modern, empfohlen",
        "format":      "tinyllama",
        "max_context": 3900,
    },
    "7": {
        "name":        "mistralai/Mistral-7B-Instruct-v0.1",
        "label":       "Mistral 7B          ~16GB   Chat, sehr gut (GPU nötig)",
        "format":      "mistral",
        "max_context": 7900,
    },
}


# =============================================================================
# CHAT-FORMAT FUNKTIONEN
# Jedes Modell erwartet einen anderen Gesprächsaufbau
# =============================================================================

def format_input(user_input, context, fmt, tokenizer):
    """
    Bereitet die Eingabe im richtigen Format für das jeweilige Modell vor.

    GPT-2 / GPT-Neo:
        Einfacher Text, Runden durch EOS-Token getrennt

    DialoGPT:
        Wie GPT-2, aber speziell auf Gespräche trainiert

    TinyLlama:
        <|system|>...<|user|>...<|assistant|>

    Mistral:
        [INST] ... [/INST]
    """
    if fmt == "gpt2":
        return context + user_input + tokenizer.eos_token

    elif fmt == "dialogpt":
        return context + user_input + tokenizer.eos_token

    elif fmt == "tinyllama":
        if not context:
            # Erster Aufruf: System-Prompt hinzufügen
            context = "<|system|>\nDu bist ein hilfreicher Assistent.</s>\n"
        return context + f"<|user|>\n{user_input}</s>\n<|assistant|>\n"

    elif fmt == "mistral":
        return context + f"[INST] {user_input} [/INST]"

    return context + user_input


def format_response(response, fmt, tokenizer):
    """
    Hängt die Antwort im richtigen Format an den Kontext an.
    """
    if fmt in ("gpt2", "dialogpt"):
        return response + tokenizer.eos_token

    elif fmt == "tinyllama":
        return response + "</s>\n"

    elif fmt == "mistral":
        return response + " "

    return response


# =============================================================================
# MODELL LADEN
# =============================================================================

def load_model(model_config):
    """
    Lädt Tokenizer und Modell von Hugging Face.
    Beim ersten Aufruf wird heruntergeladen (~/.cache/huggingface/).
    Danach startet es sofort aus dem Cache.
    """
    model_name = model_config["name"]

    print(f"\n{'='*60}")
    print(f"LADE MODELL VON HUGGING FACE")
    print(f"Modell: {model_name}")
    print(f"{'='*60}")

    # GPU falls verfügbar, sonst CPU
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Gerät: {device.upper()}")

    print("Lade Tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(model_name)

    # GPT-2 hat keinen PAD-Token — EOS-Token als Ersatz
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    print("Lade Modell-Gewichte...")
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.float16 if device == "cuda" else torch.float32,
        low_cpu_mem_usage=True,
    )
    model = model.to(device)
    model.eval()

    print(f"\n Modell erfolgreich geladen!")
    print(f"{'='*60}\n")

    return model, tokenizer, device


# =============================================================================
# CHAT LOOP
# =============================================================================

def chat_loop(model, tokenizer, device, model_config):
    """
    Interaktiver Chat mit Kontextspeicher.

    Bei jeder Eingabe wird der gesamte bisherige Gesprächsverlauf
    mitgeschickt — genau wie bei ChatGPT & Co.

    Befehle:
        exit  -> Chat beenden
        reset -> Kontext löschen, neues Gespräch starten
    """
    context = ""
    fmt = model_config["format"]
    max_context = model_config["max_context"]

    print("\n" + "="*60)
    print("CHAT GESTARTET")
    print("Befehle: 'exit' = Beenden, 'reset' = Neues Gespräch")
    print("="*60)

    while True:
        user_input = input("\nDu: ")

        if user_input.lower() == "exit":
            print("Chat beendet.")
            break

        if user_input.lower() == "reset":
            context = ""
            print("(Kontext zurückgesetzt — neues Gespräch)")
            continue

        # Eingabe im richtigen Format an Kontext anhängen
        context = format_input(user_input, context, fmt, tokenizer)

        # Tokenisieren mit Kontext-Limit
        inputs = tokenizer(
            context,
            return_tensors="pt",
            truncation=True,
            max_length=max_context,
            padding=False,
        ).to(device)

        context_length = inputs["input_ids"].shape[1]

        if context_length >= max_context:
            print("(Kontext wird gekürzt — ältere Teile vergessen...)")

        # Attention Mask explizit erstellen
        # 1 = Token beachten, 0 = ignorieren (Padding)
        # Da wir kein Padding verwenden, sind alle Tokens 1
        attention_mask = torch.ones_like(inputs["input_ids"])

        # Text generieren
        with torch.no_grad():
            outputs = model.generate(
                inputs["input_ids"],
                attention_mask=attention_mask,
                max_new_tokens=100,
                do_sample=True,
                temperature=0.8,
                top_p=0.95,
                pad_token_id=tokenizer.eos_token_id,
                eos_token_id=tokenizer.eos_token_id,
            )

        # Nur neue Tokens extrahieren
        new_token_ids = outputs[0][inputs["input_ids"].shape[1]:]
        response = tokenizer.decode(new_token_ids, skip_special_tokens=True)

        # Antwort zum Kontext hinzufügen
        context += format_response(response, fmt, tokenizer)

        print(f"\nModell: {response}")
        print(f"(Kontext: {context_length}/{max_context} Tokens)")


# =============================================================================
# MODELLAUSWAHL
# =============================================================================

def select_model():
    """Interaktive Modellauswahl beim Programmstart."""

    print("\n" + "="*60)
    print("CHAT LLM - MODELLAUSWAHL")
    print("="*60)
    print("Verfügbare Modelle:\n")
    for key, config in MODELS.items():
        print(f"  [{key}] {config['label']}")
    print("="*60)
    print("\nHinweis: Beim ersten Aufruf wird das Modell heruntergeladen.")
    print("Danach startet es sofort aus dem Cache.")

    while True:
        choice = input("\nModell wählen (1-7): ").strip()

        if choice in MODELS:
            model_config = MODELS[choice]
            print(f"\n-> Gewählt: {model_config['label'].strip()}")

            model, tokenizer, device = load_model(model_config)
            chat_loop(model, tokenizer, device, model_config)
            return

        print("Ungültige Eingabe, bitte 1-7 eingeben.")


if __name__ == "__main__":
    select_model()
