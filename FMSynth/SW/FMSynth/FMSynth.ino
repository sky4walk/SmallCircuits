// ═══════════════════════════════════════════════════════════
//  FMSynth.ino — FM Synthesizer für Wemos D1 Mini (ESP8266)
//  PWM Audio + ADSR + Serielle Steuerung
//  Samplerate: 8 kHz, Fixed-Point ISR (kein Float im ISR)
// ═══════════════════════════════════════════════════════════

#include <Arduino.h>
#include <math.h>

// ── Pins ────────────────────────────────────────────────────
#define AUDIO_PIN D1

// ── Wavetable ───────────────────────────────────────────────
const uint16_t WAVE_SIZE = 256;
int16_t sineTable[WAVE_SIZE];

void buildSineTable() {
  for (int i = 0; i < WAVE_SIZE; i++)
    sineTable[i] = (int16_t)(127.0f * sinf(2.0f * M_PI * i / WAVE_SIZE));
}

// ── ADSR (Integer, kein Float im ISR) ───────────────────────
// level: 0..65535  (65535 = volle Lautstärke)
// increment: pro Sample addieren/subtrahieren

const float SR = 8000.0f;

struct ADSR {
  float attackTime   = 0.01f;
  float decayTime    = 0.1f;
  float sustainLevel = 0.6f;
  float releaseTime  = 0.3f;

  enum class Stage : uint8_t {
    IDLE, ATTACK, DECAY, SUSTAIN, RELEASE
  } stage = Stage::IDLE;

  uint16_t level     = 0;
  uint16_t increment = 0;
  uint16_t sustainLvl = 0;

  // Wird aus dem Hauptprogramm aufgerufen (darf Float nutzen)
  void noteOn() {
    sustainLvl = (uint16_t)(sustainLevel * 65535.0f);
    uint32_t steps = (uint32_t)(attackTime * SR);
    if (steps == 0) steps = 1;
    increment = (uint16_t)(65535UL / steps);
    stage = Stage::ATTACK;
  }

  void noteOff() {
    if (stage == Stage::IDLE) return;
    uint32_t steps = (uint32_t)(releaseTime * SR);
    if (steps == 0) steps = 1;
    increment = (uint16_t)((uint32_t)level / steps);
    if (increment == 0) increment = 1;
    stage = Stage::RELEASE;
  }

  // Nur Integer-Ops — sicher im ISR
  uint16_t IRAM_ATTR tick() {
    switch (stage) {
      case Stage::ATTACK:
        if ((uint32_t)level + increment >= 65535) {
          level = 65535;
          stage = Stage::DECAY;
          uint32_t steps = (uint32_t)(decayTime * SR);
          if (steps == 0) steps = 1;
          increment = (uint16_t)((uint32_t)(65535 - sustainLvl) / steps);
          if (increment == 0) increment = 1;
        } else {
          level += increment;
        }
        break;

      case Stage::DECAY:
        if (level <= sustainLvl + increment) {
          level = sustainLvl;
          stage = Stage::SUSTAIN;
        } else {
          level -= increment;
        }
        break;

      case Stage::SUSTAIN:
        // level bleibt konstant
        break;

      case Stage::RELEASE:
        if (level <= increment) {
          level = 0;
          stage = Stage::IDLE;
        } else {
          level -= increment;
        }
        break;

      case Stage::IDLE:
        break;
    }
    return level;
  }

  bool isIdle() { return stage == Stage::IDLE; }
};

// ── Voice ────────────────────────────────────────────────────
const uint8_t  VOICES    = 3;
const uint32_t PHASE_MAX = 0xFFFFFFFFUL;

struct Voice {
  uint32_t carrierPhase    = 0;
  uint32_t modulatorPhase  = 0;
  uint32_t carrierStep     = 0;
  uint32_t modulatorStep   = 0;
  int32_t  modIndex_q8     = 640;  // 2.5 × 256
  uint8_t  note            = 255;
  ADSR     env;

  bool isActive() { return !env.isIdle(); }
};

Voice voices[VOICES];

// Globale Parameter (live änderbar über Serial)
float   gAttack    = 0.01f;
float   gDecay     = 0.1f;
float   gSustain   = 0.6f;
float   gRelease   = 0.3f;
float   gModRatio  = 2.0f;
float   gModIndex  = 2.5f;   // wird als q8 gespeichert

// ── Hilfsfunktionen ──────────────────────────────────────────
float noteToFreq(uint8_t note) {
  return 440.0f * powf(2.0f, (note - 69) / 12.0f);
}

uint32_t freqToStep(float freq) {
  return (uint32_t)(freq / SR * (float)PHASE_MAX);
}

// ── Audio ISR (nur Integer, IRAM) ────────────────────────────
void IRAM_ATTR onTimerISR() {
  int32_t mix    = 0;
  uint8_t active = 0;

  for (uint8_t v = 0; v < VOICES; v++) {
    uint16_t envLevel = voices[v].env.tick();
    if (envLevel == 0) continue;

    // Modulator
    voices[v].modulatorPhase += voices[v].modulatorStep;
    int32_t modSample = sineTable[voices[v].modulatorPhase >> 24]; // -127..127

    // Fixed-point FM: modIndex_q8 / 256 * modSample
    // Faktor 21474836 ≈ PHASE_MAX / (2π × 127)
    int32_t modOut    = (modSample * voices[v].modIndex_q8) >> 8;
    uint32_t modOffset = (uint32_t)(modOut * 21474836L);

    // Carrier
    voices[v].carrierPhase += voices[v].carrierStep;
    uint8_t idx = (uint8_t)((voices[v].carrierPhase + modOffset) >> 24);

    // Envelope (16-bit → 7-bit nutzbare Amplitude)
    mix += (sineTable[idx] * (int32_t)envLevel) >> 16;
    active++;
  }

  // Mischen
  if (active > 1) mix /= active;

  // Auf PWM-Range [0..255] skalieren
  int32_t out = mix + 127;
  if (out < 0)   out = 0;
  if (out > 255) out = 255;

  analogWrite(AUDIO_PIN, (uint16_t)out);
}

// ── Voice Allocation ─────────────────────────────────────────
uint8_t findFreeVoice() {
  // 1. Komplett idle
  for (uint8_t i = 0; i < VOICES; i++)
    if (voices[i].env.isIdle()) return i;
  // 2. Im Release (am wenigsten störend)
  for (uint8_t i = 0; i < VOICES; i++)
    if (voices[i].env.stage == ADSR::Stage::RELEASE) return i;
  // 3. Voice stealing: erste Stimme
  return 0;
}

int8_t findVoiceForNote(uint8_t note) {
  for (uint8_t i = 0; i < VOICES; i++)
    if (voices[i].note == note && voices[i].isActive()) return i;
  return -1;
}

void noteOn(uint8_t note, float velocity = 1.0f) {
  uint8_t v  = findFreeVoice();
  float freq = noteToFreq(note);

  voices[v].note         = note;
  voices[v].carrierStep  = freqToStep(freq);
  voices[v].modulatorStep = freqToStep(freq * gModRatio);
  // Velocity skaliert modIndex → weiche Töne klingen sanfter
  voices[v].modIndex_q8  = (int32_t)(gModIndex * velocity * 256.0f);
  voices[v].carrierPhase  = 0;
  voices[v].modulatorPhase = 0;

  voices[v].env.attackTime   = gAttack;
  voices[v].env.decayTime    = gDecay;
  voices[v].env.sustainLevel = gSustain;
  voices[v].env.releaseTime  = gRelease;
  voices[v].env.noteOn();
}

void noteOff(uint8_t note) {
  int8_t v = findVoiceForNote(note);
  if (v >= 0) voices[v].env.noteOff();
}

void allNotesOff() {
  for (uint8_t i = 0; i < VOICES; i++)
    voices[i].env.noteOff();
}

// Dur-Dreiklang: Root, Große Terz (+4), Quinte (+7)
void chordMajorOn(uint8_t root) {
  allNotesOff();
  noteOn(root);
  if (root + 4 <= 127) noteOn(root + 4);
  if (root + 7 <= 127) noteOn(root + 7);
}

// Moll-Dreiklang: Root, Kleine Terz (+3), Quinte (+7)
void chordMinorOn(uint8_t root) {
  allNotesOff();
  noteOn(root);
  if (root + 3 <= 127) noteOn(root + 3);
  if (root + 7 <= 127) noteOn(root + 7);
}

// ── Note-Parser: "C4", "F#3", "Bb5" → MIDI-Nummer ───────────
uint8_t parseNote(const String& s) {
  if (s.length() < 2) return 255;

  int8_t  semitone = -1;
  uint8_t pos      = 0;

  switch (toupper(s[pos++])) {
    case 'C': semitone =  0; break;
    case 'D': semitone =  2; break;
    case 'E': semitone =  4; break;
    case 'F': semitone =  5; break;
    case 'G': semitone =  7; break;
    case 'A': semitone =  9; break;
    case 'B': semitone = 11; break;
    default:  return 255;
  }

  // Vorzeichen
  if (pos < s.length() && (s[pos] == '#' || s[pos] == 'b')) {
    semitone += (s[pos] == '#') ? 1 : -1;
    pos++;
  }

  // Oktave
  if (pos >= s.length()) return 255;
  int octave = s.substring(pos).toInt();

  int midi = (octave + 1) * 12 + semitone;
  if (midi < 0 || midi > 127) return 255;
  return (uint8_t)midi;
}

// ── Preset-Sounds ────────────────────────────────────────────
void presetPiano() {
  gAttack = 0.005f; gDecay = 0.2f; gSustain = 0.4f; gRelease = 0.3f;
  gModRatio = 2.0f; gModIndex = 3.0f;
  Serial.println(F("Preset: Klavier"));
}

void presetStrings() {
  gAttack = 0.4f; gDecay = 0.1f; gSustain = 0.8f; gRelease = 0.6f;
  gModRatio = 1.0f; gModIndex = 1.5f;
  Serial.println(F("Preset: Streicher"));
}

void presetOrgan() {
  gAttack = 0.01f; gDecay = 0.0f; gSustain = 1.0f; gRelease = 0.05f;
  gModRatio = 2.0f; gModIndex = 1.0f;
  Serial.println(F("Preset: Orgel"));
}

void presetPluck() {
  gAttack = 0.001f; gDecay = 0.4f; gSustain = 0.0f; gRelease = 0.1f;
  gModRatio = 3.0f; gModIndex = 4.0f;
  Serial.println(F("Preset: Pluck"));
}

void presetBell() {
  gAttack = 0.001f; gDecay = 0.8f; gSustain = 0.1f; gRelease = 0.5f;
  gModRatio = 7.0f; gModIndex = 5.0f;
  Serial.println(F("Preset: Glocke"));
}

// ── Hilfe ausgeben ───────────────────────────────────────────
void printHelp() {
  Serial.println(F(""));
  Serial.println(F("┌─ FM Synth ── Wemos D1 Mini ──────────────┐"));
  Serial.println(F("│ NOTEN                                     │"));
  Serial.println(F("│  n C4       Note On  (C4, F#3, Bb5...)   │"));
  Serial.println(F("│  o C4       Note Off                      │"));
  Serial.println(F("│  c C4       Dur-Dreiklang                 │"));
  Serial.println(F("│  l C4       Moll-Dreiklang                │"));
  Serial.println(F("│  x          Alle Noten aus                │"));
  Serial.println(F("├─ ADSR ────────────────────────────────────┤"));
  Serial.println(F("│  a 0.01     Attack  (Sekunden)            │"));
  Serial.println(F("│  d 0.2      Decay   (Sekunden)            │"));
  Serial.println(F("│  s 0.6      Sustain (0.0–1.0)             │"));
  Serial.println(F("│  r 0.3      Release (Sekunden)            │"));
  Serial.println(F("├─ FM ──────────────────────────────────────┤"));
  Serial.println(F("│  m 2.0      Mod Ratio  (1,2,3,7...)       │"));
  Serial.println(F("│  i 2.5      Mod Index  (0.0–10.0)         │"));
  Serial.println(F("├─ PRESETS ─────────────────────────────────┤"));
  Serial.println(F("│  p1  Klavier   p2  Streicher              │"));
  Serial.println(F("│  p3  Orgel     p4  Pluck    p5  Glocke    │"));
  Serial.println(F("├───────────────────────────────────────────┤"));
  Serial.println(F("│  ?  /  h    Diese Hilfe                   │"));
  Serial.println(F("└───────────────────────────────────────────┘"));
}

// ── Serieller Command-Parser ─────────────────────────────────
String inputBuffer = "";

void handleCommand(const String& line) {
  if (line.length() == 0) return;

  char    cmd = tolower(line[0]);
  String  arg = (line.length() > 2) ? line.substring(2) : "";
  arg.trim();

  // Presets (zweistellige Befehle)
  if (line.length() >= 2 && cmd == 'p') {
    switch (line[1]) {
      case '1': presetPiano();   return;
      case '2': presetStrings(); return;
      case '3': presetOrgan();   return;
      case '4': presetPluck();   return;
      case '5': presetBell();    return;
    }
  }

  switch (cmd) {
    // ── Noten ──
    case 'n': {
      uint8_t note = parseNote(arg);
      if (note == 255) { Serial.println(F("! Ungueltige Note (Bsp: C4, F#3, Bb5)")); return; }
      noteOn(note);
      Serial.print(F(">> Note On:  ")); Serial.println(arg);
      break;
    }
    case 'o': {
      uint8_t note = parseNote(arg);
      if (note == 255) { Serial.println(F("! Ungueltige Note")); return; }
      noteOff(note);
      Serial.print(F("[] Note Off: ")); Serial.println(arg);
      break;
    }
    case 'c': {
      uint8_t root = parseNote(arg);
      if (root == 255) { Serial.println(F("! Ungueltige Note")); return; }
      chordMajorOn(root);
      Serial.print(F("## Dur:      ")); Serial.println(arg);
      break;
    }
    case 'l': {
      uint8_t root = parseNote(arg);
      if (root == 255) { Serial.println(F("! Ungueltige Note")); return; }
      chordMinorOn(root);
      Serial.print(F("## Moll:     ")); Serial.println(arg);
      break;
    }
    case 'x':
      allNotesOff();
      Serial.println(F("[] Alle Noten aus"));
      break;

    // ── ADSR ──
    case 'a':
      gAttack = constrain(arg.toFloat(), 0.001f, 5.0f);
      Serial.print(F("Attack:  ")); Serial.println(gAttack, 3);
      break;
    case 'd':
      gDecay = constrain(arg.toFloat(), 0.0f, 5.0f);
      Serial.print(F("Decay:   ")); Serial.println(gDecay, 3);
      break;
    case 's':
      gSustain = constrain(arg.toFloat(), 0.0f, 1.0f);
      Serial.print(F("Sustain: ")); Serial.println(gSustain, 2);
      break;
    case 'r':
      gRelease = constrain(arg.toFloat(), 0.001f, 5.0f);
      Serial.print(F("Release: ")); Serial.println(gRelease, 3);
      break;

    // ── FM ──
    case 'm':
      gModRatio = constrain(arg.toFloat(), 0.1f, 20.0f);
      Serial.print(F("Mod Ratio: ")); Serial.println(gModRatio, 2);
      break;
    case 'i':
      gModIndex = constrain(arg.toFloat(), 0.0f, 10.0f);
      Serial.print(F("Mod Index: ")); Serial.println(gModIndex, 2);
      break;

    // ── Hilfe ──
    case '?':
    case 'h':
      printHelp();
      break;

    default:
      Serial.print(F("? Unbekannt: ")); Serial.println(line);
      break;
  }
}

// ── Setup ────────────────────────────────────────────────────
void setup() {
  buildSineTable();

  // PWM konfigurieren — kein analogWrite() hier, Timer übernimmt sofort
  analogWriteFreq(40000);  // PWM-Träger 40 kHz (unhörbar)
  analogWriteRange(255);   // 8-bit Auflösung
  pinMode(AUDIO_PIN, OUTPUT);
  digitalWrite(AUDIO_PIN, LOW);

  Serial.begin(115200);
  delay(1000); // warten bis Serial-Monitor verbunden

  printHelp();
  Serial.println(F("Bereit! (Samplerate: 8 kHz)"));
  Serial.println(F("Serial Monitor: Zeilenende = 'Newline'"));

  // Hardware Timer sauber initialisieren
  timer1_disable();
  timer1_isr_init();
  timer1_attachInterrupt(onTimerISR);
  timer1_enable(TIM_DIV1, TIM_EDGE, TIM_LOOP);
  timer1_write(10000); // 80 MHz / 10000 = 8000 Hz Samplerate
}

// ── Loop ─────────────────────────────────────────────────────
void loop() {
  // Seriellen Input lesen (zeilenweise)
  while (Serial.available()) {
    char c = (char)Serial.read();
    if (c == '\n' || c == '\r') {
      inputBuffer.trim();
      if (inputBuffer.length() > 0) {
        handleCommand(inputBuffer);
      }
      inputBuffer = "";
    } else if (inputBuffer.length() < 64) {
      inputBuffer += c;
    }
  }

  // ESP8266 Hintergrund-Tasks (WiFi-Stack, WDT) bedienen
  yield();
}
