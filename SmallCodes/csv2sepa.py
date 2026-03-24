"""
csv_to_sepa.py
--------------
Converts a structured CSV file into a SEPA Direct Debit XML (pain.008.003.02).

CSV format:
  Section 1 — Creditor block (preceded by "#creditor"):
    creditor_name, creditor_iban, creditor_bic, creditor_id, collection_date

  Section 2 — Debitor block (preceded by "#debitors"):
    name, iban, bic, amount, mandate_id, mandate_date, sequence_type[, description]

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

PAIN_NAMESPACE = "urn:iso:std:iso:20022:tech:xsd:pain.008.003.02"
XSI_NAMESPACE  = "http://www.w3.org/2001/XMLSchema-instance"
SCHEMA_LOCATION = (
    "urn:iso:std:iso:20022:tech:xsd:pain.008.003.02 "
    "pain.008.003.02.xsd"
)

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
    try:
        return datetime.strptime(date_str.strip(), "%Y-%m-%d").date()
    except ValueError:
        raise ValidationError(f"{label}: Datum '{date_str}' muss im Format YYYY-MM-DD sein")


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

def parse_csv(path: str) -> tuple[dict, list[dict]]:
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

    creditor = {
        "name":            raw_c["creditor_name"],
        "iban":            validate_iban(raw_c["creditor_iban"], "Gläubiger IBAN"),
        "bic":             validate_bic(raw_c["creditor_bic"],   "Gläubiger BIC"),
        "creditor_id":     validate_creditor_id(raw_c["creditor_id"], "Gläubiger-ID"),
        "collection_date": validate_date(raw_c["collection_date"], "Einzugsdatum"),
    }

    # ── Parse debitors ──
    deb_reader = list(csv.DictReader(debitor_lines))
    if not deb_reader:
        raise ValidationError("Keine Schuldner-Zeilen gefunden")

    debitors = []
    required_d = ["name", "iban", "bic", "amount", "mandate_id", "mandate_date", "sequence_type"]

    for i, row in enumerate(deb_reader, start=1):
        row = {k.strip(): v.strip() for k, v in row.items() if k}
        label = f"Zeile {i} ('{row.get('name', '?')}')"

        for field in required_d:
            if field not in row or not row[field]:
                raise ValidationError(f"{label}: Pflichtfeld '{field}' fehlt")

        seq = row["sequence_type"].strip().upper()
        if seq not in VALID_SEQUENCE_TYPES:
            raise ValidationError(
                f"{label}: sequence_type '{seq}' ungültig – erlaubt: {', '.join(VALID_SEQUENCE_TYPES)}"
            )

        debitors.append({
            "name":          row["name"],
            "iban":          validate_iban(row["iban"], f"{label} IBAN"),
            "bic":           validate_bic(row["bic"],   f"{label} BIC"),
            "amount":        validate_amount(row["amount"], label),
            "mandate_id":    row["mandate_id"],
            "mandate_date":  validate_date(row["mandate_date"], f"{label} Mandatsdatum"),
            "sequence_type": seq,
            "description":   row.get("description", "").strip() or "SEPA Lastschrift",
        })

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
    root = Element(
        "Document",
        attrib={
            "xmlns":              PAIN_NAMESPACE,
            "xmlns:xsi":          XSI_NAMESPACE,
            "xsi:schemaLocation": SCHEMA_LOCATION,
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

            # Debitor agent
            dbtr_agt    = SubElement(ddt, "DbtrAgt")
            dbtr_fi     = SubElement(dbtr_agt, "FinInstnId")
            SubElement(dbtr_fi, "BIC").text   = tx["bic"]

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
creditor_name,creditor_iban,creditor_bic,creditor_id,collection_date
Mein Unternehmen GmbH,DE12500105170648489890,INGDDEFFXXX,DE98ZZZ09999999999,2025-06-01

#debitors
# Schuldnerdaten – eine Zeile pro Einzug
# name            – vollständiger Name des Kontoinhabers
# iban            – IBAN des Schuldners
# bic             – BIC der Bank des Schuldners
# amount          – Betrag in EUR (Dezimalpunkt, z.B. 49.00)
# mandate_id      – eindeutige Mandatsreferenz (z.B. Kundennummer)
# mandate_date    – Datum der Mandatsunterschrift (YYYY-MM-DD)
# sequence_type   – FRST (erster Einzug) | RCUR (wiederkehrend) | OOFF (einmalig) | FNAL (letzter)
# description     – Verwendungszweck (optional, max. 140 Zeichen)
name,iban,bic,amount,mandate_id,mandate_date,sequence_type,description
Max Mustermann,DE89370400440532013000,COBADEFFXXX,99.50,MAND-001,2024-01-15,FRST,Mitgliedsbeitrag Q1
Erika Musterfrau,DE75512108001245126199,SSKMDEMMXXX,49.00,MAND-002,2023-06-01,RCUR,Monatsbeitrag Mai
Hans Schmidt,DE91100000000123456789,BELADEBEXXX,150.00,MAND-003,2022-11-20,OOFF,Einmalige Zahlung
"""

def create_example_csv(path: str) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(EXAMPLE_CSV)


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        default_input = "input.csv"
        if Path(default_input).exists():
            print(f"Keine Argumente – verwende gefundene {default_input}")
            input_path  = default_input
            output_path = "output.xml"
        else:
            create_example_csv("input.csv")
            print(f"Keine input.csv gefunden – Beispieldatei als input.csv erstellt")
            print("   Passe die Daten an und starte erneut mit: python csv_to_sepa.py")
            sys.exit(0)
    else:
        if sys.argv[1] == "--example":
            example_path = "input_example.csv"
            create_example_csv(example_path)
            print(f"Beispieldatei erstellt: {example_path}")
            print("   Aufruf: python csv_to_sepa.py input_example.csv [output.xml]")
            sys.exit(0)

        input_path  = sys.argv[1]
        output_path = sys.argv[2] if len(sys.argv) > 2 else "output.xml"

    print(f"Lese CSV: {input_path}")

    errors = []
    try:
        creditor, debitors = parse_csv(input_path)
    except ValidationError as e:
        print(f"\nValidierungsfehler: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print(f"\nDatei nicht gefunden: {input_path}")
        sys.exit(1)

    print(f"Gläubiger:  {creditor['name']} ({creditor['iban']})")
    print(f"Schuldner:  {len(debitors)} Einträge")
    print(f"Gesamtbetrag: {sum(d['amount'] for d in debitors):.2f} EUR")
    print(f"Einzugsdatum: {creditor['collection_date']}")

    # ── Vorlaufzeit prüfen ──
    today = date.today()
    col_date = creditor["collection_date"]
    seq_types = {d["sequence_type"] for d in debitors}
    required_days = max(LEAD_DAYS[s] for s in seq_types)
    delta = (col_date - today).days

    if col_date <= today:
        print(f"\nWarnung: Einzugsdatum {col_date} liegt in der Vergangenheit oder ist heute!")
    elif delta < required_days:
        print(f"\nWarnung: Einzugsdatum {col_date} unterschreitet die empfohlene Vorlaufzeit.")
        print(f"   Heute ist {today}, benötigt werden mind. {required_days} Kalendertage → frühestens {today + __import__('datetime').timedelta(days=required_days)}.")
        print(f"   Hinweis: Bankarbeitstage (ohne Wochenenden/Feiertage) werden hier nicht berechnet – bitte manuell prüfen.")

    tree = build_xml(creditor, debitors)

    with open(output_path, "w", encoding="utf-8") as fh:
        fh.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        tree.write(fh, encoding="unicode", xml_declaration=False)

    print(f"\nXML erfolgreich erstellt: {output_path}")


if __name__ == "__main__":
    main()
