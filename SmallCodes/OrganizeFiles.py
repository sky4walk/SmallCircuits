#!/usr/bin/env python3
"""
Datei-Organizer: Verschiebt Dateien in tagesbasierte Unterverzeichnisse
und löscht Verzeichnisse, die älter als 7 Tage sind.

Kann entweder einmalig oder als Daemon (täglich um 2:00 Uhr) ausgeführt werden.
"""

import os
import sys
import shutil
import time
from datetime import datetime, timedelta
from pathlib import Path


def organize_files_by_date(source_dir, target_base_dir=None):
    """
    Verschiebt Dateien in Unterverzeichnisse basierend auf ihrem Änderungsdatum.
    
    Args:
        source_dir: Quellverzeichnis mit den zu organisierenden Dateien
        target_base_dir: Zielverzeichnis für die organisierten Ordner (optional)
    """
    source_path = Path(source_dir)
    
    if target_base_dir is None:
        target_base_dir = source_path
    else:
        target_base_dir = Path(target_base_dir)
    
    if not source_path.exists():
        print(f"Fehler: Verzeichnis {source_dir} existiert nicht!")
        return
    
    for item in source_path.iterdir():
        if item.is_dir():
            continue
        
        modification_time = datetime.fromtimestamp(item.stat().st_mtime)
        date_folder_name = modification_time.strftime("%Y-%m-%d")
        date_folder_path = target_base_dir / date_folder_name
        date_folder_path.mkdir(exist_ok=True)
        
        target_file_path = date_folder_path / item.name
        
        if target_file_path.exists():
            timestamp = datetime.now().strftime("%H%M%S")
            name_parts = item.stem, timestamp, item.suffix
            new_name = f"{name_parts[0]}_{name_parts[1]}{name_parts[2]}"
            target_file_path = date_folder_path / new_name
        
        shutil.move(str(item), str(target_file_path))
        print(f"Verschoben: {item.name} -> {date_folder_name}/")


def delete_old_directories(base_dir, days_old=7):
    """
    Löscht Unterverzeichnisse basierend auf dem Datum im Verzeichnisnamen (YYYY-MM-DD).
    
    Args:
        base_dir: Basisverzeichnis, in dem nach alten Ordnern gesucht wird
        days_old: Alter in Tagen (Standard: 7)
    """
    base_path = Path(base_dir)
    
    if not base_path.exists():
        print(f"Fehler: Verzeichnis {base_dir} existiert nicht!")
        return
    
    cutoff_date = datetime.now() - timedelta(days=days_old)
    
    for item in base_path.iterdir():
        if not item.is_dir():
            continue
        
        try:
            dir_date = datetime.strptime(item.name, "%Y-%m-%d")
            
            if dir_date < cutoff_date:
                age_days = (datetime.now() - dir_date).days
                try:
                    shutil.rmtree(item)
                    print(f"Gelöscht: {item.name} (Alter: {age_days} Tage)")
                except Exception as e:
                    print(f"Fehler beim Löschen von {item.name}: {e}")
        except ValueError:
            print(f"Übersprungen: {item.name} (kein gültiges Datumsformat YYYY-MM-DD)")
            continue


def run_once(source_directory):
    """
    Führt die Organisierung einmalig aus.
    """
    print("=" * 60)
    print("Datei-Organizer gestartet")
    print(f"Verzeichnis: {source_directory}")
    print(f"Zeit: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    print("\n1. Organisiere Dateien nach Datum...")
    organize_files_by_date(source_directory)
    
    print("\n2. Lösche Verzeichnisse älter als 7 Tage...")
    delete_old_directories(source_directory, days_old=7)
    
    print("\n" + "=" * 60)
    print("Fertig!")
    print("=" * 60)


def run_daily(source_directory, target_hour=2, target_minute=0):
    """
    Führt die Organisierung täglich zur angegebenen Uhrzeit aus.
    
    Args:
        source_directory: Arbeitsverzeichnis
        target_hour: Stunde (0-23), Standard: 2 Uhr
        target_minute: Minute (0-59), Standard: 0
    """
    print("=" * 60)
    print("Datei-Organizer im Daemon-Modus")
    print(f"Verzeichnis: {source_directory}")
    print(f"Wird täglich um {target_hour:02d}:{target_minute:02d} Uhr ausgeführt")
    print("Drücke Ctrl+C zum Beenden")
    print("=" * 60)
    
    while True:
        now = datetime.now()
        
        next_run = now.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)
        
        if now >= next_run:
            next_run += timedelta(days=1)
        
        wait_seconds = (next_run - now).total_seconds()
        
        print(f"\n[{now.strftime('%Y-%m-%d %H:%M:%S')}] Nächste Ausführung: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Warte {wait_seconds/3600:.1f} Stunden...")
        
        time.sleep(wait_seconds)
        
        run_once(source_directory)


def parse_args():
    """
    Parst Kommandozeilenargumente manuell (ohne argparse).
    Gibt ein dict mit den geparsten Werten zurück.
    """
    args = {
        "mode": "once",        # "once" | "daemon"
        "path": None,          # Arbeitsverzeichnis (None = cwd)
        "time": (2, 0),        # (hour, minute) für Daemon-Modus
    }

    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]

        if arg in ("--daemon", "-d"):
            args["mode"] = "daemon"
            # Optionale Zeitangabe direkt danach: z.B. -d 14:30
            if i + 1 < len(sys.argv) and ":" in sys.argv[i + 1]:
                i += 1
                try:
                    parts = sys.argv[i].split(":")
                    args["time"] = (int(parts[0]), int(parts[1]) if len(parts) > 1 else 0)
                except ValueError:
                    print("Fehler: Zeitformat sollte HH:MM sein (z.B. 14:30)")
                    sys.exit(1)

        elif arg in ("--path", "-p"):
            if i + 1 >= len(sys.argv):
                print("Fehler: --path benötigt ein Verzeichnis als Argument")
                sys.exit(1)
            i += 1
            args["path"] = sys.argv[i]

        elif arg in ("--help", "-h"):
            print("""
Datei-Organizer - Verwendung:

  python3 OrganizeFiles.py                        Einmalige Ausführung (aktuelles Verzeichnis)
  python3 OrganizeFiles.py -p /pfad/zum/ordner    Einmalige Ausführung (angegebener Pfad)
  python3 OrganizeFiles.py -d                     Daemon-Modus (täglich um 2:00 Uhr, aktuelles Verzeichnis)
  python3 OrganizeFiles.py -d 14:30               Daemon-Modus (täglich um 14:30 Uhr)
  python3 OrganizeFiles.py -d -p /pfad/zum/ordner Daemon-Modus mit angegebenem Pfad
  python3 OrganizeFiles.py -d 14:30 -p /pfad      Daemon-Modus mit Zeit und Pfad
  python3 OrganizeFiles.py --help                 Diese Hilfe anzeigen

Optionen:
  -p, --path <verzeichnis>   Arbeitsverzeichnis (Standard: aktuelles Verzeichnis)
  -d, --daemon [HH:MM]       Daemon-Modus, optional mit Uhrzeit (Standard: 02:00)

Funktionen:
  - Verschiebt Dateien in Unterverzeichnisse nach Datum (YYYY-MM-DD)
  - Löscht Verzeichnisse, die älter als 7 Tage sind

Tipp:
  nohup python3 OrganizeFiles.py -d -p /home/pi/daten &
  Lässt das Programm auch nach dem Ausloggen laufen.
            """)
            sys.exit(0)

        else:
            print(f"Unbekannte Option: {arg}")
            print("Verwende --help für Hilfe")
            sys.exit(1)

        i += 1

    return args


def main():
    args = parse_args()

    # Pfad bestimmen: Argument > aktuelles Verzeichnis
    source_directory = args["path"] if args["path"] else os.getcwd()

    # Pfad validieren
    if not Path(source_directory).exists():
        print(f"Fehler: Verzeichnis '{source_directory}' existiert nicht!")
        sys.exit(1)

    if args["mode"] == "daemon":
        hour, minute = args["time"]
        try:
            run_daily(source_directory, target_hour=hour, target_minute=minute)
        except KeyboardInterrupt:
            print("\n\nDaemon beendet.")
            sys.exit(0)
    else:
        run_once(source_directory)


if __name__ == "__main__":
    main()
