#pip install staticmap pillow lxml
import xml.etree.ElementTree as ET
from staticmap import StaticMap, Line, CircleMarker
import sys

# KML-Datei einlesen
kml_file = sys.argv[1] if len(sys.argv) > 1 else "track.kml"

tree = ET.parse(kml_file)
root = tree.getroot()

coords = []
for coord_elem in root.iter('{http://www.google.com/kml/ext/2.2}coord'):
    parts = coord_elem.text.strip().split()
    if len(parts) >= 2:
        coords.append((float(parts[0]), float(parts[1])))

print(f"{len(coords)} Koordinaten gefunden")

# Karte rendern mit OSM-Hintergrund
m = StaticMap(1400, 1100, url_template='https://tile.openstreetmap.org/{z}/{x}/{y}.png')

m.add_line(Line(coords, '#FF6600', 4))
m.add_marker(CircleMarker(coords[0], '#00CC44', 14))   # Start (grün)
m.add_marker(CircleMarker(coords[-1], '#CC2200', 14))  # Ziel (rot)

image = m.render()
output = kml_file.replace('.kml', '.jpg')
image.save(output, 'JPEG', quality=93)
print(f"Gespeichert: {output}")
