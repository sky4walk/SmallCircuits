import random

# === Strategien ===
def strategy_manual(player_number):
    while True:
        choice = input(f"Spieler {player_number}, wähle (C = zustimmen / D = verraten / q = beenden): ").strip().lower()
        if choice in ["c", "d", "q"]:
            return choice
        print("Ungültige Eingabe. Bitte C, D oder q eingeben.")

def strategy_tit_for_tat(last_opponent):
    if last_opponent is None:
        return "c"
    return last_opponent

def strategy_always_cooperate(_):
    return "c"

def strategy_always_defect(_):
    return "d"

def strategy_random(_):
    return random.choice(["c", "d"])

def strategy_grim_trigger(last_opponent, state={}):
    if 'defected' not in state:
        state['defected'] = False
    if last_opponent == 'd':
        state['defected'] = True
    return 'd' if state['defected'] else 'c'

def strategy_tit_for_two_tats(last_opponent, state={}):
    if 'last_two' not in state:
        state['last_two'] = []
    if last_opponent is not None:
        state['last_two'].append(last_opponent)
        if len(state['last_two']) > 2:
            state['last_two'].pop(0)
    if state['last_two'] == ['d', 'd']:
        return 'd'
    return 'c'

def strategy_pavlov(last_self, last_opponent, state={}):
    if last_self is None or last_opponent is None:
        state['last_move'] = 'c'
        return 'c'
    if (last_self == 'c' and last_opponent == 'c') or (last_self == 'd' and last_opponent == 'd'):
        state['last_move'] = last_self
    else:
        state['last_move'] = 'd' if last_self == 'c' else 'c'
    return state['last_move']

# === Punktevergabe ===
def score_round(p1, p2):
    if p1 == 'c' and p2 == 'c':
        return 3, 3
    elif p1 == 'd' and p2 == 'c':
        return 5, 0
    elif p1 == 'c' and p2 == 'd':
        return 0, 5
    else:
        return 1, 1

# === Alle Strategien für Turnier und Auswahl ===
strategies_list = [
    ("Tit-for-Tat", strategy_tit_for_tat),
    ("Always Cooperate", strategy_always_cooperate),
    ("Always Defect", strategy_always_defect),
    ("Random", strategy_random),
    ("Grim Trigger", strategy_grim_trigger),
    ("Tit-for-Two-Tats", strategy_tit_for_two_tats),
    ("Pavlov", strategy_pavlov)
]

# === Auswahl einer Strategie (inklusive manuell) ===
def choose_strategy(player_number):
    print(f"\nWähle eine Strategie für Spieler {player_number}:")
    print("1: Manuell spielen")
    for i, (name, _) in enumerate(strategies_list):
        print(f"{i+2}: {name}")
    while True:
        s = input("Eingabe: ").strip()
        if s == "1":
            return "Manuell", lambda last1, last2=None: strategy_manual(player_number)
        elif s in map(str, range(2, len(strategies_list)+2)):
            name, func = strategies_list[int(s)-2]
            return name, func
        else:
            print("Ungültige Eingabe, bitte erneut versuchen.")

# === Abfrage der Rundenzahl ===
def choose_rounds():
    while True:
        r = input("\nWieviele Runden sollen gespielt werden? ").strip()
        if r.isdigit() and int(r) > 0:
            return int(r)
        print("Bitte eine gültige positive Zahl eingeben.")

# === Spiel zwischen zwei Strategien/Spielern ===
def play_game(name1, strat1, name2, strat2, rounds):
    score1 = 0
    score2 = 0
    last1, last2 = None, None
    state1, state2 = {}, {}

    for r in range(1, rounds+1):
        print(f"\n--- Runde {r} ---")
        # Zug Spieler 1
        if name1 == "Manuell":
            move1 = strat1(last2)
            if move1 == 'q':
                print("\nSpieler 1 hat das Spiel beendet.")
                break
        else:
            if name1 == "Pavlov":
                move1 = strat1(last1, last2, state1)
            elif name1 in ["Grim Trigger", "Tit-for-Two-Tats"]:
                move1 = strat1(last2, state1)
            else:
                move1 = strat1(last2)

        # Zug Spieler 2
        if name2 == "Manuell":
            move2 = strat2(last1)
            if move2 == 'q':
                print("\nSpieler 2 hat das Spiel beendet.")
                break
        else:
            if name2 == "Pavlov":
                move2 = strat2(last2, last1, state2)
            elif name2 in ["Grim Trigger", "Tit-for-Two-Tats"]:
                move2 = strat2(last1, state2)
            else:
                move2 = strat2(last1)

        print(f"Spieler 1 ({name1}): {move1.upper()} | Spieler 2 ({name2}): {move2.upper()}")
        s1, s2 = score_round(move1, move2)
        score1 += s1
        score2 += s2
        print(f"Punkte: Spieler 1 +{s1}, Spieler 2 +{s2}")
        print(f"Gesamtpunkte: Spieler 1 = {score1}, Spieler 2 = {score2}")
        last1, last2 = move1, move2

    print("\n=== Spiel beendet ===")
    print(f"Endstand: Spieler 1 = {score1}, Spieler 2 = {score2}")

# === Turniermodus ===
def tournament(rounds):
    total_scores = {name:0 for name, _ in strategies_list}
    print(f"\n--- Turniermodus: {rounds} Runden pro Spiel ---")
    for i in range(len(strategies_list)):
        for j in range(i+1, len(strategies_list)):
            name1, strat1 = strategies_list[i]
            name2, strat2 = strategies_list[j]
            s1, s2 = play_game_tournament(name1, strat1, name2, strat2, rounds)
            total_scores[name1] += s1
            total_scores[name2] += s2
            print(f"{name1} vs {name2}: {s1}-{s2}")
    print("\n=== Turnierergebnis: Gesamtpunkte ===")
    for name, score in total_scores.items():
        print(f"{name}: {score} Punkte")

def play_game_tournament(name1, strat1, name2, strat2, rounds):
    score1 = 0
    score2 = 0
    last1, last2 = None, None
    state1, state2 = {}, {}
    for _ in range(rounds):
        # Spieler 1
        if name1 == "Pavlov":
            move1 = strat1(last1, last2, state1)
        elif name1 in ["Grim Trigger", "Tit-for-Two-Tats"]:
            move1 = strat1(last2, state1)
        else:
            move1 = strat1(last2)
        # Spieler 2
        if name2 == "Pavlov":
            move2 = strat2(last2, last1, state2)
        elif name2 in ["Grim Trigger", "Tit-for-Two-Tats"]:
            move2 = strat2(last1, state2)
        else:
            move2 = strat2(last1)
        s1, s2 = score_round(move1, move2)
        score1 += s1
        score2 += s2
        last1, last2 = move1, move2
    return score1, score2

# === Hauptprogramm ===
def main():
    print("=== Gefangenendilemma Simulator ===")
    print("1: Manuelles Spiel")
    print("2: Turniermodus")
    while True:
        mode = input("Wähle Modus (1 oder 2): ").strip()
        if mode == "1":
            # Manuelles Spiel
            name1, strat1 = choose_strategy(1)
            name2, strat2 = choose_strategy(2)
            rounds = choose_rounds()
            play_game(name1, strat1, name2, strat2, rounds)
            break
        elif mode == "2":
            rounds = choose_rounds()
            tournament(rounds)
            break
        else:
            print("Ungültige Eingabe, bitte 1 oder 2 eingeben.")

main()
