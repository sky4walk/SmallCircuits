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
    
    # Wenn kein Zielverzeichnis angegeben, verwende das Quellverzeichnis
    if target_base_dir is None:
        target_base_dir = source_path
    else:
        target_base_dir = Path(target_base_dir)
    
    if not source_path.exists():
        print(f"Fehler: Verzeichnis {source_dir} existiert nicht!")
        return
    
    # Durchlaufe alle Dateien im Quellverzeichnis
    for item in source_path.iterdir():
        # Überspringe Verzeichnisse
        if item.is_dir():
            continue
        
        # Hole das Änderungsdatum der Datei
        modification_time = datetime.fromtimestamp(item.stat().st_mtime)
        
        # Erstelle Verzeichnisname im Format YYYY-MM-DD
        date_folder_name = modification_time.strftime("%Y-%m-%d")
        date_folder_path = target_base_dir / date_folder_name
        
        # Erstelle das Verzeichnis, falls es nicht existiert
        date_folder_path.mkdir(exist_ok=True)
        
        # Verschiebe die Datei
        target_file_path = date_folder_path / item.name
        
        # Falls Datei bereits existiert, füge Timestamp hinzu
        if target_file_path.exists():
            timestamp = datetime.now().strftime("%H%M%S")
            name_parts = item.stem, timestamp, item.suffix
            new_name = f"{name_parts[0]}_{name_parts[1]}{name_parts[2]}"
            target_file_path = date_folder_path / new_name
        
        shutil.move(str(item), str(target_file_path))
        print(f"Verschoben: {item.name} -> {date_folder_name}/")


def delete_old_directories(base_dir, days_old=7):
    """
    Löscht Unterverzeichnisse, die älter als die angegebene Anzahl von Tagen sind.
    
    Args:
        base_dir: Basisverzeichnis, in dem nach alten Ordnern gesucht wird
        days_old: Alter in Tagen (Standard: 7)
    """
    base_path = Path(base_dir)
    
    if not base_path.exists():
        print(f"Fehler: Verzeichnis {base_dir} existiert nicht!")
        return
    
    # Berechne das Grenzdatum
    cutoff_date = datetime.now() - timedelta(days=days_old)
    
    # Durchlaufe alle Unterverzeichnisse
    for item in base_path.iterdir():
        if not item.is_dir():
            continue
        
        # Hole das Änderungsdatum des Verzeichnisses
        dir_modification_time = datetime.fromtimestamp(item.stat().st_mtime)
        
        # Prüfe, ob das Verzeichnis älter als das Grenzatum ist
        if dir_modification_time < cutoff_date:
            try:
                shutil.rmtree(item)
                print(f"Gelöscht: {item.name} (Alter: {(datetime.now() - dir_modification_time).days} Tage)")
            except Exception as e:
                print(f"Fehler beim Löschen von {item.name}: {e}")


def run_once():
    """
    Führt die Organisierung einmalig aus.
    """
    SOURCE_DIRECTORY = os.getcwd()
    
    print("=" * 60)
    print("Datei-Organizer gestartet")
    print(f"Verzeichnis: {SOURCE_DIRECTORY}")
    print(f"Zeit: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Schritt 1: Dateien organisieren
    print("\n1. Organisiere Dateien nach Datum...")
    organize_files_by_date(SOURCE_DIRECTORY)
    
    # Schritt 2: Alte Verzeichnisse löschen
    print("\n2. Lösche Verzeichnisse älter als 7 Tage...")
    delete_old_directories(SOURCE_DIRECTORY, days_old=7)
    
    print("\n" + "=" * 60)
    print("Fertig!")
    print("=" * 60)


def run_daily(target_hour=2, target_minute=0):
    """
    Führt die Organisierung täglich zur angegebenen Uhrzeit aus.
    
    Args:
        target_hour: Stunde (0-23), Standard: 2 Uhr
        target_minute: Minute (0-59), Standard: 0
    """
    print("=" * 60)
    print("Datei-Organizer im Daemon-Modus")
    print(f"Wird täglich um {target_hour:02d}:{target_minute:02d} Uhr ausgeführt")
    print("Drücke Ctrl+C zum Beenden")
    print("=" * 60)
    
    while True:
        now = datetime.now()
        
        # Berechne die nächste Ausführungszeit
        next_run = now.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)
        
        # Wenn die Zeit heute schon vorbei ist, nimm morgen
        if now >= next_run:
            next_run += timedelta(days=1)
        
        # Berechne Wartezeit
        wait_seconds = (next_run - now).total_seconds()
        
        print(f"\n[{now.strftime('%Y-%m-%d %H:%M:%S')}] Nächste Ausführung: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Warte {wait_seconds/3600:.1f} Stunden...")
        
        # Warte bis zur nächsten Ausführung
        time.sleep(wait_seconds)
        
        # Führe die Organisierung aus
        run_once()


def main():
    """
    Hauptfunktion: Organisiert Dateien und löscht alte Verzeichnisse.
    """
    # Verwende das aktuelle Arbeitsverzeichnis
    SOURCE_DIRECTORY = os.getcwd()
    
    print("=" * 60)
    print("Datei-Organizer gestartet")
    print("=" * 60)
    
    # Schritt 1: Dateien organisieren
    print("\n1. Organisiere Dateien nach Datum...")
    organize_files_by_date(SOURCE_DIRECTORY)
    
    # Schritt 2: Alte Verzeichnisse löschen
    print("\n2. Lösche Verzeichnisse älter als 7 Tage...")
    delete_old_directories(SOURCE_DIRECTORY, days_old=7)
    
    print("\n" + "=" * 60)
    print("Fertig!")
    print("=" * 60)


if __name__ == "__main__":
    # Prüfe Kommandozeilenargumente
    if len(sys.argv) > 1:
        if sys.argv[1] == "--daemon" or sys.argv[1] == "-d":
            # Daemon-Modus: Läuft täglich
            target_hour = 2  # Standard: 2 Uhr nachts
            target_minute = 0
            
            # Optional: Zeit als Argument übergeben (z.B. --daemon 14:30)
            if len(sys.argv) > 2:
                try:
                    time_parts = sys.argv[2].split(":")
                    target_hour = int(time_parts[0])
                    target_minute = int(time_parts[1]) if len(time_parts) > 1 else 0
                except:
                    print("Fehler: Zeitformat sollte HH:MM sein (z.B. 14:30)")
                    sys.exit(1)
            
            try:
                run_daily(target_hour, target_minute)
            except KeyboardInterrupt:
                print("\n\nDaemon beendet.")
                sys.exit(0)
        elif sys.argv[1] == "--help" or sys.argv[1] == "-h":
            print("""
Datei-Organizer - Verwendung:

  python file_organizer.py           Einmalige Ausführung
  python file_organizer.py -d        Daemon-Modus (täglich um 2:00 Uhr)
  python file_organizer.py -d 14:30  Daemon-Modus (täglich um 14:30 Uhr)
  python file_organizer.py --help    Diese Hilfe anzeigen

Funktionen:
  - Verschiebt Dateien in Unterverzeichnisse nach Datum (YYYY-MM-DD)
  - Löscht Verzeichnisse, die älter als 7 Tage sind
            """)
            sys.exit(0)
        else:
            print(f"Unbekannte Option: {sys.argv[1]}")
            print("Verwende --help für Hilfe")
            sys.exit(1)
    else:
        # Standardmodus: Einmalige Ausführung
        main()
