1. Arduino IDE vorbereiten

download: https://www.arduino.cc/en/software
sudo apt install esptool

chmod +x arduino-ide_*.AppImage
./arduino-ide_2.3.8_Linux_64bit.AppImage --no-sandbox

Board installieren (falls noch nicht):

Datei → Voreinstellungen → Zusätzliche Boardverwalter-URLs:
http://arduino.esp8266.com/stable/package_esp8266com_index.json

Datei → Einstellungen → "Ausführliche Ausgabe während: Kompilierung" ankreuzen → OK

Werkzeuge → Board → Boardverwalter → esp8266 installieren 3.2.1
Board wählen: LOLIN(WEMOS) D1 R2 & mini
Flash Size: 4MB (FS:2MB)

Werkzeuge - SSL Support → "Basic SSL ciphers (lower ROM, faster boot)"


