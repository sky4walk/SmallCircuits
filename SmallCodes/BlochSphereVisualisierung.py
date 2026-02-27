"""
Bloch-Kugel Visualisierung mit Quantengattern
==============================================

Erstellt hochwertige Visualisierungen der Bloch-Kugel und zeigt,
wie verschiedene Quantengatter als Rotationen wirken.
"""

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.patches import FancyArrowPatch
from mpl_toolkits.mplot3d.proj3d import proj_transform
import math

# Farben
COLORS = {
    'sphere': '#e8f4f8',
    'equator': '#95a5a6',
    'axis': '#34495e',
    'ket0': '#2ecc71',
    'ket1': '#e74c3c',
    'plus': '#3498db',
    'minus': '#9b59b6',
    'plusi': '#f39c12',
    'minusi': '#e67e22',
    'arrow': '#c0392b',
    'grid': '#bdc3c7'
}

class Arrow3D(FancyArrowPatch):
    """3D-Pfeil für Matplotlib"""
    def __init__(self, x, y, z, dx, dy, dz, *args, **kwargs):
        super().__init__((0, 0), (0, 0), *args, **kwargs)
        self._xyz = (x, y, z)
        self._dxdydz = (dx, dy, dz)

    def draw(self, renderer):
        x1, y1, z1 = self._xyz
        dx, dy, dz = self._dxdydz
        x2, y2, z2 = (x1 + dx, y1 + dy, z1 + dz)

        xs, ys, zs = proj_transform((x1, x2), (y1, y2), (z1, z2), self.axes.M)
        self.set_positions((xs[0], ys[0]), (xs[1], ys[1]))
        super().draw(renderer)
        
    def do_3d_projection(self, renderer=None):
        x1, y1, z1 = self._xyz
        dx, dy, dz = self._dxdydz
        x2, y2, z2 = (x1 + dx, y1 + dy, z1 + dz)

        xs, ys, zs = proj_transform((x1, x2), (y1, y2), (z1, z2), self.axes.M)
        self.set_positions((xs[0], ys[0]), (xs[1], ys[1]))
        
        return np.min(zs)

def bloch_koordinaten(theta, phi):
    """Konvertiert Bloch-Winkel zu kartesischen Koordinaten"""
    x = np.sin(theta) * np.cos(phi)
    y = np.sin(theta) * np.sin(phi)
    z = np.cos(theta)
    return x, y, z

def matrix_mal_vektor(matrix, vektor):
    """Matrix-Vektor-Multiplikation"""
    result = np.zeros(len(vektor), dtype=complex)
    for i in range(len(matrix)):
        for j in range(len(matrix[0])):
            result[i] += matrix[i][j] * vektor[j]
    return result

def vektor_zu_bloch(vektor):
    """
    Konvertiert einen Zustandsvektor [α, β] zu Bloch-Koordinaten.
    
    Berechnet die Erwartungswerte der Pauli-Matrizen:
    x = ⟨σₓ⟩, y = ⟨σᵧ⟩, z = ⟨σᵧ⟩
    """
    alpha = vektor[0]
    beta = vektor[1]
    
    # Pauli-Erwartungswerte
    x = 2 * np.real(np.conj(alpha) * beta)
    y = 2 * np.imag(np.conj(alpha) * beta)
    z = np.abs(alpha)**2 - np.abs(beta)**2
    
    return x, y, z

def zeichne_bloch_kugel(ax, title="Bloch-Kugel", elevation=20, azimuth=45):
    """Zeichnet die Basis-Bloch-Kugel"""
    
    # Kugel-Oberfläche
    u = np.linspace(0, 2 * np.pi, 50)
    v = np.linspace(0, np.pi, 50)
    x = np.outer(np.cos(u), np.sin(v))
    y = np.outer(np.sin(u), np.sin(v))
    z = np.outer(np.ones(np.size(u)), np.cos(v))
    
    ax.plot_surface(x, y, z, alpha=0.1, color=COLORS['sphere'], edgecolor='none')
    
    # Äquator
    theta = np.linspace(0, 2*np.pi, 100)
    x_eq = np.cos(theta)
    y_eq = np.sin(theta)
    z_eq = np.zeros_like(theta)
    ax.plot(x_eq, y_eq, z_eq, color=COLORS['equator'], linewidth=1.5, 
            linestyle='--', alpha=0.5)
    
    # Längen- und Breitengrade
    for angle in [np.pi/4, np.pi/2, 3*np.pi/4]:
        x_lat = np.sin(angle) * np.cos(theta)
        y_lat = np.sin(angle) * np.sin(theta)
        z_lat = np.cos(angle) * np.ones_like(theta)
        ax.plot(x_lat, y_lat, z_lat, color=COLORS['grid'], 
                linewidth=0.5, alpha=0.3)
    
    # Achsen
    axis_length = 1.4
    
    # X-Achse
    arrow_x = Arrow3D(0, 0, 0, axis_length, 0, 0,
                      mutation_scale=20, lw=2, arrowstyle='-|>',
                      color=COLORS['axis'])
    ax.add_artist(arrow_x)
    ax.text(axis_length + 0.1, 0, 0, 'X', fontsize=12, fontweight='bold')
    
    # Y-Achse
    arrow_y = Arrow3D(0, 0, 0, 0, axis_length, 0,
                      mutation_scale=20, lw=2, arrowstyle='-|>',
                      color=COLORS['axis'])
    ax.add_artist(arrow_y)
    ax.text(0, axis_length + 0.1, 0, 'Y', fontsize=12, fontweight='bold')
    
    # Z-Achse
    arrow_z = Arrow3D(0, 0, 0, 0, 0, axis_length,
                      mutation_scale=20, lw=2, arrowstyle='-|>',
                      color=COLORS['axis'])
    ax.add_artist(arrow_z)
    ax.text(0, 0, axis_length + 0.1, 'Z', fontsize=12, fontweight='bold')
    
    # Wichtige Zustände markieren
    # |0⟩ (Nordpol)
    ax.plot([0], [0], [1], 'o', color=COLORS['ket0'], markersize=10, 
            markeredgecolor='white', markeredgewidth=2)
    ax.text(0, 0, 1.2, '|0⟩', fontsize=11, fontweight='bold', 
            ha='center', color=COLORS['ket0'])
    
    # |1⟩ (Südpol)
    ax.plot([0], [0], [-1], 'o', color=COLORS['ket1'], markersize=10,
            markeredgecolor='white', markeredgewidth=2)
    ax.text(0, 0, -1.2, '|1⟩', fontsize=11, fontweight='bold',
            ha='center', color=COLORS['ket1'])
    
    # |+⟩ (auf X-Achse)
    ax.plot([1], [0], [0], 'o', color=COLORS['plus'], markersize=8,
            markeredgecolor='white', markeredgewidth=2)
    ax.text(1.15, 0, 0, '|+⟩', fontsize=10, fontweight='bold',
            color=COLORS['plus'])
    
    # |−⟩ (auf -X-Achse)
    ax.plot([-1], [0], [0], 'o', color=COLORS['minus'], markersize=8,
            markeredgecolor='white', markeredgewidth=2)
    ax.text(-1.15, 0, 0, '|−⟩', fontsize=10, fontweight='bold',
            color=COLORS['minus'])
    
    # Einstellungen
    ax.set_xlim([-1.5, 1.5])
    ax.set_ylim([-1.5, 1.5])
    ax.set_zlim([-1.5, 1.5])
    ax.set_box_aspect([1, 1, 1])
    ax.view_init(elev=elevation, azim=azimuth)
    ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
    ax.set_axis_off()

def zeige_zustand_auf_bloch(ax, vektor, label, color, title=""):
    """Zeigt einen Quantenzustand auf der Bloch-Kugel"""
    zeichne_bloch_kugel(ax, title=title)
    
    # Konvertiere zu Bloch-Koordinaten
    x, y, z = vektor_zu_bloch(vektor)
    
    # Pfeil vom Ursprung zum Zustand
    arrow = Arrow3D(0, 0, 0, x, y, z,
                    mutation_scale=20, lw=3, arrowstyle='-|>',
                    color=color)
    ax.add_artist(arrow)
    
    # Punkt am Ende
    ax.plot([x], [y], [z], 'o', color=color, markersize=12,
            markeredgecolor='white', markeredgewidth=2.5)
    
    # Label
    offset = 1.25
    ax.text(x*offset, y*offset, z*offset, label, fontsize=12,
            fontweight='bold', color=color,
            bbox=dict(boxstyle='round,pad=0.5', facecolor='white', 
                     edgecolor=color, linewidth=2))

def zeige_gatter_wirkung(zustand_vorher, gatter_matrix, gatter_name, 
                         output_file, color_vorher='#3498db', color_nachher='#e74c3c'):
    """Zeigt Vorher-Nachher einer Gatter-Anwendung - BEIDE auf einer Kugel!"""
    
    fig = plt.figure(figsize=(12, 10))
    ax = fig.add_subplot(111, projection='3d')
    
    # Zeichne Basis-Kugel
    zeichne_bloch_kugel(ax, f'{gatter_name}: Vorher → Nachher', elevation=20, azimuth=45)
    
    # Zustand VORHER
    x1, y1, z1 = vektor_zu_bloch(zustand_vorher)
    
    # Pfeil VORHER (dünn, gestrichelt)
    arrow_vorher = Arrow3D(0, 0, 0, x1, y1, z1,
                          mutation_scale=15, lw=2, arrowstyle='-|>',
                          color=color_vorher, linestyle='--', alpha=0.5)
    ax.add_artist(arrow_vorher)
    
    # Punkt VORHER
    ax.plot([x1], [y1], [z1], 'o', color=color_vorher, markersize=10,
            markeredgecolor='white', markeredgewidth=2, alpha=0.6)
    
    # Label VORHER
    offset = 1.3
    ax.text(x1*offset, y1*offset, z1*offset, 'Vorher', fontsize=11,
            color=color_vorher, fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.4', facecolor='white', 
                     edgecolor=color_vorher, linewidth=1.5, alpha=0.9))
    
    # Zustand NACHHER
    zustand_nachher = matrix_mal_vektor(gatter_matrix, zustand_vorher)
    x2, y2, z2 = vektor_zu_bloch(zustand_nachher)
    
    # Pfeil NACHHER (dick, durchgezogen)
    arrow_nachher = Arrow3D(0, 0, 0, x2, y2, z2,
                           mutation_scale=20, lw=4, arrowstyle='-|>',
                           color=color_nachher)
    ax.add_artist(arrow_nachher)
    
    # Punkt NACHHER
    ax.plot([x2], [y2], [z2], 'o', color=color_nachher, markersize=14,
            markeredgecolor='white', markeredgewidth=2.5)
    
    # Label NACHHER
    ax.text(x2*offset, y2*offset, z2*offset, 'Nachher', fontsize=12,
            color=color_nachher, fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='white', 
                     edgecolor=color_nachher, linewidth=2, alpha=0.9))
    
    # Rotationspfad (Bogen zwischen vorher und nachher)
    # Interpoliere mehrere Zwischenschritte
    schritte = 20
    pfad_x, pfad_y, pfad_z = [], [], []
    
    for i in range(schritte + 1):
        t = i / schritte
        # Einfache lineare Interpolation und dann normalisieren
        zwischen = (1-t) * zustand_vorher + t * zustand_nachher
        # Normalisieren (damit es auf der Kugel bleibt)
        norm = np.sqrt(np.abs(zwischen[0])**2 + np.abs(zwischen[1])**2)
        if norm > 0:
            zwischen = zwischen / norm
        x, y, z = vektor_zu_bloch(zwischen)
        pfad_x.append(x)
        pfad_y.append(y)
        pfad_z.append(z)
    
    # Zeichne Rotationspfad
    ax.plot(pfad_x, pfad_y, pfad_z, color='#f39c12', linewidth=3, 
            linestyle=':', alpha=0.7, label='Rotationspfad')
    
    # Winkel berechnen und anzeigen
    # Winkel zwischen zwei Zustandsvektoren
    dot_product = np.real(np.conj(zustand_vorher[0]) * zustand_nachher[0] + 
                          np.conj(zustand_vorher[1]) * zustand_nachher[1])
    winkel = np.arccos(np.clip(np.abs(dot_product), -1, 1))
    winkel_grad = np.degrees(winkel)
    
    # Info-Text
    info_text = f'Rotation: {winkel_grad:.1f}°'
    ax.text2D(0.05, 0.95, info_text, transform=ax.transAxes,
              fontsize=13, fontweight='bold',
              bbox=dict(boxstyle='round,pad=0.7', facecolor='yellow', alpha=0.8),
              verticalalignment='top')
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=150, bbox_inches='tight', facecolor='white')
    print(f"✓ Gespeichert: {output_file}")
    plt.close()

def zeige_rotation_animation(zustand, achse, winkel, gatter_name, output_file):
    """Zeigt die Rotation in mehreren Schritten - mit Geister-Zuständen"""
    
    fig = plt.figure(figsize=(20, 5))
    
    schritte = 5
    
    for i in range(schritte):
        ax = fig.add_subplot(1, schritte, i+1, projection='3d')
        
        # Berechne Zwischenzustand
        anteil = i / (schritte - 1) if schritte > 1 else 0
        theta = winkel * anteil
        
        # Rotationsmatrix
        if achse == 'X':
            matrix = np.array([[np.cos(theta/2), -1j*np.sin(theta/2)],
                              [-1j*np.sin(theta/2), np.cos(theta/2)]])
        elif achse == 'Y':
            matrix = np.array([[np.cos(theta/2), -np.sin(theta/2)],
                              [np.sin(theta/2), np.cos(theta/2)]])
        else:  # Z
            matrix = np.array([[np.exp(-1j*theta/2), 0],
                              [0, np.exp(1j*theta/2)]])
        
        zwischen_zustand = matrix_mal_vektor(matrix, zustand)
        
        # Zeichne Basis-Kugel
        zeichne_bloch_kugel(ax, "", elevation=20, azimuth=45)
        
        # Farbverlauf: von blau nach rot
        farbe = plt.cm.RdYlBu_r(anteil)
        
        # Zeige ALLE vorherigen Zustände als Geister
        for j in range(i):
            ghost_anteil = j / (schritte - 1)
            ghost_theta = winkel * ghost_anteil
            
            if achse == 'X':
                ghost_matrix = np.array([[np.cos(ghost_theta/2), -1j*np.sin(ghost_theta/2)],
                                        [-1j*np.sin(ghost_theta/2), np.cos(ghost_theta/2)]])
            elif achse == 'Y':
                ghost_matrix = np.array([[np.cos(ghost_theta/2), -np.sin(ghost_theta/2)],
                                        [np.sin(ghost_theta/2), np.cos(ghost_theta/2)]])
            else:  # Z
                ghost_matrix = np.array([[np.exp(-1j*ghost_theta/2), 0],
                                        [0, np.exp(1j*ghost_theta/2)]])
            
            ghost_zustand = matrix_mal_vektor(ghost_matrix, zustand)
            gx, gy, gz = vektor_zu_bloch(ghost_zustand)
            
            # Geister-Punkt
            ax.plot([gx], [gy], [gz], 'o', color='gray', markersize=6, alpha=0.3)
        
        # Aktueller Zustand
        x, y, z = vektor_zu_bloch(zwischen_zustand)
        
        # Pfeil
        arrow = Arrow3D(0, 0, 0, x, y, z,
                       mutation_scale=20, lw=3, arrowstyle='-|>',
                       color=farbe)
        ax.add_artist(arrow)
        
        # Punkt
        ax.plot([x], [y], [z], 'o', color=farbe, markersize=14,
                markeredgecolor='white', markeredgewidth=2.5)
        
        # Titel mit Prozent und Winkel
        winkel_grad = np.degrees(theta)
        titel = f'{int(anteil*100)}%\n{winkel_grad:.0f}°'
        ax.set_title(titel, fontsize=14, fontweight='bold', pad=10)
        
        # Label
        offset = 1.25
        ax.text(x*offset, y*offset, z*offset, f'Schritt {i+1}', fontsize=10,
                fontweight='bold', color=farbe,
                bbox=dict(boxstyle='round,pad=0.4', facecolor='white', 
                         edgecolor=farbe, linewidth=2))
    
    # Großer Titel für die ganze Figur
    fig.suptitle(gatter_name, fontsize=16, fontweight='bold', y=0.98)
    
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig(output_file, dpi=150, bbox_inches='tight', facecolor='white')
    print(f"✓ Gespeichert: {output_file}")
    plt.close()

def erstelle_alle_visualisierungen():
    """Erstellt alle Bloch-Kugel-Visualisierungen"""
    
    print("\n" + "="*70)
    print("  Bloch-Kugel Visualisierungen erstellen")
    print("="*70)
    
    # Basis-Zustände
    ket0 = np.array([1, 0], dtype=complex)
    ket1 = np.array([0, 1], dtype=complex)
    ketplus = np.array([1/np.sqrt(2), 1/np.sqrt(2)], dtype=complex)
    
    # Quantengatter
    X = np.array([[0, 1], [1, 0]], dtype=complex)
    Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
    Z = np.array([[1, 0], [0, -1]], dtype=complex)
    H = np.array([[1, 1], [1, -1]], dtype=complex) / np.sqrt(2)
    S = np.array([[1, 0], [0, 1j]], dtype=complex)
    T = np.array([[1, 0], [0, np.exp(1j*np.pi/4)]], dtype=complex)
    
    # 1. Basis-Bloch-Kugel
    print("\n1. Basis-Bloch-Kugel...")
    fig = plt.figure(figsize=(10, 10))
    ax = fig.add_subplot(111, projection='3d')
    zeichne_bloch_kugel(ax, "Die Bloch-Kugel")
    plt.savefig('bloch_basis.png', dpi=150, 
                bbox_inches='tight', facecolor='white')
    print("✓ Gespeichert: bloch_basis.png")
    plt.close()
    
    # 2. X-Gatter: |0⟩ → |1⟩
    print("\n2. X-Gatter: |0⟩ → |1⟩...")
    zeige_gatter_wirkung(ket0, X, "X-Gatter", 
                        'bloch_x_gatter.png')
    
    # 3. H-Gatter: |0⟩ → |+⟩
    print("\n3. Hadamard: |0⟩ → |+⟩...")
    zeige_gatter_wirkung(ket0, H, "Hadamard-Gatter",
                        'bloch_h_gatter.png')
    
    # 4. Z-Gatter: |+⟩ → |−⟩
    print("\n4. Z-Gatter: |+⟩ → |−⟩...")
    zeige_gatter_wirkung(ketplus, Z, "Z-Gatter",
                        'bloch_z_gatter.png')
    
    # 5. Y-Gatter: |0⟩ → i|1⟩
    print("\n5. Y-Gatter: |0⟩ → i|1⟩...")
    zeige_gatter_wirkung(ket0, Y, "Y-Gatter",
                        'bloch_y_gatter.png')
    
    # 6. S-Gatter: |+⟩ → |+i⟩
    print("\n6. S-Gatter (90° um Z)...")
    zeige_gatter_wirkung(ketplus, S, "S-Gatter",
                        'bloch_s_gatter.png')
    
    # 7. T-Gatter
    print("\n7. T-Gatter (45° um Z)...")
    zeige_gatter_wirkung(ketplus, T, "T-Gatter",
                        'bloch_t_gatter.png')
    
    # 8. X-Rotation Animation
    print("\n8. X-Rotation Animation...")
    zeige_rotation_animation(ket0, 'X', np.pi, "X-Rotation (180°)",
                            'bloch_x_rotation.png')
    
    # 9. Y-Rotation Animation
    print("\n9. Y-Rotation Animation...")
    zeige_rotation_animation(ket0, 'Y', np.pi, "Y-Rotation (180°)",
                            'bloch_y_rotation.png')
    
    # 10. Z-Rotation Animation
    print("\n10. Z-Rotation Animation...")
    zeige_rotation_animation(ketplus, 'Z', np.pi, "Z-Rotation (180°)",
                            'bloch_z_rotation.png')
    
    # 11. Vergleich aller Pauli-Gatter
    print("\n11. Alle Pauli-Gatter im Vergleich...")
    fig = plt.figure(figsize=(18, 6))
    
    gatter_liste = [
        (X, 'X-Gatter\n(180° um X)', ket0, COLORS['ket0']),
        (Y, 'Y-Gatter\n(180° um Y)', ket0, COLORS['plusi']),
        (Z, 'Z-Gatter\n(180° um Z)', ketplus, COLORS['plus'])
    ]
    
    for idx, (gatter, name, zustand, farbe) in enumerate(gatter_liste, 1):
        ax = fig.add_subplot(1, 3, idx, projection='3d')
        zustand_nach = matrix_mal_vektor(gatter, zustand)
        zeige_zustand_auf_bloch(ax, zustand_nach, 'Nach Gatter', farbe, title=name)
    
    plt.tight_layout()
    plt.savefig('bloch_pauli_vergleich.png', dpi=150,
                bbox_inches='tight', facecolor='white')
    print("✓ Gespeichert: bloch_pauli_vergleich.png")
    plt.close()
    
    # 12. Verschiedene Ansichten der Bloch-Kugel
    print("\n12. Verschiedene Ansichten...")
    fig = plt.figure(figsize=(18, 6))
    
    ansichten = [
        (20, 45, "Perspektive"),
        (0, 0, "Seitenansicht (Y-Z)"),
        (90, 0, "Draufsicht (X-Y)")
    ]
    
    for idx, (elev, azim, titel) in enumerate(ansichten, 1):
        ax = fig.add_subplot(1, 3, idx, projection='3d')
        zeichne_bloch_kugel(ax, titel, elevation=elev, azimuth=azim)
    
    plt.tight_layout()
    plt.savefig('bloch_ansichten.png', dpi=150,
                bbox_inches='tight', facecolor='white')
    print("✓ Gespeichert: bloch_ansichten.png")
    plt.close()
    
    print("\n" + "="*70)
    print("  FERTIG! Alle Visualisierungen erstellt.")
    print("="*70)
    print("\nDateien im aktuellen Verzeichnis:")
    print("  • bloch_basis.png - Die Basis-Bloch-Kugel")
    print("  • bloch_x_gatter.png - X-Gatter Vorher/Nachher")
    print("  • bloch_h_gatter.png - Hadamard Vorher/Nachher")
    print("  • bloch_z_gatter.png - Z-Gatter Vorher/Nachher")
    print("  • bloch_y_gatter.png - Y-Gatter Vorher/Nachher")
    print("  • bloch_s_gatter.png - S-Gatter Vorher/Nachher")
    print("  • bloch_t_gatter.png - T-Gatter Vorher/Nachher")
    print("  • bloch_x_rotation.png - X-Rotation in 4 Schritten")
    print("  • bloch_y_rotation.png - Y-Rotation in 4 Schritten")
    print("  • bloch_z_rotation.png - Z-Rotation in 4 Schritten")
    print("  • bloch_pauli_vergleich.png - Alle Pauli-Gatter")
    print("  • bloch_ansichten.png - Verschiedene Perspektiven")
    print()

if __name__ == "__main__":
    erstelle_alle_visualisierungen()
