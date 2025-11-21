import re
import sys
import random

def read_text_file(filepath):
    with open(filepath, "r", encoding="utf-8") as file:
        return file.read()

def tokenize(text):
    return re.findall(r'\w+', text.lower())

def generate_ngrams(words, n):
    return [tuple(words[i:i+n]) for i in range(len(words) - n + 1)]

def ngram_frequencies(words, n):
    freq = {}
    for gram in generate_ngrams(words, n):
        freq[gram] = freq.get(gram, 0) + 1
    return freq

def predict_candidates(frequencies, context):
    candidates = {}
    for gram, count in frequencies.items():
        if gram[:-1] == context:
            next_word = gram[-1]
            candidates[next_word] = candidates.get(next_word, 0) + count
    return candidates

def choose_weighted(candidates):
    words = list(candidates.keys())
    weights = list(candidates.values())
    return random.choices(words, weights=weights, k=1)[0]

def generate_sentence_random(words, frequencies, n, max_length=20):
    start_index = random.randint(0, len(words) - n)
    context = tuple(words[start_index:start_index + n - 1])
    sentence = list(context)

    for _ in range(max_length):
        candidates = predict_candidates(frequencies, tuple(sentence[-(n-1):]))
        if not candidates:
            break
        sentence.append(choose_weighted(candidates))

    return " ".join(sentence)

def generate_sentence_with_start(start_text, frequencies, n, max_length=20):
    tokens = tokenize(start_text)

    if len(tokens) < n - 1:
        print(f"Fehler: Für N={n} müssen mindestens {n-1} Startwörter eingegeben werden.")
        return None

    context = tuple(tokens[-(n-1):])
    sentence = tokens[:]  # komplette Starttokens übernehmen

    for _ in range(max_length):
        candidates = predict_candidates(frequencies, tuple(sentence[-(n-1):]))
        if not candidates:
            break
        sentence.append(choose_weighted(candidates))

    return " ".join(sentence)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Benutzung: python ngram.py <dateiname> <n>")
        sys.exit(1)

    filepath = sys.argv[1]

    try:
        n = int(sys.argv[2])
        if n < 2:
            raise ValueError
    except ValueError:
        print("Fehler: <n> muss eine ganze Zahl >= 2 sein.")
        sys.exit(1)

    text = read_text_file(filepath)
    words = tokenize(text)
    freq = ngram_frequencies(words, n)

    print("\n=== Satzgenerierung ===")
    start_text = input(f"Startsatz eingeben (oder Enter für zufälligen Start): ").strip()

    if start_text:
        result = generate_sentence_with_start(start_text, freq, n)
    else:
        result = generate_sentence_random(words, freq, n)

    print("\nGenerierter Satz:")
    print(result)
