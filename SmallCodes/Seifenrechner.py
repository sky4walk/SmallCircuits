# --- Seifenrechner in Python (mit großer Ölliste & Wasserberechnung) ---

SAP_VALUES = {
    # Öle & pflanzliche Fette
    "olive": 0.134,
    "coconut": 0.183,
    "coconut_76": 0.183,
    "coconut_92": 0.183,
    "palm": 0.141,
    "palm_kernel": 0.247,
    "shea": 0.128,
    "cocoa_butter": 0.137,
    "mango_butter": 0.135,
    "babassu": 0.175,
    "avocado": 0.133,
    "almond": 0.136,
    "apricot": 0.136,
    "grapeseed": 0.135,
    "sunflower": 0.135,
    "high_oleic_sunflower": 0.138,
    "rapeseed": 0.133,
    "canola": 0.133,
    "castor": 0.128,
    "hemp": 0.136,
    "jojoba": 0.069,
    "linseed": 0.135,
    "safflower": 0.135,
    "sesame": 0.133,
    "rice_bran": 0.128,
    "macadamia": 0.139,
    "hazelnut": 0.136,
    "peanut": 0.136,
    "walnut": 0.136,
    "corn": 0.136,
    "argan": 0.136,

    # Tierische Fette
    "lard": 0.138,
    "tallow": 0.141,
    "duck_fat": 0.138,

    # Spezialfette
    "lanolin": 0.074,
    "beeswax": 0.069,
}

def calculate_lye(oils, superfat=5, koh=False):
    total_naoh = 0.0
    for oil, amount in oils.items():
        if oil not in SAP_VALUES:
            raise ValueError(f"Verseifungszahl für '{oil}' nicht vorhanden.")
        total_naoh += SAP_VALUES[oil] * amount

    total_naoh *= (100 - superfat) / 100

    if koh:
        return total_naoh * 1.403  # NaOH → KOH Umrechnungsfaktor
    return total_naoh


def calculate_water(lye_amount, concentration):
    concentration = concentration / 100
    total_solution = lye_amount / concentration
    return total_solution - lye_amount


def main():
    print("🧼 Seifenrechner (NaOH / KOH) mit großer Ölliste")

    oils = {}
    print("\nGib deine Öle ein (Enter für Ende).")
    print("Verfügbare Öle:", ", ".join(SAP_VALUES.keys()))

    while True:
        oil = input("\nÖlname: ").strip().lower()
        if oil == "":
            break
        if oil not in SAP_VALUES:
            print("Öl nicht in Datenbank.")
            continue

        try:
            amount = float(input(f"Menge von {oil} in g: "))
        except ValueError:
            print("Bitte eine gültige Zahl eingeben.")
            continue

        oils[oil] = oils.get(oil, 0) + amount

    superfat = float(input("\nÜberfettung in %: "))
    lye_type = input("Laugenart (naoh/koh): ").strip().lower()
    use_koh = lye_type == "koh"
    concentration = float(input("Laugekonzentration (%) z.B. 30–33: "))

    lye = calculate_lye(oils, superfat, koh=use_koh)
    water = calculate_water(lye, concentration)

    print("\n--- Ergebnis ---")
    print("Ölmischung:", oils)
    print(f"Überfettung: {superfat}%")
    print(f"Laugekonzentration: {concentration}%")
    print(f"{'KOH' if use_koh else 'NaOH'}-Menge: {lye:.2f} g")
    print(f"Wassermenge: {water:.2f} g")
    print(f"Gesamt-Lösung: {lye + water:.2f} g")


if __name__ == "__main__":
    main()
