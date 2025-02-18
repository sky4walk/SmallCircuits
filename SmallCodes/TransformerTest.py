import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

# Modell und Tokenizer laden
model_name = "gpt2"  # oder ein anderes Modell wie "EleutherAI/gpt-j-6B"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)

# Auf GPU verschieben (falls verfügbar)
if torch.cuda.is_available() : 
    device = "cuda" 
else:
    device = "cpu"
model = model.to(device)

# Beispiel-Textgenerierung
input_text = "What is artificial intelligence?"
inputs = tokenizer(input_text, return_tensors="pt").to(device)
outputs = model.generate(inputs["input_ids"], max_length=50, num_return_sequences=1)
print(tokenizer.decode(outputs[0], skip_special_tokens=True))