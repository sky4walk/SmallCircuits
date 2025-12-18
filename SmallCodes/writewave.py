import math

def pack(fmt, *values):
    """
    Eigene Implementierung von struct.pack() für WAV-Dateien.
    
    Unterstützte Formate:
    - '<h': signed short (2 Bytes, little-endian)
    - '<H': unsigned short (2 Bytes, little-endian)
    - '<I': unsigned int (4 Bytes, little-endian)
    - '<hh': zwei signed shorts
    """
    result = bytearray()
    
    # Little-Endian prüfen
    little_endian = fmt.startswith('<')
    if little_endian:
        fmt = fmt[1:]  # '<' entfernen
    
    value_index = 0
    i = 0
    
    while i < len(fmt):
        format_char = fmt[i]
        
        if format_char == 'h':  # signed short (2 Bytes, -32768 bis 32767)
            value = values[value_index]
            value_index += 1
            
            # Auf Bereich begrenzen
            if value < -32768:
                value = -32768
            if value > 32767:
                value = 32767
            
            # Negative Zahlen in unsigned umwandeln (Zweierkomplement)
            if value < 0:
                value = 65536 + value
            
            # In Bytes umwandeln (little-endian)
            byte1 = value & 0xFF
            byte2 = (value >> 8) & 0xFF
            result.append(byte1)
            result.append(byte2)
            
        elif format_char == 'H':  # unsigned short (2 Bytes, 0 bis 65535)
            value = values[value_index]
            value_index += 1
            
            # Auf Bereich begrenzen
            if value < 0:
                value = 0
            if value > 65535:
                value = 65535
            
            # In Bytes umwandeln (little-endian)
            byte1 = value & 0xFF
            byte2 = (value >> 8) & 0xFF
            result.append(byte1)
            result.append(byte2)
            
        elif format_char == 'I':  # unsigned int (4 Bytes, 0 bis 4294967295)
            value = values[value_index]
            value_index += 1
            
            # Auf Bereich begrenzen
            if value < 0:
                value = 0
            if value > 4294967295:
                value = 4294967295
            
            # In Bytes umwandeln (little-endian)
            byte1 = value & 0xFF
            byte2 = (value >> 8) & 0xFF
            byte3 = (value >> 16) & 0xFF
            byte4 = (value >> 24) & 0xFF
            result.append(byte1)
            result.append(byte2)
            result.append(byte3)
            result.append(byte4)
        
        i += 1
    
    return bytes(result)


def write_wav_header(f, num_channels, sample_rate, bits_per_sample, num_samples):
    """
    Schreibt den WAV-Header manuell - jetzt komplett ohne struct!
    """
    byte_rate = sample_rate * num_channels * bits_per_sample // 8
    block_align = num_channels * bits_per_sample // 8
    data_size = num_samples * num_channels * bits_per_sample // 8
    
    # RIFF-Header
    f.write(b'RIFF')
    f.write(pack('<I', 36 + data_size))  # Dateigröße - 8
    f.write(b'WAVE')
    
    # fmt-Chunk
    f.write(b'fmt ')
    f.write(pack('<I', 16))  # Größe des fmt-Chunks
    f.write(pack('<H', 1))   # Audio-Format (1 = PCM)
    f.write(pack('<H', num_channels))
    f.write(pack('<I', sample_rate))
    f.write(pack('<I', byte_rate))
    f.write(pack('<H', block_align))
    f.write(pack('<H', bits_per_sample))
    
    # data-Chunk Header
    f.write(b'data')
    f.write(pack('<I', data_size))


def write_wav_file(filename, duration=2.0, frequency=440, sample_rate=44100, amplitude=0.5):
    """
    Schreibt eine WAV-Datei mit einem Sinuston - komplett ohne externe Bibliotheken!
    
    Parameter:
    - filename: Name der zu erstellenden WAV-Datei
    - duration: Dauer in Sekunden
    - frequency: Frequenz des Tons in Hz (440 Hz = A4)
    - sample_rate: Abtastrate in Hz (44100 ist CD-Qualität)
    - amplitude: Lautstärke (0.0 bis 1.0)
    """
    num_channels = 1
    bits_per_sample = 16
    num_samples = int(sample_rate * duration)
    
    with open(filename, 'wb') as f:
        # WAV-Header schreiben
        write_wav_header(f, num_channels, sample_rate, bits_per_sample, num_samples)
        
        # Audio-Daten schreiben
        for i in range(num_samples):
            # Sinuswelle berechnen
            sample = amplitude * math.sin(2 * math.pi * frequency * i / sample_rate)
            # In 16-bit Integer konvertieren (-32768 bis 32767)
            sample_int = int(sample * 32767)
            # Als binäre Daten schreiben (little-endian, signed short)
            f.write(pack('<h', sample_int))
    
    print(f"WAV-Datei '{filename}' erfolgreich erstellt!")
    print(f"Dauer: {duration}s, Frequenz: {frequency}Hz, Abtastrate: {sample_rate}Hz")


def write_stereo_wav(filename, duration=2.0, freq_left=440, freq_right=554, sample_rate=44100):
    """
    Schreibt eine Stereo-WAV-Datei mit unterschiedlichen Frequenzen für linken und rechten Kanal.
    """
    num_channels = 2
    bits_per_sample = 16
    num_samples = int(sample_rate * duration)
    
    with open(filename, 'wb') as f:
        # WAV-Header schreiben
        write_wav_header(f, num_channels, sample_rate, bits_per_sample, num_samples)
        
        # Audio-Daten schreiben
        for i in range(num_samples):
            # Linker Kanal
            sample_left = 0.5 * math.sin(2 * math.pi * freq_left * i / sample_rate)
            sample_left_int = int(sample_left * 32767)
            
            # Rechter Kanal
            sample_right = 0.5 * math.sin(2 * math.pi * freq_right * i / sample_rate)
            sample_right_int = int(sample_right * 32767)
            
            # Beide Kanäle schreiben (interleaved)
            f.write(pack('<hh', sample_left_int, sample_right_int))
    
    print(f"Stereo-WAV-Datei '{filename}' erfolgreich erstellt!")


def write_wav_from_samples(filename, samples, sample_rate=44100, num_channels=1):
    """
    Schreibt beliebige Sample-Daten in eine WAV-Datei.
    
    Parameter:
    - filename: Name der WAV-Datei
    - samples: Liste von Samples (Werte zwischen -1.0 und 1.0)
    - sample_rate: Abtastrate in Hz
    - num_channels: 1 für Mono, 2 für Stereo
    """
    bits_per_sample = 16
    num_samples = len(samples)
    
    with open(filename, 'wb') as f:
        # WAV-Header schreiben
        write_wav_header(f, num_channels, sample_rate, bits_per_sample, num_samples)
        
        # Samples schreiben
        for sample in samples:
            # Wert auf -1.0 bis 1.0 begrenzen
            sample = max(-1.0, min(1.0, sample))
            # In 16-bit Integer konvertieren
            sample_int = int(sample * 32767)
            f.write(pack('<h', sample_int))
    
    print(f"WAV-Datei '{filename}' mit {num_samples} Samples erstellt!")


# Beispielverwendung
if __name__ == "__main__":
    # Einfacher Mono-Ton (440 Hz = Ton A)
    write_wav_file("ton_440hz.wav", duration=2.0, frequency=440)
    
    # Höherer Ton (C-Dur: C4 = 261.63 Hz)
    write_wav_file("ton_c4.wav", duration=1.5, frequency=261.63)
    
    # Stereo-Beispiel (linker Kanal A, rechter Kanal C#)
    write_stereo_wav("stereo_ton.wav", duration=2.0, freq_left=440, freq_right=554.37)
    
    # Benutzerdefinierte Samples
    # Beispiel: Sägezahnwelle
    samples = []
    for i in range(44100):  # 1 Sekunde
        samples.append((i % 100) / 50.0 - 1.0)
    write_wav_from_samples("saegezahn.wav", samples)
    
    # Test der pack-Funktion
    print("\nTest von pack():")
    print(pack('<h', 1000))  # b'\xe8\x03'
    print(pack('<I', 44100))  # b'D\xac\x00\x00'
    print(pack('<hh', 100, 200))  # b'd\x00\xc8\x00'