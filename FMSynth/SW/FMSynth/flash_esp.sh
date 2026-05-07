#!/bin/bash
# ─────────────────────────────────────────────────────────────
# flash_esp.sh — Brausteuerung auf ESP8266 (Wemos D1 Mini) flashen
# Liegt im gleichen Verzeichnis wie der Sketch
# ─────────────────────────────────────────────────────────────

SKETCH_DIR="$(dirname "$0")"
BUILD_DIR="$SKETCH_DIR/build/esp8266.esp8266.d1"
BAUD=921600

# ── Neueste BIN-Datei automatisch finden ─────────────────────
BIN_FILE=$(find "$BUILD_DIR" -name "*.bin" ! -name "*.signed" \
           -printf '%T@ %p\n' 2>/dev/null | sort -n | tail -1 | cut -d' ' -f2-)

if [ -z "$BIN_FILE" ]; then
  # Fallback: im Sketch-Verzeichnis suchen
  BIN_FILE=$(find "$SKETCH_DIR" -name "*.bin" ! -name "*.signed" \
             -printf '%T@ %p\n' 2>/dev/null | sort -n | tail -1 | cut -d' ' -f2-)
fi

if [ -z "$BIN_FILE" ]; then
  echo "❌ Keine BIN-Datei gefunden in:"
  echo "   $BUILD_DIR"
  echo ""
  echo "   Arduino IDE: Sketch → Exportiere kompilierte Binärdatei"
  exit 1
fi

# ── Port automatisch erkennen ─────────────────────────────────
PORT=""
for p in /dev/ttyUSB0 /dev/ttyUSB1 /dev/ttyACM0 /dev/ttyACM1; do
  if [ -e "$p" ]; then
    PORT="$p"
    break
  fi
done

if [ -z "$PORT" ]; then
  echo "❌ Kein ESP gefunden — USB-Kabel prüfen!"
  echo "   Gesucht: /dev/ttyUSB0, /dev/ttyUSB1, /dev/ttyACM0, /dev/ttyACM1"
  exit 1
fi

# ── Info anzeigen ─────────────────────────────────────────────
BIN_SIZE=$(du -h "$BIN_FILE" | cut -f1)
BIN_DATE=$(date -r "$BIN_FILE" "+%d.%m.%Y %H:%M")

echo "🍺 Brausteuerung Flash-Script"
echo "─────────────────────────────"
echo "Port:     $PORT"
echo "Datei:    $(basename $BIN_FILE)"
echo "Größe:    $BIN_SIZE"
echo "Datum:    $BIN_DATE"
echo "Baudrate: $BAUD"
echo "─────────────────────────────"
echo ""
read -p "▶ Flashen starten? (j/n): " confirm
if [ "$confirm" != "j" ] && [ "$confirm" != "J" ]; then
  echo "Abgebrochen."
  exit 0
fi

echo ""
echo "⏳ Flashe..."
esptool --port "$PORT" \
        --baud "$BAUD" \
        --chip esp8266 \
        write_flash 0x0 "$BIN_FILE"

if [ $? -eq 0 ]; then
  echo ""
  echo "✓ Erfolgreich geflasht!"
  echo "  ESP startet neu — Serial Monitor auf 115200 Baud öffnen"
  echo "  Web-Interface: http://brausteuerung.local"
  stty -F $PORT 115200 raw
  cat $PORT
else
  echo ""
  echo "❌ Flash fehlgeschlagen!"
  echo "   - USB-Kabel prüfen"
  echo "   - Port-Berechtigung: sudo chmod 666 $PORT"
  echo "   - oder: sudo usermod -a -G dialout $USER"
  exit 1
fi
