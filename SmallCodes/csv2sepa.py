"""
csv_to_sepa.py
--------------
Converts a structured CSV file into a SEPA Direct Debit XML (pain.008.003.02).

CSV format:
  Section 1 — Creditor block (preceded by "#creditor"):
    creditor_name, creditor_iban, creditor_bic, creditor_id, collection_date

  Section 2 — Debitor block (preceded by "#debitors"):
    Mitglieds-Nr.,Name,Vorname,Ansprechpart-ner bei Firmen,Mitglied seit,Zahler ab,
    geboren,Straße,PLZ,Ort,Adresse geändert seit Beitritt,Telefon,Handy,e-mail,
    Zustimmung Fotos,Änderung Bank seit Beitritt?,abweichender Zahler,
    Mandats-datum,IBAN,BIC,Bank,Betrag,Ausgetreten
    Zeilen ohne IBAN oder mit Ausgetreten-Datum werden übersprungen.

Usage:
  python csv_to_sepa.py input.csv [output.xml]
"""

import csv
import sys
import uuid
import re
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from xml.etree.ElementTree import Element, SubElement, ElementTree, indent
from pathlib import Path

try:
    from schwifty import IBAN
    SCHWIFTY_AVAILABLE = True
except ImportError:
    SCHWIFTY_AVAILABLE = False


# ── Constants ────────────────────────────────────────────────────────────────

XSI_NAMESPACE = "http://www.w3.org/2001/XMLSchema-instance"

PAIN_VERSIONS = {
    "pain.008.003.02": {
        "namespace":      "urn:iso:std:iso:20022:tech:xsd:pain.008.003.02",
        "schema_location":"urn:iso:std:iso:20022:tech:xsd:pain.008.003.02 pain.008.003.02.xsd",
    },
    "pain.008.001.02": {
        "namespace":      "urn:iso:std:iso:20022:tech:xsd:pain.008.001.02",
        "schema_location":"urn:iso:std:iso:20022:tech:xsd:pain.008.001.02 pain.008.001.02.xsd",
    },
}
VALID_PAIN_VERSIONS = set(PAIN_VERSIONS.keys())

VALID_SEQUENCE_TYPES = {"FRST", "RCUR", "OOFF", "FNAL"}

# Minimum lead days per sequence type (TARGET2 banking days, simplified)
LEAD_DAYS = {"FRST": 5, "RCUR": 2, "OOFF": 5, "FNAL": 2}


# ── Validation helpers ────────────────────────────────────────────────────────

class ValidationError(Exception):
    pass


def validate_iban(iban_str: str, label: str) -> str:
    iban_str = iban_str.strip().replace(" ", "").upper()
    if SCHWIFTY_AVAILABLE:
        try:
            return str(IBAN(iban_str))
        except Exception as e:
            raise ValidationError(f"{label}: ungültige IBAN '{iban_str}' – {e}")
    else:
        # Basic structural check (length + numeric mod-97)
        if not re.fullmatch(r"[A-Z]{2}[0-9]{2}[A-Z0-9]{1,30}", iban_str):
            raise ValidationError(f"{label}: IBAN '{iban_str}' hat ungültiges Format")
        rearranged = iban_str[4:] + iban_str[:4]
        numeric = "".join(str(ord(c) - 55) if c.isalpha() else c for c in rearranged)
        if int(numeric) % 97 != 1:
            raise ValidationError(f"{label}: IBAN '{iban_str}' hat ungültige Prüfziffer")
    return iban_str


def validate_bic(bic_str: str, label: str) -> str:
    bic_str = bic_str.strip().upper()
    if not re.fullmatch(r"[A-Z]{6}[A-Z0-9]{2}([A-Z0-9]{3})?", bic_str):
        raise ValidationError(f"{label}: ungültiger BIC '{bic_str}'")
    return bic_str


def validate_date(date_str: str, label: str) -> date:
    date_str = date_str.strip()
    for fmt in ("%Y-%m-%d", "%d.%m.%Y"):
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    raise ValidationError(f"{label}: Datum '{date_str}' muss im Format YYYY-MM-DD oder DD.MM.YYYY sein")


def validate_amount(amount_str: str, label: str) -> Decimal:
    try:
        amount = Decimal(amount_str.strip().replace(",", "."))
        if amount <= 0:
            raise ValidationError(f"{label}: Betrag muss > 0 sein")
        return amount.quantize(Decimal("0.01"))
    except InvalidOperation:
        raise ValidationError(f"{label}: ungültiger Betrag '{amount_str}'")


def validate_creditor_id(cid: str, label: str) -> str:
    cid = cid.strip()
    # German Gläubiger-ID pattern: DE + 2 digits + ZZZ + 11 alphanumeric
    if not re.fullmatch(r"[A-Z]{2}[0-9]{2}[A-Z0-9]{3}[A-Z0-9]{1,28}", cid):
        raise ValidationError(
            f"{label}: Gläubiger-ID '{cid}' hat unerwartetes Format "
            f"(erwartet z.B. DE98ZZZ09999999999)"
        )
    return cid


# ── CSV parser ────────────────────────────────────────────────────────────────

def parse_csv(path: str, verbose: bool = False) -> tuple[dict, list[dict]]:
    """
    Returns (creditor_dict, [debitor_dict, ...]).
    Raises ValidationError on any problem.
    """
    with open(path, newline="", encoding="utf-8-sig") as fh:
        raw_lines = fh.readlines()

    creditor_lines: list[str] = []
    debitor_lines:  list[str] = []
    section = None

    for line in raw_lines:
        stripped = line.strip()
        if stripped.lower() == "#creditor":
            section = "creditor"
            continue
        if stripped.lower() == "#debitors":
            section = "debitors"
            continue
        if stripped == "":
            continue
        # Kommentarzeilen: beginnen mit # aber sind keine Sektions-Marker
        if stripped.startswith("#") and stripped.lower() not in ("#creditor", "#debitors"):
            continue
        if section == "creditor":
            creditor_lines.append(line)
        elif section == "debitors":
            debitor_lines.append(line)

    if not creditor_lines:
        raise ValidationError("CSV enthält keinen #creditor Block")
    if not debitor_lines:
        raise ValidationError("CSV enthält keinen #debitors Block")

    # ── Parse creditor ──
    cred_reader = list(csv.DictReader(creditor_lines))
    if len(cred_reader) != 1:
        raise ValidationError(
            f"#creditor Block muss genau eine Datenzeile haben (gefunden: {len(cred_reader)})"
        )
    raw_c = {k.strip(): v.strip() for k, v in cred_reader[0].items()}

    required_c = ["creditor_name", "creditor_iban", "creditor_bic", "creditor_id", "collection_date"]
    for field in required_c:
        if field not in raw_c or not raw_c[field]:
            raise ValidationError(f"Pflichtfeld '{field}' fehlt im #creditor Block")

    pain_version = raw_c.get("pain_version", "pain.008.003.02").strip()
    if pain_version not in VALID_PAIN_VERSIONS:
        raise ValidationError(
            f"Unbekannte pain_version '{pain_version}' – erlaubt: {', '.join(sorted(VALID_PAIN_VERSIONS))}"
        )

    creditor = {
        "name":            raw_c["creditor_name"],
        "iban":            validate_iban(raw_c["creditor_iban"], "Gläubiger IBAN"),
        "bic":             validate_bic(raw_c["creditor_bic"],   "Gläubiger BIC"),
        "creditor_id":     validate_creditor_id(raw_c["creditor_id"], "Gläubiger-ID"),
        "collection_date": date.today() + __import__("datetime").timedelta(days=7),
        "pain_version":    pain_version,
    }

    if verbose:
        print("\n[Gläubiger]")
        print(f"  Name:           {creditor['name']}")
        print(f"  IBAN:           {creditor['iban']}")
        print(f"  BIC:            {creditor['bic']}")
        print(f"  Gläubiger-ID:   {creditor['creditor_id']}")
        print(f"  Einzugsdatum:   {creditor['collection_date']}")
        print(f"  pain_version:   {creditor['pain_version']}")

    # ── Parse debitors (Vereinsmitglieder-Format) ──
    deb_reader = list(csv.DictReader(debitor_lines))
    if not deb_reader:
        raise ValidationError("Keine Schuldner-Zeilen gefunden")

    debitors  = []
    skipped   = []

    if verbose:
        print(f"\n[Schuldner] – lese {len(deb_reader)} Zeilen...")

    for i, row in enumerate(deb_reader, start=1):
        row = {k.strip(): v.strip() for k, v in row.items() if k}

        # Name zusammensetzen
        vorname    = row.get("Vorname", "").strip()
        nachname   = row.get("Name", "").strip()
        full_name  = f"{vorname} {nachname}".strip() or f"Zeile {i}"
        label      = f"Zeile {i} ('{full_name}')"

        # Ausgetretene Mitglieder überspringen
        ausgetreten = row.get("Ausgetreten", "").strip()
        if ausgetreten:
            msg = f"  ⏭  {label} – ausgetreten am {ausgetreten}"
            skipped.append(msg)
            if verbose: print(msg)
            continue

        # Kein IBAN → überspringen
        iban_raw = row.get("IBAN", "").strip()
        if not iban_raw:
            msg = f"  ⏭  {label} – keine IBAN vorhanden"
            skipped.append(msg)
            if verbose: print(msg)
            continue

        # Ungültige IBAN → überspringen
        try:
            iban_validated = validate_iban(iban_raw, label)
        except ValidationError as e:
            short_msg = f"  ⚠️  {label} – ungültige IBAN '{iban_raw}', wird übersprungen"
            verbose_msg = f"{short_msg}: {e}"
            skipped.append(short_msg)
            print(verbose_msg if verbose else short_msg)
            continue

        # Pflichtfelder prüfen
        mandate_id_raw  = row.get("Mitglieds-Nr.", "").strip()
        mandate_date_raw = row.get("Mandats-datum", "").strip()
        bic_raw         = row.get("BIC", "").strip()
        # Bankname aus "Bank"-Spalte ist kein BIC – nur echte BIC-artige Werte übernehmen
        if bic_raw and not re.fullmatch(r"[A-Za-z]{6}[A-Za-z0-9]{2}([A-Za-z0-9]{3})?", bic_raw):
            if verbose:
                print(f"    ⚠️  '{bic_raw}' ist kein gültiger BIC und wird ignoriert (→ NOTPROVIDED)")
            bic_raw = ""  # als leer behandeln
        amount_raw      = row.get("Betrag", "").strip()

        if not mandate_id_raw:
            raise ValidationError(f"{label}: Pflichtfeld 'Mitglieds-Nr.' fehlt")
        if not mandate_date_raw:
            raise ValidationError(f"{label}: Pflichtfeld 'Mandats-datum' fehlt")
        # BIC ist optional (seit 2016 innerhalb der EU nicht mehr zwingend)
        if not amount_raw:
            raise ValidationError(f"{label}: Pflichtfeld 'Betrag' fehlt")

        entry = {
            "name":          full_name,
            "iban":          iban_validated,
            "bic":           validate_bic(bic_raw, f"{label} BIC") if bic_raw else "",
            "amount":        validate_amount(amount_raw,     label),
            "mandate_id":    mandate_id_raw,
            "mandate_date":  validate_date(mandate_date_raw, f"{label} Mandats-datum"),
            "sequence_type": "RCUR",
            "description":   "Jahresbeitrag",
        }
        if verbose:
            print(f"\n  [Zeile {i}] {full_name}")
            print(f"    Mitglieds-Nr.:  {entry['mandate_id']}")
            print(f"    IBAN:           {entry['iban']}")
            print(f"    BIC:            {entry['bic'] or '(leer → NOTPROVIDED)'}")
            print(f"    Betrag:         {entry['amount']} EUR")
            print(f"    Mandats-datum:  {entry['mandate_date']}")
            print(f"    Sequenztyp:     {entry['sequence_type']}")
        debitors.append(entry)

    if skipped and not verbose:
        print(f"  Übersprungen ({len(skipped)} Einträge):")
        for s in skipped:
            print(s)
    elif skipped and verbose:
        print(f"\n  → {len(skipped)} Einträge übersprungen.")

    if not debitors:
        raise ValidationError("Keine gültigen Schuldner-Einträge nach Filterung gefunden")

    return creditor, debitors


# ── XML builder ───────────────────────────────────────────────────────────────

def build_xml(creditor: dict, debitors: list[dict]) -> ElementTree:
    now_str       = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    msg_id        = f"MSG-{uuid.uuid4().hex[:16].upper()}"
    total_amount  = sum(d["amount"] for d in debitors)
    nb_of_txs     = len(debitors)
    collection_dt = creditor["collection_date"].strftime("%Y-%m-%d")

    # Group debitors by sequence_type → each gets its own PmtInf block
    from collections import defaultdict
    groups: dict[str, list] = defaultdict(list)
    for d in debitors:
        groups[d["sequence_type"]].append(d)

    # ── Root ──
    version_cfg = PAIN_VERSIONS[creditor["pain_version"]]
    root = Element(
        "Document",
        attrib={
            "xmlns":              version_cfg["namespace"],
            "xmlns:xsi":          XSI_NAMESPACE,
            "xsi:schemaLocation": version_cfg["schema_location"],
        },
    )
    cdi = SubElement(root, "CstmrDrctDbtInitn")

    # ── Group Header ──
    grp = SubElement(cdi, "GrpHdr")
    SubElement(grp, "MsgId").text       = msg_id
    SubElement(grp, "CreDtTm").text     = now_str
    SubElement(grp, "NbOfTxs").text     = str(nb_of_txs)
    SubElement(grp, "CtrlSum").text     = f"{total_amount:.2f}"
    initg = SubElement(grp, "InitgPty")
    SubElement(initg, "Nm").text        = creditor["name"]

    # ── Payment Information (one per sequence type) ──
    for seq_type, txs in groups.items():
        grp_amount = sum(d["amount"] for d in txs)
        pmt_id     = f"PMT-{seq_type}-{uuid.uuid4().hex[:8].upper()}"

        pmt = SubElement(cdi, "PmtInf")
        SubElement(pmt, "PmtInfId").text    = pmt_id
        SubElement(pmt, "PmtMtd").text      = "DD"
        SubElement(pmt, "NbOfTxs").text     = str(len(txs))
        SubElement(pmt, "CtrlSum").text     = f"{grp_amount:.2f}"

        svc = SubElement(pmt, "PmtTpInf")
        lvl = SubElement(svc, "SvcLvl")
        SubElement(lvl, "Cd").text          = "SEPA"
        lct = SubElement(svc, "LclInstrm")
        SubElement(lct, "Cd").text          = "CORE"
        SubElement(svc, "SeqTp").text       = seq_type

        SubElement(pmt, "ReqdColltnDt").text = collection_dt

        # Creditor
        cdtr = SubElement(pmt, "Cdtr")
        SubElement(cdtr, "Nm").text         = creditor["name"]
        cdtr_acct = SubElement(pmt, "CdtrAcct")
        cdtr_id   = SubElement(cdtr_acct, "Id")
        SubElement(cdtr_id, "IBAN").text    = creditor["iban"]
        cdtr_agt  = SubElement(pmt, "CdtrAgt")
        cdtr_fi   = SubElement(cdtr_agt, "FinInstnId")
        SubElement(cdtr_fi, "BIC").text     = creditor["bic"]

        # Creditor scheme ID (Gläubiger-ID)
        scheme = SubElement(pmt, "CdtrSchmeId")
        scheme_id = SubElement(scheme, "Id")
        prvt_id   = SubElement(scheme_id, "PrvtId")
        othr      = SubElement(prvt_id, "Othr")
        SubElement(othr, "Id").text         = creditor["creditor_id"]
        schme_nm  = SubElement(othr, "SchmeNm")
        SubElement(schme_nm, "Prtry").text  = "SEPA"

        # ── Direct Debit Transaction Info (one per debitor) ──
        for tx in txs:
            e2e_id = f"E2E-{tx['mandate_id']}"

            ddt = SubElement(pmt, "DrctDbtTxInf")

            pmt_id_elem = SubElement(ddt, "PmtId")
            SubElement(pmt_id_elem, "EndToEndId").text = e2e_id[:35]  # max 35 chars

            amt = SubElement(ddt, "InstdAmt", attrib={"Ccy": "EUR"})
            amt.text = f"{tx['amount']:.2f}"

            # Mandate
            ddt_tx      = SubElement(ddt, "DrctDbtTx")
            mndt        = SubElement(ddt_tx, "MndtRltdInf")
            SubElement(mndt, "MndtId").text   = tx["mandate_id"]
            SubElement(mndt, "DtOfSgntr").text = tx["mandate_date"].strftime("%Y-%m-%d")

            # Debitor agent (BIC optional)
            dbtr_agt = SubElement(ddt, "DbtrAgt")
            dbtr_fi  = SubElement(dbtr_agt, "FinInstnId")
            if tx["bic"]:
                SubElement(dbtr_fi, "BIC").text = tx["bic"]
            else:
                SubElement(dbtr_fi, "Othr").text = "NOTPROVIDED"  # SEPA-konformer Platzhalter

            # Debitor
            dbtr        = SubElement(ddt, "Dbtr")
            SubElement(dbtr, "Nm").text       = tx["name"]
            dbtr_acct   = SubElement(ddt, "DbtrAcct")
            dbtr_id_el  = SubElement(dbtr_acct, "Id")
            SubElement(dbtr_id_el, "IBAN").text = tx["iban"]

            # Remittance info
            rmt         = SubElement(ddt, "RmtInf")
            SubElement(rmt, "Ustrd").text     = tx["description"][:140]  # max 140 chars

    indent(root, space="  ")
    return ElementTree(root)



# ── Example CSV generator ─────────────────────────────────────────────────────

EXAMPLE_CSV = """\
#creditor
# Gläubigerdaten – diese Felder beschreiben dein Unternehmen als Einzieher
# creditor_name    – Name deines Unternehmens (wie auf dem Bankkonto hinterlegt)
# creditor_iban    – IBAN deines Geschäftskontos, auf das eingezogen wird
# creditor_bic     – BIC deiner Bank
# creditor_id      – Gläubiger-ID (beantragen bei der Deutschen Bundesbank)
# collection_date  – gewünschtes Einzugsdatum (YYYY-MM-DD, mind. 5 Bankarbeitstage in der Zukunft)
# pain_version     – XML-Format: pain.008.003.02 (Standard) oder pain.008.001.02 (optional)
creditor_name,creditor_iban,creditor_bic,creditor_id,collection_date,pain_version
Mein Unternehmen GmbH,DE12500105170648489890,INGDDEFFXXX,DE98ZZZ09999999999,2025-06-01,pain.008.003.02

#debitors
# Mitgliederdaten – eine Zeile pro Mitglied
# Mitglieds-Nr.               – wird als Mandatsreferenz verwendet
# Name / Vorname              – werden zu vollem Namen zusammengesetzt
# Mandats-datum               – Datum der SEPA-Mandatsunterschrift (YYYY-MM-DD)
# IBAN / BIC                  – Kontodaten des Zahlers
# Betrag                      – Jahresbeitrag in EUR (Dezimalpunkt, z.B. 49.00)
# Ausgetreten                 – wenn gefüllt, wird das Mitglied übersprungen
# Alle anderen Spalten werden eingelesen aber für den Einzug nicht verwendet
Mitglieds-Nr.,Name,Vorname,Ansprechpart-ner bei Firmen,Mitglied seit,Zahler ab,geboren,Straße,PLZ,Ort,Adresse geändert seit Beitritt,Telefon,Handy,e-mail,Zustimmung Fotos,Änderung Bank seit Beitritt?,abweichender Zahler,Mandats-datum,IBAN,BIC,Bank,Betrag,Ausgetreten
1001,Mustermann,Max,,2020-01-01,,1985-03-12,Musterstraße 1,12345,Musterstadt,,0911123456,,max@example.de,Ja,Nein,,2020-01-01,DE89370400440532013000,COBADEFFXXX,Commerzbank,49.00,
1002,Musterfrau,Erika,,2019-06-01,,1990-07-22,Beispielweg 5,54321,Beispielort,,,,erika@example.de,Nein,Nein,,2019-06-01,DE75512108001245126199,SSKMDEMMXXX,Sparkasse,49.00,
1003,Schmidt,Hans,,2018-03-15,,1978-11-05,Testgasse 9,99999,Teststadt,,,,,,Nein,,2018-03-15,,,,,2023-05-01
1004,Bauer,Anna,,2021-09-01,,1995-02-28,Hauptstr. 3,10115,Berlin,,030987654,,anna@example.de,Ja,Nein,,2021-09-01,DE91100000000123456789,BELADEBEXXX,Berliner Bank,49.00,
"""

def create_example_csv(path: str) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(EXAMPLE_CSV)


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        default_input = "input.csv"
        if Path(default_input).exists():
            print(f"📂 Keine Argumente – verwende gefundene {default_input}")
            input_path  = default_input
            output_path = "output.xml"
        else:
            create_example_csv("input.csv")
            print(f"📝 Keine input.csv gefunden – Beispieldatei als input.csv erstellt")
            print("   Passe die Daten an und starte erneut mit: python csv_to_sepa.py")
            sys.exit(0)
    else:
        if sys.argv[1] == "--example":
            example_path = "input_example.csv"
            create_example_csv(example_path)
            print(f"📝 Beispieldatei erstellt: {example_path}")
            print("   Aufruf: python csv_to_sepa.py input_example.csv [output.xml]")
            sys.exit(0)

        args = [a for a in sys.argv[1:] if a != "--verbose"]
        input_path  = args[0] if args else "input.csv"
        output_path = args[1] if len(args) > 1 else "output.xml"

    verbose = "--verbose" in sys.argv

    print(f"📂 Lese CSV: {input_path}")

    errors = []
    try:
        creditor, debitors = parse_csv(input_path, verbose=verbose)
    except ValidationError as e:
        print(f"\n❌ Validierungsfehler: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print(f"\n❌ Datei nicht gefunden: {input_path}")
        sys.exit(1)

    print(f"✅ Gläubiger:  {creditor['name']} ({creditor['iban']})")
    print(f"✅ Format:     {creditor['pain_version']}")
    print(f"✅ Schuldner:  {len(debitors)} Einträge")
    print(f"✅ Gesamtbetrag: {sum(d['amount'] for d in debitors):.2f} EUR")
    print(f"✅ Einzugsdatum: {creditor['collection_date']}")

    # ── Vorlaufzeit prüfen ──
    today = date.today()
    col_date = creditor["collection_date"]
    seq_types = {d["sequence_type"] for d in debitors}
    required_days = max(LEAD_DAYS[s] for s in seq_types)
    delta = (col_date - today).days

    if col_date <= today:
        print(f"\n⚠️  Warnung: Einzugsdatum {col_date} liegt in der Vergangenheit oder ist heute!")
    elif delta < required_days:
        print(f"\n⚠️  Warnung: Einzugsdatum {col_date} unterschreitet die empfohlene Vorlaufzeit.")
        print(f"   Heute ist {today}, benötigt werden mind. {required_days} Kalendertage → frühestens {today + __import__('datetime').timedelta(days=required_days)}.")
        print(f"   Hinweis: Bankarbeitstage (ohne Wochenenden/Feiertage) werden hier nicht berechnet – bitte manuell prüfen.")

    tree = build_xml(creditor, debitors)

    with open(output_path, "w", encoding="utf-8") as fh:
        fh.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        tree.write(fh, encoding="unicode", xml_declaration=False)

    print(f"\n🎉 XML erfolgreich erstellt: {output_path}")


if __name__ == "__main__":
    main()
