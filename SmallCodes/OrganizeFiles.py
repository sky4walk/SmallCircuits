#!/usr/bin/env python3
"""
Datei-Organizer: Verschiebt Dateien in tagesbasierte Unterverzeichnisse
und löscht Verzeichnisse, die älter als 7 Tage sind.
"""

import os
import shutil
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
    main()
