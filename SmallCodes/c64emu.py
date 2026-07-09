"""
c64emu.py — Single-file Commodore 64 emulator in Python.

A from-scratch port + bug-fix + extension of Andre Betz's Java MyC64Emu.
Originally three files (c64emu.py, chips.py, c64_test_prg.py), now consolidated.

Status
------
* 6502 CPU: passes Klaus Dormann functional test (30.6M instructions, ~95M cyc).
* PLA banking, KERNAL/BASIC/CHARGEN ROMs, all RAM regions.
* VIC raster line counter (PAL 312 lines), basic register read/write, raster IRQ.
* CIA1 + CIA2 timers with IRQ/NMI; CIA1 keyboard matrix readout.
* SID stub (silent), color RAM, expansion port open bus.
* Pygame frontend: 40×25 text rendering, keyboard input, real-time-ish.

Bugs fixed vs. the Java original
--------------------------------
* PLA processor-port bits actually update on setCHAREN/setHIRAM/setLORAM.
* ADC adds its 'cycles' argument; SBC follows through.
* INC uses its 'cycles' parameter (was hardcoded 2).
* Opcode 0x7D ADC abs,X now reads memory instead of passing the address.
* Opcode 0x8E STX abs uses stx, not sta.
* SID memory-range check uses end bound (used start twice).
* INC abs has the right cycle count (6, not 4).
* NMOS JMP (indirect) page-wrap bug modeled (Klaus test requires it).
* CPU reset SP = $FD, the canonical post-reset value.
* No more resource leaks (Java had unclosed InputStream/BufferedWriter).

Usage
-----
* `python3 c64emu.py`                  – boot in a pygame window
* `python3 c64emu.py --cputest`        – run the Klaus 6502 functional test
* `python3 c64emu.py --headless N`     – boot, run N steps, dump screen as ASCII
* `python3 c64emu.py --scale 3`        – set window scale (default 2)
* `python3 c64emu.py game.prg`         – boot, then auto-load (& RUN if BASIC)
* `python3 c64emu.py game.prg --no-run`– load but don't auto-RUN
* `python3 c64emu.py tune.sid`         – boot, load PSID, play 50 Hz
* `python3 c64emu.py game.d64`         – mount disk, auto-load & start
* In the window: F11 = warp speed toggle, F12 = soft reset.

D64 disk images are served through KERNAL traps at two levels: the high-level
LOAD / OPEN-CHRIN routines, and the low-level serial (IEC) primitives
(LISTEN/SECOND/CIOUT/UNLSN/TALK/TKSA/ACPTR/UNTALK) that custom game loaders
use to read files directly off the bus. This lets protected multi-stage
loaders (e.g. Bruce Lee) boot without a full 1541 CPU emulation.

ROMs: by default the GPL-3 Open Roms (MEGA65 project) are used, embedded
in this file. Place original C64 ROMs at ./roms/{basic,chargen,kernal}.bin to use
those instead (they will take precedence).
"""

from __future__ import annotations

import base64
import os
import sys
import time
import zlib

# Bump this when rendering/emulation behaviour changes, so it's easy to tell
# which build is actually running.
__version__ = "2026.07.09-split-vmatrix"


# =============================================================================
# Config — C64 memory map constants
# =============================================================================

class Config:
    # Source: https://www.c64-wiki.de/wiki/Speicherbelegungsplan
    ADDR_ZERO_PAGE_START       = 0x0000
    ADDR_ZERO_PAGE_END         = 0x00FF
    ADDR_PROCESSOR_STACK_START = 0x0100
    ADDR_PROCESSOR_STACK_END   = 0x01FF
    ADDR_BASIC_ROM_START       = 0xA000
    ADDR_BASIC_ROM_END         = 0xBFFF
    ADDR_CHARACTER_ROM_START   = 0xD000
    ADDR_CHARACTER_ROM_END     = 0xDFFF
    ADDR_VIC_REGISTER_START    = 0xD000
    ADDR_VIC_REGISTER_END      = 0xD3FF
    ADDR_SID_REGISTER_START    = 0xD400
    ADDR_SID_REGISTER_END      = 0xD7FF
    ADDR_COLOR_RAM_START       = 0xD800
    ADDR_COLOR_RAM_END         = 0xDBFF
    ADDR_CIA1_REGISTER_START   = 0xDC00
    ADDR_CIA1_REGISTER_END     = 0xDCFF
    ADDR_CIA2_REGISTER_START   = 0xDD00
    ADDR_CIA2_REGISTER_END     = 0xDDFF
    ADDR_EXTENSION_START       = 0xDE00
    ADDR_EXTENSION_END         = 0xDFFF
    ADDR_KERNAL_ROM_START      = 0xE000
    ADDR_KERNAL_ROM_END        = 0xFFFF

    ADDR_DATA_DIRECTION_REG    = 0x0000
    ADDR_PROCESSOR_PORT_REG    = 0x0001
    ADDR_BASE_STACK            = 0x0100
    ADDR_NMI_VECTOR            = 0xFFFA
    ADDR_RESET_VECTOR          = 0xFFFC
    ADDR_IRQ_VECTOR            = 0xFFFE


# =============================================================================
# Tools — byte/word helpers
# =============================================================================

def byte2hex(val, add=0): return f"0x{((val & 0xFF) + (add & 0xFF)) & 0xFF:02x}"
def word2hex(val):        return f"0x{val & 0xFFFF:04x}"
def low_byte(addr):       return addr & 0xFF
def high_byte(addr):      return (addr >> 8) & 0xFF
def make_word(lo, hi):    return ((hi & 0xFF) << 8) | (lo & 0xFF)
def test_bit(reg, pos):   return (reg & (1 << pos)) != 0

def set_bit(reg, pos, val):
    return (reg | (1 << pos)) if val else (reg & ~(1 << pos) & 0xFFFF)

def signed_byte(val):
    """Two's-complement interpretation of a byte."""
    val &= 0xFF
    return val - 256 if val & 0x80 else val

def in_range(start, end, addr):
    return start <= addr <= end


# =============================================================================
# PLA — memory banking
# =============================================================================

class AddressSpace:
    RAM         = 0
    OPEN        = 1
    BASIC_ROM   = 2
    CHARSET_ROM = 3
    KERNAL_ROM  = 4
    IO          = 5
    CART_LOW    = 6
    CART_HIGH   = 7


class Pla:
    """
    Programmable Logic Array — controls which chip answers a given address.
    See https://www.c64-wiki.de/wiki/PLA_(C64-Chip)
    """

    def __init__(self):
        self.charen = True
        self.hiram = True
        self.loram = True
        self.exrom = True
        self.game = True
        self.processor_port = 0x07
        self.reset()

    def reset(self):
        self.charen = True
        self.hiram = True
        self.loram = True
        self.exrom = True
        self.game = True
        self.processor_port = 0x07

    def set_charen(self):  self.charen = True;  self.processor_port = set_bit(self.processor_port, 2, True)  & 0xFF
    def clear_charen(self):self.charen = False; self.processor_port = set_bit(self.processor_port, 2, False) & 0xFF
    def set_hiram(self):   self.hiram = True;   self.processor_port = set_bit(self.processor_port, 1, True)  & 0xFF
    def clear_hiram(self): self.hiram = False;  self.processor_port = set_bit(self.processor_port, 1, False) & 0xFF
    def set_loram(self):   self.loram = True;   self.processor_port = set_bit(self.processor_port, 0, True)  & 0xFF
    def clear_loram(self): self.loram = False;  self.processor_port = set_bit(self.processor_port, 0, False) & 0xFF
    def set_exrom(self):   self.exrom = True
    def clear_exrom(self): self.exrom = False
    def set_game(self):    self.game = True
    def clear_game(self):  self.game = False

    @property
    def prozessorport(self):
        return self.processor_port & 0xFF

    @prozessorport.setter
    def prozessorport(self, port):
        self.processor_port = port & 0xFF
        if test_bit(self.processor_port, 2): self.set_charen()
        else:                                self.clear_charen()
        if test_bit(self.processor_port, 1): self.set_hiram()
        else:                                self.clear_hiram()
        if test_bit(self.processor_port, 0): self.set_loram()
        else:                                self.clear_loram()

    def address_space(self, addr):
        if 0x1000 <= addr <= 0x7FFF:
            if not self.game and self.exrom:
                return AddressSpace.OPEN
            return AddressSpace.RAM
        if 0x8000 <= addr <= 0x9FFF:
            if not self.exrom and self.hiram and self.loram:
                return AddressSpace.CART_LOW
            return AddressSpace.RAM
        if 0xA000 <= addr <= 0xBFFF:
            if not self.game and self.exrom:
                return AddressSpace.OPEN
            if not self.game and not self.exrom and self.hiram:
                return AddressSpace.CART_HIGH
            if self.hiram and self.loram:
                return AddressSpace.BASIC_ROM
            return AddressSpace.RAM
        if 0xC000 <= addr <= 0xCFFF:
            if not self.game and self.exrom:
                return AddressSpace.OPEN
            return AddressSpace.RAM
        if 0xD000 <= addr <= 0xDFFF:
            if not self.game and self.exrom:
                return AddressSpace.IO
            if not self.hiram and not self.loram:
                return AddressSpace.RAM
            if self.charen:
                return AddressSpace.IO
            return AddressSpace.CHARSET_ROM
        if 0xE000 <= addr <= 0xFFFF:
            if not self.game and self.exrom:
                return AddressSpace.CART_HIGH
            if self.hiram:
                return AddressSpace.KERNAL_ROM
            return AddressSpace.RAM
        return AddressSpace.RAM


# =============================================================================
# VIC-II  ($D000-$D3FF, mirrored every $40 bytes)
# =============================================================================

class Vic:
    REG_RASTER_LINE = 0x12
    REG_CTRL1       = 0x11
    REG_IRQ_STATUS  = 0x19
    REG_IRQ_ENABLE  = 0x1A
    REG_BORDER_COL  = 0x20
    REG_BG_COL_0    = 0x21

    CYCLES_PER_LINE = 63
    LINES_PER_FRAME = 312
    # Raster line at which the renderer latches display-relevant registers.
    # Sits inside the visible playfield (below any top status split), so that
    # per-frame rendering uses the values active during the main display area
    # rather than whatever the game left set during vblank. This is what makes
    # mid-frame raster splits on $D018 (font/screen base double-buffering, as
    # used by e.g. Bruce Lee) render correctly without full cycle accuracy.
    SAMPLE_LINE = 150

    def __init__(self):
        self.regs = bytearray(0x40)
        # Snapshot of self.regs taken at SAMPLE_LINE each frame; the frontend
        # renders from this rather than the live registers.
        self.display_regs = bytearray(0x40)
        # $D018 value active at each raster line, recorded as the beam passes.
        # Lets the renderer give each character row the font/screen base that
        # was active at its raster position, so vertical raster splits (e.g. a
        # status line in a different font than the playfield below) render
        # correctly even without cycle-accurate emulation.
        self.line_d018 = bytearray(self.LINES_PER_FRAME)
        # $D011 (mode: BMM/ECM) and $D016 (MCM) per raster line too, so a
        # mid-screen split between graphics modes — e.g. Elite's bitmap 3D view
        # above a text dashboard — is rendered per row in the correct mode.
        self.line_d011 = bytearray(self.LINES_PER_FRAME)
        self.line_d016 = bytearray(self.LINES_PER_FRAME)
        self.raster = 0
        self._line_cycles = 0
        self.raster_compare = 0
        self.irq_status = 0
        self.irq_enable = 0
        # Sprite-sprite ($D01E) and sprite-data ($D01F) collision latches.
        # Bits are set as collisions occur; reading clears the register.
        self.sprite_sprite_coll = 0
        self.sprite_data_coll = 0
        # Boot-time defaults to match the kernal's expectations
        self.regs[0x20] = 0x0E       # border = light blue
        self.regs[0x21] = 0x06       # background = blue
        self.regs[0x11] = 0x1B       # display on, 25 rows, scroll y=3
        self.regs[0x18] = 0x14       # screen mem $0400, char mem $1000
        self.regs[0x16] = 0xC8       # default control reg 2
        self.display_regs[:] = self.regs
        for i in range(self.LINES_PER_FRAME):
            self.line_d018[i] = self.regs[0x18]
            self.line_d011[i] = self.regs[0x11]
            self.line_d016[i] = self.regs[0x16]

    @property
    def irq_line(self):
        return (self.irq_status & self.irq_enable & 0x0F) != 0

    def read(self, offset):
        offset &= 0x3F
        if offset >= 0x2F:
            return 0xFF
        if offset == self.REG_RASTER_LINE:
            return self.raster & 0xFF
        if offset == self.REG_CTRL1:
            return (self.regs[offset] & 0x7F) | ((self.raster >> 1) & 0x80)
        if offset == self.REG_IRQ_STATUS:
            v = self.irq_status & 0x0F
            if v & self.irq_enable:
                v |= 0x80
            return v | 0x70
        if offset == self.REG_IRQ_ENABLE:
            return self.irq_enable | 0xF0
        if offset == 0x1E:                       # sprite-sprite collision (read clears)
            v = self.sprite_sprite_coll
            self.sprite_sprite_coll = 0
            return v
        if offset == 0x1F:                       # sprite-data collision (read clears)
            v = self.sprite_data_coll
            self.sprite_data_coll = 0
            return v
        return self.regs[offset]

    def write(self, offset, val):
        offset &= 0x3F
        val &= 0xFF
        if offset == self.REG_RASTER_LINE:
            self.raster_compare = (self.raster_compare & 0x100) | val
        elif offset == self.REG_CTRL1:
            self.regs[offset] = val
            self.raster_compare = (self.raster_compare & 0xFF) | ((val & 0x80) << 1)
        elif offset == self.REG_IRQ_STATUS:
            self.irq_status &= ~(val & 0x0F)
        elif offset == self.REG_IRQ_ENABLE:
            self.irq_enable = val & 0x0F
        else:
            self.regs[offset] = val

    def tick(self, cycles):
        self._line_cycles += cycles
        while self._line_cycles >= self.CYCLES_PER_LINE:
            self._line_cycles -= self.CYCLES_PER_LINE
            self.raster = (self.raster + 1) % self.LINES_PER_FRAME
            self.line_d018[self.raster] = self.regs[0x18]
            self.line_d011[self.raster] = self.regs[0x11]
            self.line_d016[self.raster] = self.regs[0x16]
            if self.raster == self.raster_compare:
                self.irq_status |= 0x01
            if self.raster == self.SAMPLE_LINE:
                # Latch the registers active during the visible playfield so the
                # per-frame renderer is immune to mid-frame raster splits.
                self.display_regs[:] = self.regs


# =============================================================================
# SID ($D400-$D7FF, mirrored every $20 bytes)
#
# 3 voices, each with 4 waveforms (saw/triangle/pulse/noise) and ADSR envelope.
# Sample-rate generation in chunks (one frame worth at a time). No filter yet,
# no combined-waveform emulation, no per-cycle sample accuracy — good enough
# for most simple SID tunes, all PRGs that play single notes, and clearly
# audible "yes, the music is there" verification.
# =============================================================================

class SidVoice:
    """One of three SID voices."""

    def __init__(self):
        self.freq = 0
        self.pulse_width = 0
        self.control = 0
        self.attack_decay = 0
        self.sustain_release = 0
        # Internal state
        self.phase = 0           # 24-bit accumulator (treated as float for vectorisation)
        self.envelope = 0.0      # 0.0..1.0
        self.env_state = 0       # 0=release, 1=attack, 2=decay, 3=sustain
        # Noise: 23-bit LFSR clocked from the oscillator (bit 19), so the noise
        # has a frequency-dependent character just like the real SID. noise_acc
        # accumulates oscillator advance toward the next LFSR shift.
        self.noise_lfsr = 0x7FFFFF
        self.noise_acc = 0.0
        self.noise_out = 0.0

    def write_reg(self, offset, val):
        if   offset == 0: self.freq = (self.freq & 0xFF00) | val
        elif offset == 1: self.freq = (self.freq & 0x00FF) | (val << 8)
        elif offset == 2: self.pulse_width = (self.pulse_width & 0x0F00) | val
        elif offset == 3: self.pulse_width = (self.pulse_width & 0x00FF) | ((val & 0x0F) << 8)
        elif offset == 4:
            old_gate = self.control & 0x01
            new_gate = val & 0x01
            if new_gate and not old_gate:
                self.env_state = 1    # attack triggered
            elif not new_gate and old_gate:
                self.env_state = 0    # release triggered
            if val & 0x08:            # TEST bit resets phase
                self.phase = 0
            self.control = val
        elif offset == 5: self.attack_decay = val
        elif offset == 6: self.sustain_release = val


class Sid:
    """
    SID 6581/8580 (simplified).

    Frame-buffered audio: read SID register state at start of frame, generate
    one frame worth of samples assuming static state. Register writes within
    a frame take effect on the next frame boundary.
    """
    CPU_CLOCK = 985248.0          # PAL master clock (Hz)
    SAMPLE_RATE = 44100

    # Approximate ADSR times in seconds for rate values 0..15 (from SID datasheet)
    ATTACK_TIMES = (0.002, 0.008, 0.016, 0.024, 0.038, 0.056, 0.068, 0.080,
                    0.100, 0.250, 0.500, 0.800, 1.000, 3.000, 5.000, 8.000)
    DECAY_TIMES  = tuple(t * 3.0 for t in ATTACK_TIMES)   # decay/release ~3x

    irq_line = False

    def __init__(self):
        self.voices = [SidVoice() for _ in range(3)]
        self.master_vol = 0
        self.regs = bytearray(0x20)
        # Filter — analog state-variable filter, two integrators
        self.filter_cutoff = 0          # 11-bit (FC LO 3 bits + FC HI 8 bits)
        self.filter_resonance = 0       # 4-bit, high nibble of $D417
        self.filter_routing = 0         # bits 0..2 = route v1..v3 through filter
        self.filter_mode = 0            # bit 0=LP, 1=BP, 2=HP, 3=v3-disconnect
        self._flt_low = 0.0             # integrator 1 (lowpass output)
        self._flt_band = 0.0            # integrator 2 (bandpass output)

    def read(self, offset):
        offset &= 0x1F
        if offset == 0x1B:                # OSC3 readout
            return (int(self.voices[2].phase) >> 16) & 0xFF
        if offset == 0x1C:                # ENV3 readout
            return int(self.voices[2].envelope * 255) & 0xFF
        return 0                          # writeable regs read as 0

    def write(self, offset, val):
        offset &= 0x1F
        val &= 0xFF
        self.regs[offset] = val
        if offset < 0x07:
            self.voices[0].write_reg(offset, val)
        elif offset < 0x0E:
            self.voices[1].write_reg(offset - 0x07, val)
        elif offset < 0x15:
            self.voices[2].write_reg(offset - 0x0E, val)
        elif offset == 0x15:                                  # FC LO (3 bits used)
            self.filter_cutoff = (self.filter_cutoff & 0x7F8) | (val & 0x07)
        elif offset == 0x16:                                  # FC HI (8 bits)
            self.filter_cutoff = (self.filter_cutoff & 0x007) | (val << 3)
        elif offset == 0x17:                                  # res/filt routing
            self.filter_resonance = (val >> 4) & 0x0F
            self.filter_routing   = val & 0x0F
        elif offset == 0x18:
            self.master_vol  = val & 0x0F
            # bits 4..6 of $D418 = LP/BP/HP mode; bit 7 = voice-3 disconnect
            self.filter_mode = (val >> 4) & 0x0F

    def tick(self, cycles):
        pass                              # state is sampled at frame boundary

    # ------------------------------------------------------------------
    # Sample generation (vectorised via numpy)
    # ------------------------------------------------------------------

    def generate_samples(self, n_samples, np):
        cycles_per_sample = self.CPU_CLOCK / self.SAMPLE_RATE
        # Generate each voice's (waveform * envelope), keep them separate
        v_out = [self._gen_voice(v, n_samples, np, cycles_per_sample)
                 for v in self.voices]

        # Split into filtered vs direct paths according to $D417 routing
        filter_in = np.zeros(n_samples, dtype=np.float32)
        direct    = np.zeros(n_samples, dtype=np.float32)
        for i, vo in enumerate(v_out):
            if (self.filter_routing >> i) & 1:
                filter_in += vo
            else:
                # Voice 3 disconnect (bit 7 of $D418) removes v3 from the direct
                # path but leaves it available to the filter if routed.
                if i == 2 and (self.filter_mode & 0x08):
                    continue
                direct += vo

        filtered = self._apply_filter(filter_in, n_samples, np)
        out = direct + filtered
        out *= self.master_vol / 15.0 / 3.0
        return out

    def _gen_voice(self, v, n_samples, np, cycles_per_sample):
        """Compute one voice's (waveform * envelope) — vectorised in numpy."""
        phase_step = v.freq * cycles_per_sample
        idx = np.arange(1, n_samples + 1, dtype=np.float64)
        phases = (v.phase + idx * phase_step) % (1 << 24)
        v.phase = float(phases[-1])

        wave = np.zeros(n_samples, dtype=np.float32)
        n_wave = 0
        if v.control & 0x10:          # TRIANGLE
            half = 1 << 23
            tri = np.where(phases < half,
                           phases / (1 << 22) - 1.0,
                           ((1 << 24) - phases) / (1 << 22) - 1.0)
            wave += tri.astype(np.float32); n_wave += 1
        if v.control & 0x20:          # SAWTOOTH
            wave += (phases / (1 << 23) - 1.0).astype(np.float32); n_wave += 1
        if v.control & 0x40:          # PULSE
            wave += np.where((phases.astype(np.int64) >> 12) < v.pulse_width,
                             np.float32(1.0), np.float32(-1.0))
            n_wave += 1
        if v.control & 0x80:          # NOISE
            wave += self._gen_noise(v, n_samples, np, phase_step)
            n_wave += 1
        if n_wave > 1:
            wave /= n_wave

        env = self._envelope_chunk(v, n_samples, np)
        return wave * env

    def _gen_noise(self, v, n_samples, np, phase_step):
        """
        Generate the SID noise waveform for one voice.

        A 23-bit Fibonacci LFSR (feedback = bit22 XOR bit17) is shifted once
        each time the oscillator accumulator advances past a 2^20 boundary
        (i.e. bit 19 goes high), so the shift rate — and therefore the noise's
        spectral character/'pitch' — scales with the voice frequency, exactly
        like the real chip. Between shifts the 8-bit output is held (sample &
        hold), which is why low-frequency noise sounds like a low rumble and
        high-frequency noise like bright hiss, rather than uniform white noise.
        """
        out = np.empty(n_samples, dtype=np.float32)
        lfsr = v.noise_lfsr
        acc = v.noise_acc
        cur = v.noise_out
        BOUND = 1 << 20
        for i in range(n_samples):
            acc += phase_step
            shifted = False
            while acc >= BOUND:
                acc -= BOUND
                fb = ((lfsr >> 22) ^ (lfsr >> 17)) & 1
                lfsr = ((lfsr << 1) | fb) & 0x7FFFFF
                shifted = True
            if shifted:
                # 8-bit output tapped from LFSR bits 22,20,16,13,11,7,4,2
                b = ((((lfsr >> 22) & 1) << 7) | (((lfsr >> 20) & 1) << 6) |
                     (((lfsr >> 16) & 1) << 5) | (((lfsr >> 13) & 1) << 4) |
                     (((lfsr >> 11) & 1) << 3) | (((lfsr >>  7) & 1) << 2) |
                     (((lfsr >>  4) & 1) << 1) |  ((lfsr >>  2) & 1))
                cur = b / 127.5 - 1.0
            out[i] = cur
        v.noise_lfsr = lfsr
        v.noise_acc = acc
        v.noise_out = cur
        return out

    def _apply_filter(self, input_arr, n_samples, np):
        """
        Two-integrator (Chamberlin) state-variable filter approximating the
        SID's analog filter. Outputs of all three modes are summed per the
        $D418 mode bits (bits 4..6 → LP, BP, HP). The cutoff curve is a coarse
        fit to the 6581 — close enough for tunes to sound "right", not exact.
        """
        mode = self.filter_mode & 0x07
        if mode == 0 or self.filter_routing & 0x07 == 0:
            # No mode bits set, OR no voices routed: filter contributes nothing.
            # On the real SID, voices routed to a "mute" filter are inaudible —
            # which is what this returns (direct path is summed separately).
            return np.zeros(n_samples, dtype=np.float32)

        # Cutoff mapping: 11-bit 0..2047 → ~30 Hz .. ~12 kHz, exponential-ish.
        # This approximates the 6581's documented curve well enough for music.
        fc_norm = self.filter_cutoff / 2047.0
        fc_hz   = 30.0 * (12000.0 / 30.0) ** fc_norm
        # SVF coefficient (Chamberlin form). Clamp for numerical stability.
        f = min(2.0 * np.sin(np.pi * fc_hz / self.SAMPLE_RATE), 1.6)
        # Damping: high resonance ⇒ low damping. Range from 1.4 (Q≈0.7) to 0.1 (Q≈10).
        damping = 1.4 - (self.filter_resonance / 15.0) * 1.3

        low  = self._flt_low
        band = self._flt_band
        # Pre-allocate only outputs we need
        want_lp = mode & 0x01
        want_bp = mode & 0x02
        want_hp = mode & 0x04
        lp = np.empty(n_samples, dtype=np.float32) if want_lp else None
        bp = np.empty(n_samples, dtype=np.float32) if want_bp else None
        hp = np.empty(n_samples, dtype=np.float32) if want_hp else None

        # Per-sample SVF recursion. Sequential by nature — can't fully vectorise.
        for i in range(n_samples):
            high = input_arr[i] - low - damping * band
            band += f * high
            low  += f * band
            if want_lp: lp[i] = low
            if want_bp: bp[i] = band
            if want_hp: hp[i] = high

        self._flt_low  = float(low)
        self._flt_band = float(band)

        result = np.zeros(n_samples, dtype=np.float32)
        if lp is not None: result += lp
        if bp is not None: result += bp
        if hp is not None: result += hp
        return result

    def _envelope_chunk(self, v, n_samples, np):
        """Update voice v's envelope across n_samples, return array of values."""
        env = np.empty(n_samples, dtype=np.float32)
        e, state = v.envelope, v.env_state
        sustain = ((v.sustain_release >> 4) & 0x0F) / 15.0
        sr = self.SAMPLE_RATE
        a_rate = 1.0 / (self.ATTACK_TIMES[(v.attack_decay >> 4) & 0x0F] * sr)
        d_rate = ((1.0 - sustain) /
                  (self.DECAY_TIMES[v.attack_decay & 0x0F] * sr)
                  if sustain < 1.0 else 0.0)
        r_rate = 1.0 / (self.DECAY_TIMES[v.sustain_release & 0x0F] * sr)

        for i in range(n_samples):
            if   state == 1:              # attack
                e += a_rate
                if e >= 1.0: e = 1.0; state = 2
            elif state == 2:              # decay
                if e > sustain:
                    e -= d_rate
                    if e <= sustain: e = sustain; state = 3
            elif state == 3:              # sustain
                e = sustain
            elif state == 0:              # release
                if e > 0:
                    e -= r_rate
                    if e < 0: e = 0
            env[i] = e

        v.envelope, v.env_state = float(e), state
        return env


# =============================================================================
# Color RAM ($D800-$DBFF, 4-bit per cell)
# =============================================================================

class ColorRam:
    SIZE = 0x400
    irq_line = False

    def __init__(self):
        self.ram = bytearray(self.SIZE)

    def read(self, offset):  return self.ram[offset & 0x3FF] & 0x0F
    def write(self, offset, val): self.ram[offset & 0x3FF] = val & 0x0F
    def tick(self, cycles):  pass


# =============================================================================
# CIA  (used for CIA1 @ $DC00 and CIA2 @ $DD00)
# =============================================================================

class Cia:
    """
    MOS 6526 CIA — Timer A/B + ports A/B + interrupt control.

    For CIA1, the host frontend populates `keyboard_matrix` with the set of
    pressed (row, col) keys; reading port B then returns the column response
    for whichever rows are currently selected via port A.
    """
    R_PRA = 0x00; R_PRB = 0x01; R_DDRA = 0x02; R_DDRB = 0x03
    R_TA_LO = 0x04; R_TA_HI = 0x05; R_TB_LO = 0x06; R_TB_HI = 0x07
    R_ICR = 0x0D
    R_CRA = 0x0E; R_CRB = 0x0F

    F_TA = 0x01
    F_TB = 0x02
    F_ALARM = 0x04
    F_SP = 0x08
    F_FLAG = 0x10
    F_IR = 0x80

    def __init__(self, name="CIA"):
        self.name = name
        self.regs = bytearray(0x10)
        self.pra = 0xFF; self.prb = 0xFF
        self.ddra = 0x00; self.ddrb = 0x00
        self.port_a_in = 0xFF
        self.port_b_in = 0xFF
        self.timer_a = 0xFFFF
        self.timer_a_latch = 0xFFFF
        self.timer_a_running = False
        self.timer_a_oneshot = False
        self.timer_b = 0xFFFF
        self.timer_b_latch = 0xFFFF
        self.timer_b_running = False
        self.timer_b_oneshot = False
        self.icr_data = 0
        self.icr_mask = 0
        # CIA1-specific: keyboard matrix, set of (row, col) for pressed keys
        self.keyboard_matrix = set()
        # CIA1-specific: joystick state. joystick_state[0] = port 1, [1] = port 2.
        # Each byte's bits 0-4 = up/down/left/right/fire, where 1 = PRESSED in
        # our internal convention. We invert when reading via CIA ports
        # (the real C64 lines are pulled LOW when pressed).
        self.joystick_state = [0, 0]

    @property
    def irq_line(self):
        return (self.icr_data & self.icr_mask & 0x1F) != 0

    def _scan_ports(self):
        """Resolve the keyboard matrix and joysticks into the electrical pin
        states of port A and port B.

        Each pressed key at (pa_bit, pb_bit) wires port-A line pa_bit to
        port-B line pb_bit; a line driven low on one side pulls the connected
        input line on the other side low. This supports BOTH scan directions:
        the normal one (drive columns on port A, read rows on port B) and the
        reverse one (drive rows on port B, read columns on port A) that some
        games — e.g. Bruce Lee's title menu — use to detect keypresses.
        """
        # Pin state ignoring the matrix: output bits drive their register
        # value, input bits are pulled high.
        a = ((self.pra & self.ddra) | (self.port_a_in & ~self.ddra)) & 0xFF
        b = ((self.prb & self.ddrb) | (self.port_b_in & ~self.ddrb)) & 0xFF
        # Joystick switches short port pins directly to ground.
        a &= ~self.joystick_state[1] & 0xFF   # joystick 2 on port A
        b &= ~self.joystick_state[0] & 0xFF   # joystick 1 on port B
        if self.keyboard_matrix:
            # A pressed key only pulls a line low if that line is an input
            # (an output driving high is not overridden). Iterate to a
            # fixpoint so keys sharing lines resolve correctly.
            for _ in range(8):
                changed = False
                for pa_bit, pb_bit in self.keyboard_matrix:
                    a_low = not ((a >> pa_bit) & 1)
                    b_low = not ((b >> pb_bit) & 1)
                    a_in = not ((self.ddra >> pa_bit) & 1)
                    b_in = not ((self.ddrb >> pb_bit) & 1)
                    if a_low and not b_low and b_in:
                        b &= ~(1 << pb_bit) & 0xFF
                        changed = True
                    elif b_low and not a_low and a_in:
                        a &= ~(1 << pa_bit) & 0xFF
                        changed = True
                if not changed:
                    break
        return a, b

    def _read_port_a(self):
        return self._scan_ports()[0]

    def _read_port_b(self):
        return self._scan_ports()[1]

    def read(self, offset):
        offset &= 0x0F
        if offset == self.R_PRA:    return self._read_port_a()
        if offset == self.R_PRB:    return self._read_port_b()
        if offset == self.R_DDRA:   return self.ddra
        if offset == self.R_DDRB:   return self.ddrb
        if offset == self.R_TA_LO:  return self.timer_a & 0xFF
        if offset == self.R_TA_HI:  return (self.timer_a >> 8) & 0xFF
        if offset == self.R_TB_LO:  return self.timer_b & 0xFF
        if offset == self.R_TB_HI:  return (self.timer_b >> 8) & 0xFF
        if offset == self.R_ICR:
            v = self.icr_data
            if self.irq_line:
                v |= self.F_IR
            self.icr_data = 0
            return v
        return self.regs[offset]

    def write(self, offset, val):
        offset &= 0x0F
        val &= 0xFF
        if offset == self.R_PRA:    self.pra = val
        elif offset == self.R_PRB:  self.prb = val
        elif offset == self.R_DDRA: self.ddra = val
        elif offset == self.R_DDRB: self.ddrb = val
        elif offset == self.R_TA_LO: self.timer_a_latch = (self.timer_a_latch & 0xFF00) | val
        elif offset == self.R_TA_HI: self.timer_a_latch = (self.timer_a_latch & 0x00FF) | (val << 8)
        elif offset == self.R_TB_LO: self.timer_b_latch = (self.timer_b_latch & 0xFF00) | val
        elif offset == self.R_TB_HI: self.timer_b_latch = (self.timer_b_latch & 0x00FF) | (val << 8)
        elif offset == self.R_ICR:
            if val & 0x80: self.icr_mask |= (val & 0x1F)
            else:          self.icr_mask &= ~(val & 0x1F)
        elif offset == self.R_CRA:
            self.regs[offset] = val
            self.timer_a_running = (val & 0x01) != 0
            self.timer_a_oneshot = (val & 0x08) != 0
            if val & 0x10:
                self.timer_a = self.timer_a_latch
        elif offset == self.R_CRB:
            self.regs[offset] = val
            self.timer_b_running = (val & 0x01) != 0
            self.timer_b_oneshot = (val & 0x08) != 0
            if val & 0x10:
                self.timer_b = self.timer_b_latch
        else:
            self.regs[offset] = val

    def tick(self, cycles):
        if self.timer_a_running:
            self.timer_a -= cycles
            if self.timer_a <= 0:
                self.icr_data |= self.F_TA
                if self.timer_a_oneshot:
                    self.timer_a_running = False
                    self.timer_a = self.timer_a_latch
                else:
                    self.timer_a += self.timer_a_latch + 1
                    if self.timer_a <= 0:
                        self.timer_a = self.timer_a_latch or 0xFFFF
        if self.timer_b_running:
            self.timer_b -= cycles
            if self.timer_b <= 0:
                self.icr_data |= self.F_TB
                if self.timer_b_oneshot:
                    self.timer_b_running = False
                    self.timer_b = self.timer_b_latch
                else:
                    self.timer_b += self.timer_b_latch + 1
                    if self.timer_b <= 0:
                        self.timer_b = self.timer_b_latch or 0xFFFF


# =============================================================================
# Memory — dispatches to RAM, ROM, or chips per PLA state
# =============================================================================

class Memory:
    SIZE = 0x10000

    def __init__(self, basic_rom=None, char_rom=None, kernal_rom=None,
                 vic=None, sid=None, color_ram=None, cia1=None, cia2=None):
        self.ram = bytearray(self.SIZE)
        self.rom = bytearray(self.SIZE)
        self.pla = Pla()
        self.vic       = vic       if vic       is not None else Vic()
        self.sid       = sid       if sid       is not None else Sid()
        self.color_ram = color_ram if color_ram is not None else ColorRam()
        self.cia1      = cia1      if cia1      is not None else Cia("CIA1")
        self.cia2      = cia2      if cia2      is not None else Cia("CIA2")
        if basic_rom  is not None: self._load_rom(Config.ADDR_BASIC_ROM_START,     basic_rom)
        if char_rom   is not None: self._load_rom(Config.ADDR_CHARACTER_ROM_START, char_rom)
        if kernal_rom is not None: self._load_rom(Config.ADDR_KERNAL_ROM_START,    kernal_rom)
        self.reset()

    def reset(self):
        self.pla.reset()
        self.ram[Config.ADDR_PROCESSOR_PORT_REG] = self.pla.prozessorport

    # --- direct access ---

    def read_ram_direct(self, addr):
        if 0 <= addr < self.SIZE:
            return self.ram[addr]
        return 0

    def write_ram_direct(self, addr, val):
        if 0 <= addr < self.SIZE:
            self.ram[addr] = val & 0xFF

    def read_rom_direct(self, addr):
        if 0 <= addr < self.SIZE:
            return self.rom[addr]
        return 0

    def _load_rom(self, start, data):
        end = min(start + len(data), self.SIZE)
        self.rom[start:end] = data[: end - start]

    def load_ram(self, start, data):
        end = min(start + len(data), self.SIZE)
        self.ram[start:end] = data[: end - start]

    # --- VIC view of memory (bank-switched) ---

    def vic_bank(self):
        """Return the current VIC bank (0..3). Selected via CIA2 port A bits 0,1
        (inverted: 0b11 = bank 0, 0b00 = bank 3)."""
        return 3 - (self.cia2.pra & 0x03)

    def read_vic(self, addr):
        """
        Read a byte from the VIC's 14-bit address space.
        Banks 0 and 2 expose the character ROM at VIC offset $1000-$1FFF
        regardless of what RAM is there.
        """
        addr &= 0x3FFF
        bank = self.vic_bank()
        if bank in (0, 2) and 0x1000 <= addr < 0x2000:
            return self.rom[0xD000 + (addr & 0x0FFF)]
        return self.ram[(bank * 0x4000) + addr]

    def read_vic_bytes(self, addr, n):
        """Read n bytes via VIC view as a Python bytes object."""
        return bytes(self.read_vic(addr + i) for i in range(n))

    # --- system access ---

    def read_system_byte(self, addr):
        addr &= 0xFFFF
        if 0xD000 <= addr <= 0xDFFF:
            space = self.pla.address_space(addr)
            if space == AddressSpace.CHARSET_ROM:
                return self.read_rom_direct(addr)
            if space == AddressSpace.IO:
                if addr < 0xD400: return self.vic.read(addr - 0xD000)
                if addr < 0xD800: return self.sid.read(addr - 0xD400)
                if addr < 0xDC00: return self.color_ram.read(addr - 0xD800)
                if addr < 0xDD00: return self.cia1.read(addr - 0xDC00)
                if addr < 0xDE00: return self.cia2.read(addr - 0xDD00)
                return 0xFF
            return self.read_ram_direct(addr)
        if 0xA000 <= addr <= 0xBFFF:
            if self.pla.address_space(addr) == AddressSpace.BASIC_ROM:
                return self.read_rom_direct(addr)
            return self.read_ram_direct(addr)
        if 0xE000 <= addr <= 0xFFFF:
            if self.pla.address_space(addr) == AddressSpace.KERNAL_ROM:
                return self.read_rom_direct(addr)
            return self.read_ram_direct(addr)
        return self.read_ram_direct(addr)

    def write_system_byte(self, addr, val):
        addr &= 0xFFFF
        val &= 0xFF
        if addr == Config.ADDR_PROCESSOR_PORT_REG:
            self.pla.prozessorport = val
            self.write_ram_direct(addr, val)
            return
        if 0xD000 <= addr <= 0xDFFF:
            space = self.pla.address_space(addr)
            if space == AddressSpace.IO:
                if   addr < 0xD400: self.vic.write(addr - 0xD000, val)
                elif addr < 0xD800: self.sid.write(addr - 0xD400, val)
                elif addr < 0xDC00: self.color_ram.write(addr - 0xD800, val)
                elif addr < 0xDD00: self.cia1.write(addr - 0xDC00, val)
                elif addr < 0xDE00: self.cia2.write(addr - 0xDD00, val)
                return
            self.write_ram_direct(addr, val)
            return
        self.write_ram_direct(addr, val)

    def read_system_word(self, addr):
        lo = self.read_system_byte(addr)
        hi = self.read_system_byte(addr + 1)
        return make_word(lo, hi)

    def write_system_word(self, addr, val):
        self.write_system_byte(addr, low_byte(val))
        self.write_system_byte(addr + 1, high_byte(val))


# =============================================================================
# MOS 6502 CPU
# =============================================================================

class CPU:
    """
    MOS 6502 emulator.

    Status register layout (bit -> flag):
      7 N   negative
      6 V   overflow
      5 -   always 1 (when read)
      4 B   break (always 1 in pushed copies and via PHP)
      3 D   decimal mode
      2 I   interrupt disable
      1 Z   zero
      0 C   carry
    """

    FN, FV, FB, FD, FI, FZ, FC = 7, 6, 4, 3, 2, 1, 0

    def __init__(self, memory):
        self.mem = memory
        self.reg_a = 0
        self.reg_x = 0
        self.reg_y = 0
        self.reg_sr = 0
        self.reg_sp = 0
        self.reg_pc = 0
        self.cycles = 0
        self.irq_line = False
        self.nmi_pending = False
        self._prev_nmi = False
        # PC-traps: {address: callable()}. When PC == address at step boundary,
        # the callable runs instead of normal instruction fetch. Used for
        # KERNAL routine interception (LOAD trap etc.).
        self.traps = {}
        self._build_dispatch()
        self.reset()
        self.trace = False

    def reset(self):
        self.reg_a = 0
        self.reg_x = 0
        self.reg_y = 0
        self.reg_sp = 0xFD
        self.reg_sr = 0
        self.reg_pc = self.mem.read_system_word(Config.ADDR_RESET_VECTOR)
        self.cycles = 0

    # ---------- register accessors ----------

    @property
    def pc(self): return self.reg_pc & 0xFFFF
    @pc.setter
    def pc(self, v): self.reg_pc = v & 0xFFFF

    @property
    def sr(self): return ((self.reg_sr & 0xFF) | 0x30)
    @sr.setter
    def sr(self, v): self.reg_sr = v & 0xFF

    @property
    def sp(self): return self.reg_sp & 0xFF
    @sp.setter
    def sp(self, v): self.reg_sp = v & 0xFF

    @property
    def a(self): return self.reg_a & 0xFF
    @a.setter
    def a(self, v): self.reg_a = v & 0xFF

    @property
    def x(self): return self.reg_x & 0xFF
    @x.setter
    def x(self, v): self.reg_x = v & 0xFF

    @property
    def y(self): return self.reg_y & 0xFF
    @y.setter
    def y(self, v): self.reg_y = v & 0xFF

    # ---------- flags ----------

    def get_flag(self, bit):       return test_bit(self.reg_sr, bit)
    def set_flag(self, bit, val):  self.reg_sr = set_bit(self.reg_sr, bit, val) & 0xFF

    def get_flag_n(self): return self.get_flag(self.FN)
    def get_flag_v(self): return self.get_flag(self.FV)
    def get_flag_b(self): return self.get_flag(self.FB)
    def get_flag_d(self): return self.get_flag(self.FD)
    def get_flag_i(self): return self.get_flag(self.FI)
    def get_flag_z(self): return self.get_flag(self.FZ)
    def get_flag_c(self): return self.get_flag(self.FC)

    def update_nz(self, val):
        val &= 0xFF
        self.set_flag(self.FN, (val & 0x80) != 0)
        self.set_flag(self.FZ, val == 0)

    # ---------- stack ----------

    def push(self, val):
        self.mem.write_system_byte(Config.ADDR_BASE_STACK + self.sp, val)
        self.sp = (self.sp - 1) & 0xFF

    def pop(self):
        self.sp = (self.sp + 1) & 0xFF
        return self.mem.read_system_byte(Config.ADDR_BASE_STACK + self.sp)

    # ---------- fetch ----------

    def fetch_byte(self):
        v = self.mem.read_system_byte(self.pc)
        self.pc = self.pc + 1
        return v

    def fetch_word(self):
        lo = self.fetch_byte()
        hi = self.fetch_byte()
        return make_word(lo, hi)

    # ---------- addressing modes ----------

    def _imm(self):    return self.fetch_byte()
    def _zp(self):     return self.fetch_byte()
    def _zp_x(self):   return (self.fetch_byte() + self.x) & 0xFF
    def _zp_y(self):   return (self.fetch_byte() + self.y) & 0xFF
    def _abs(self):    return self.fetch_word()
    def _abs_x(self):  return (self.fetch_word() + self.x) & 0xFFFF
    def _abs_y(self):  return (self.fetch_word() + self.y) & 0xFFFF

    def _ind_x(self):
        zp = (self.fetch_byte() + self.x) & 0xFF
        lo = self.mem.read_system_byte(zp)
        hi = self.mem.read_system_byte((zp + 1) & 0xFF)
        return make_word(lo, hi)

    def _ind_y(self):
        zp = self.fetch_byte()
        lo = self.mem.read_system_byte(zp)
        hi = self.mem.read_system_byte((zp + 1) & 0xFF)
        return (make_word(lo, hi) + self.y) & 0xFFFF

    # ---------- arithmetic / logic ----------

    def _adc(self, val, cycles):
        a = self.a
        carry_in = 1 if self.get_flag_c() else 0
        if self.get_flag_d():
            lo = (a & 0x0F) + (val & 0x0F) + carry_in
            hi = (a >> 4) + (val >> 4)
            if lo > 9:
                lo += 6
                hi += 1
            bin_res = (a + val + carry_in) & 0xFF
            self.set_flag(self.FN, (hi & 0x08) != 0)
            self.set_flag(self.FV,
                ((a ^ val) & 0x80 == 0) and ((a ^ (hi << 4)) & 0x80 != 0))
            if hi > 9:
                hi += 6
            self.set_flag(self.FC, hi > 15)
            res = ((hi << 4) | (lo & 0x0F)) & 0xFF
            self.set_flag(self.FZ, bin_res == 0)
            self.a = res
        else:
            total = a + val + carry_in
            res = total & 0xFF
            self.set_flag(self.FC, total > 0xFF)
            self.set_flag(self.FV,
                ((a ^ val) & 0x80 == 0) and ((a ^ res) & 0x80 != 0))
            self.a = res
            self.update_nz(res)
        self.cycles += cycles

    def _sbc(self, val, cycles):
        if self.get_flag_d():
            a = self.a
            carry_in = 1 if self.get_flag_c() else 0
            lo = (a & 0x0F) - (val & 0x0F) - (1 - carry_in)
            hi = (a >> 4) - (val >> 4)
            if lo < 0:
                lo -= 6
                hi -= 1
            if hi < 0:
                hi -= 6
            bin_total = a - val - (1 - carry_in)
            self.set_flag(self.FC, bin_total >= 0)
            res = ((hi << 4) | (lo & 0x0F)) & 0xFF
            self.set_flag(self.FV,
                ((a ^ val) & 0x80 != 0) and ((a ^ (bin_total & 0xFF)) & 0x80 != 0))
            self.update_nz(bin_total & 0xFF)
            self.set_flag(self.FZ, (bin_total & 0xFF) == 0)
            self.a = res
            self.cycles += cycles
        else:
            self._adc(val ^ 0xFF, cycles)

    def _and(self, val, cycles):
        self.a = self.a & val; self.update_nz(self.a); self.cycles += cycles

    def _ora(self, val, cycles):
        self.a = self.a | val; self.update_nz(self.a); self.cycles += cycles

    def _eor(self, val, cycles):
        self.a = self.a ^ val; self.update_nz(self.a); self.cycles += cycles

    def _bit(self, adr, cycles):
        val = self.mem.read_system_byte(adr)
        self.set_flag(self.FN, (val & 0x80) != 0)
        self.set_flag(self.FV, (val & 0x40) != 0)
        self.set_flag(self.FZ, (val & self.a) == 0)
        self.cycles += cycles

    def _cmp_reg(self, reg_val, val, cycles):
        res = (reg_val - (val & 0xFF)) & 0xFF
        self.set_flag(self.FC, reg_val >= (val & 0xFF))
        self.update_nz(res)
        self.cycles += cycles

    # ---------- shifts ----------

    def _asl(self, val):
        self.set_flag(self.FC, (val & 0x80) != 0)
        val = (val << 1) & 0xFF
        self.update_nz(val)
        return val

    def _lsr(self, val):
        self.set_flag(self.FC, (val & 1) != 0)
        val = (val >> 1) & 0x7F
        self.update_nz(val)
        return val

    def _rol(self, val):
        old_c = 1 if self.get_flag_c() else 0
        self.set_flag(self.FC, (val & 0x80) != 0)
        val = ((val << 1) & 0xFE) | old_c
        self.update_nz(val)
        return val

    def _ror(self, val):
        old_c = 0x80 if self.get_flag_c() else 0
        self.set_flag(self.FC, (val & 1) != 0)
        val = (val >> 1) | old_c
        self.update_nz(val)
        return val

    def _rmw(self, adr, fn, cycles):
        val = self.mem.read_system_byte(adr)
        self.mem.write_system_byte(adr, val)
        new = fn(val)
        self.mem.write_system_byte(adr, new)
        self.cycles += cycles

    # ---------- inc/dec ----------

    def _inc_mem(self, adr, cycles):
        val = self.mem.read_system_byte(adr)
        self.mem.write_system_byte(adr, val)
        val = (val + 1) & 0xFF
        self.mem.write_system_byte(adr, val)
        self.update_nz(val)
        self.cycles += cycles

    def _dec_mem(self, adr, cycles):
        val = self.mem.read_system_byte(adr)
        self.mem.write_system_byte(adr, val)
        val = (val - 1) & 0xFF
        self.mem.write_system_byte(adr, val)
        self.update_nz(val)
        self.cycles += cycles

    # ---------- branches ----------

    def _branch(self, take):
        offset = self.fetch_byte()
        self.cycles += 2
        if take:
            self.cycles += 1
            target = (self.pc + signed_byte(offset)) & 0xFFFF
            if (target & 0xFF00) != (self.pc & 0xFF00):
                self.cycles += 1
            self.pc = target

    # ---------- BRK / RTI / JSR / RTS / JMP indirect ----------

    def _brk(self):
        self.fetch_byte()
        self.push(high_byte(self.pc))
        self.push(low_byte(self.pc))
        self.push((self.reg_sr | 0x30) & 0xFF)
        self.set_flag(self.FI, True)
        self.pc = self.mem.read_system_word(Config.ADDR_IRQ_VECTOR)
        self.cycles += 7

    def _rti(self):
        self.reg_sr = self.pop() & 0xCF
        lo = self.pop()
        hi = self.pop()
        self.pc = make_word(lo, hi)
        self.cycles += 6

    def _jsr(self):
        target = self._abs()
        ret = (self.pc - 1) & 0xFFFF
        self.push(high_byte(ret))
        self.push(low_byte(ret))
        self.pc = target
        self.cycles += 6

    def _rts(self):
        lo = self.pop()
        hi = self.pop()
        self.pc = (make_word(lo, hi) + 1) & 0xFFFF
        self.cycles += 6

    def _jmp_indirect(self):
        ptr = self._abs()
        lo = self.mem.read_system_byte(ptr)
        hi_addr = (ptr & 0xFF00) | ((ptr + 1) & 0xFF)
        hi = self.mem.read_system_byte(hi_addr)
        self.pc = make_word(lo, hi)
        self.cycles += 5

    # ---------- IRQ / NMI ----------

    def _service_irq(self, vector_addr):
        self.push(high_byte(self.pc))
        self.push(low_byte(self.pc))
        self.push((self.reg_sr & 0xEF) | 0x20)
        self.set_flag(self.FI, True)
        self.pc = self.mem.read_system_word(vector_addr)
        self.cycles += 7

    def irq(self):
        if not self.get_flag_i():
            self._service_irq(Config.ADDR_IRQ_VECTOR)

    def nmi(self):
        self._service_irq(Config.ADDR_NMI_VECTOR)

    # ---------- dispatch table ----------

    def _build_dispatch(self):
        M = self.mem
        d = [None] * 256

        # ORA
        d[0x09] = lambda: self._ora(self._imm(), 2)
        d[0x05] = lambda: self._ora(M.read_system_byte(self._zp()), 3)
        d[0x15] = lambda: self._ora(M.read_system_byte(self._zp_x()), 4)
        d[0x0D] = lambda: self._ora(M.read_system_byte(self._abs()), 4)
        d[0x1D] = lambda: self._ora(M.read_system_byte(self._abs_x()), 4)
        d[0x19] = lambda: self._ora(M.read_system_byte(self._abs_y()), 4)
        d[0x01] = lambda: self._ora(M.read_system_byte(self._ind_x()), 6)
        d[0x11] = lambda: self._ora(M.read_system_byte(self._ind_y()), 5)

        # AND
        d[0x29] = lambda: self._and(self._imm(), 2)
        d[0x25] = lambda: self._and(M.read_system_byte(self._zp()), 3)
        d[0x35] = lambda: self._and(M.read_system_byte(self._zp_x()), 4)
        d[0x2D] = lambda: self._and(M.read_system_byte(self._abs()), 4)
        d[0x3D] = lambda: self._and(M.read_system_byte(self._abs_x()), 4)
        d[0x39] = lambda: self._and(M.read_system_byte(self._abs_y()), 4)
        d[0x21] = lambda: self._and(M.read_system_byte(self._ind_x()), 6)
        d[0x31] = lambda: self._and(M.read_system_byte(self._ind_y()), 5)

        # EOR
        d[0x49] = lambda: self._eor(self._imm(), 2)
        d[0x45] = lambda: self._eor(M.read_system_byte(self._zp()), 3)
        d[0x55] = lambda: self._eor(M.read_system_byte(self._zp_x()), 4)
        d[0x4D] = lambda: self._eor(M.read_system_byte(self._abs()), 4)
        d[0x5D] = lambda: self._eor(M.read_system_byte(self._abs_x()), 4)
        d[0x59] = lambda: self._eor(M.read_system_byte(self._abs_y()), 4)
        d[0x41] = lambda: self._eor(M.read_system_byte(self._ind_x()), 6)
        d[0x51] = lambda: self._eor(M.read_system_byte(self._ind_y()), 5)

        # ADC
        d[0x69] = lambda: self._adc(self._imm(), 2)
        d[0x65] = lambda: self._adc(M.read_system_byte(self._zp()), 3)
        d[0x75] = lambda: self._adc(M.read_system_byte(self._zp_x()), 4)
        d[0x6D] = lambda: self._adc(M.read_system_byte(self._abs()), 4)
        d[0x7D] = lambda: self._adc(M.read_system_byte(self._abs_x()), 4)
        d[0x79] = lambda: self._adc(M.read_system_byte(self._abs_y()), 4)
        d[0x61] = lambda: self._adc(M.read_system_byte(self._ind_x()), 6)
        d[0x71] = lambda: self._adc(M.read_system_byte(self._ind_y()), 5)

        # SBC
        d[0xE9] = lambda: self._sbc(self._imm(), 2)
        d[0xE5] = lambda: self._sbc(M.read_system_byte(self._zp()), 3)
        d[0xF5] = lambda: self._sbc(M.read_system_byte(self._zp_x()), 4)
        d[0xED] = lambda: self._sbc(M.read_system_byte(self._abs()), 4)
        d[0xFD] = lambda: self._sbc(M.read_system_byte(self._abs_x()), 4)
        d[0xF9] = lambda: self._sbc(M.read_system_byte(self._abs_y()), 4)
        d[0xE1] = lambda: self._sbc(M.read_system_byte(self._ind_x()), 6)
        d[0xF1] = lambda: self._sbc(M.read_system_byte(self._ind_y()), 5)

        # CMP / CPX / CPY
        d[0xC9] = lambda: self._cmp_reg(self.a, self._imm(), 2)
        d[0xC5] = lambda: self._cmp_reg(self.a, M.read_system_byte(self._zp()), 3)
        d[0xD5] = lambda: self._cmp_reg(self.a, M.read_system_byte(self._zp_x()), 4)
        d[0xCD] = lambda: self._cmp_reg(self.a, M.read_system_byte(self._abs()), 4)
        d[0xDD] = lambda: self._cmp_reg(self.a, M.read_system_byte(self._abs_x()), 4)
        d[0xD9] = lambda: self._cmp_reg(self.a, M.read_system_byte(self._abs_y()), 4)
        d[0xC1] = lambda: self._cmp_reg(self.a, M.read_system_byte(self._ind_x()), 6)
        d[0xD1] = lambda: self._cmp_reg(self.a, M.read_system_byte(self._ind_y()), 5)
        d[0xE0] = lambda: self._cmp_reg(self.x, self._imm(), 2)
        d[0xE4] = lambda: self._cmp_reg(self.x, M.read_system_byte(self._zp()), 3)
        d[0xEC] = lambda: self._cmp_reg(self.x, M.read_system_byte(self._abs()), 4)
        d[0xC0] = lambda: self._cmp_reg(self.y, self._imm(), 2)
        d[0xC4] = lambda: self._cmp_reg(self.y, M.read_system_byte(self._zp()), 3)
        d[0xCC] = lambda: self._cmp_reg(self.y, M.read_system_byte(self._abs()), 4)

        # BIT
        d[0x24] = lambda: self._bit(self._zp(), 3)
        d[0x2C] = lambda: self._bit(self._abs(), 4)

        # LDA / LDX / LDY
        d[0xA9] = lambda: (setattr(self, 'a', self._imm()), self.update_nz(self.a), self._tick(2))
        d[0xA5] = lambda: self._lda_from(self._zp(), 3)
        d[0xB5] = lambda: self._lda_from(self._zp_x(), 4)
        d[0xAD] = lambda: self._lda_from(self._abs(), 4)
        d[0xBD] = lambda: self._lda_from(self._abs_x(), 4)
        d[0xB9] = lambda: self._lda_from(self._abs_y(), 4)
        d[0xA1] = lambda: self._lda_from(self._ind_x(), 6)
        d[0xB1] = lambda: self._lda_from(self._ind_y(), 5)

        d[0xA2] = lambda: (setattr(self, 'x', self._imm()), self.update_nz(self.x), self._tick(2))
        d[0xA6] = lambda: self._ldx_from(self._zp(), 3)
        d[0xB6] = lambda: self._ldx_from(self._zp_y(), 4)
        d[0xAE] = lambda: self._ldx_from(self._abs(), 4)
        d[0xBE] = lambda: self._ldx_from(self._abs_y(), 4)

        d[0xA0] = lambda: (setattr(self, 'y', self._imm()), self.update_nz(self.y), self._tick(2))
        d[0xA4] = lambda: self._ldy_from(self._zp(), 3)
        d[0xB4] = lambda: self._ldy_from(self._zp_x(), 4)
        d[0xAC] = lambda: self._ldy_from(self._abs(), 4)
        d[0xBC] = lambda: self._ldy_from(self._abs_x(), 4)

        # STA / STX / STY
        d[0x85] = lambda: self._sta_at(self._zp(), 3)
        d[0x95] = lambda: self._sta_at(self._zp_x(), 4)
        d[0x8D] = lambda: self._sta_at(self._abs(), 4)
        d[0x9D] = lambda: self._sta_at(self._abs_x(), 5)
        d[0x99] = lambda: self._sta_at(self._abs_y(), 5)
        d[0x81] = lambda: self._sta_at(self._ind_x(), 6)
        d[0x91] = lambda: self._sta_at(self._ind_y(), 6)

        d[0x86] = lambda: self._stx_at(self._zp(), 3)
        d[0x96] = lambda: self._stx_at(self._zp_y(), 4)
        d[0x8E] = lambda: self._stx_at(self._abs(), 4)

        d[0x84] = lambda: self._sty_at(self._zp(), 3)
        d[0x94] = lambda: self._sty_at(self._zp_x(), 4)
        d[0x8C] = lambda: self._sty_at(self._abs(), 4)

        # Inc/Dec
        d[0xE6] = lambda: self._inc_mem(self._zp(), 5)
        d[0xF6] = lambda: self._inc_mem(self._zp_x(), 6)
        d[0xEE] = lambda: self._inc_mem(self._abs(), 6)
        d[0xFE] = lambda: self._inc_mem(self._abs_x(), 7)
        d[0xC6] = lambda: self._dec_mem(self._zp(), 5)
        d[0xD6] = lambda: self._dec_mem(self._zp_x(), 6)
        d[0xCE] = lambda: self._dec_mem(self._abs(), 6)
        d[0xDE] = lambda: self._dec_mem(self._abs_x(), 7)

        d[0xE8] = lambda: self._inx()
        d[0xC8] = lambda: self._iny()
        d[0xCA] = lambda: self._dex()
        d[0x88] = lambda: self._dey()

        # Shifts/rotates accumulator
        d[0x0A] = lambda: (setattr(self, 'a', self._asl(self.a)), self._tick(2))
        d[0x4A] = lambda: (setattr(self, 'a', self._lsr(self.a)), self._tick(2))
        d[0x2A] = lambda: (setattr(self, 'a', self._rol(self.a)), self._tick(2))
        d[0x6A] = lambda: (setattr(self, 'a', self._ror(self.a)), self._tick(2))

        # Shifts/rotates memory
        d[0x06] = lambda: self._rmw(self._zp(),    self._asl, 5)
        d[0x16] = lambda: self._rmw(self._zp_x(),  self._asl, 6)
        d[0x0E] = lambda: self._rmw(self._abs(),   self._asl, 6)
        d[0x1E] = lambda: self._rmw(self._abs_x(), self._asl, 7)
        d[0x46] = lambda: self._rmw(self._zp(),    self._lsr, 5)
        d[0x56] = lambda: self._rmw(self._zp_x(),  self._lsr, 6)
        d[0x4E] = lambda: self._rmw(self._abs(),   self._lsr, 6)
        d[0x5E] = lambda: self._rmw(self._abs_x(), self._lsr, 7)
        d[0x26] = lambda: self._rmw(self._zp(),    self._rol, 5)
        d[0x36] = lambda: self._rmw(self._zp_x(),  self._rol, 6)
        d[0x2E] = lambda: self._rmw(self._abs(),   self._rol, 6)
        d[0x3E] = lambda: self._rmw(self._abs_x(), self._rol, 7)
        d[0x66] = lambda: self._rmw(self._zp(),    self._ror, 5)
        d[0x76] = lambda: self._rmw(self._zp_x(),  self._ror, 6)
        d[0x6E] = lambda: self._rmw(self._abs(),   self._ror, 6)
        d[0x7E] = lambda: self._rmw(self._abs_x(), self._ror, 7)

        # Transfers
        d[0xAA] = lambda: (setattr(self, 'x', self.a), self.update_nz(self.x), self._tick(2))
        d[0xA8] = lambda: (setattr(self, 'y', self.a), self.update_nz(self.y), self._tick(2))
        d[0x8A] = lambda: (setattr(self, 'a', self.x), self.update_nz(self.a), self._tick(2))
        d[0x98] = lambda: (setattr(self, 'a', self.y), self.update_nz(self.a), self._tick(2))
        d[0x9A] = lambda: (setattr(self, 'sp', self.x), self._tick(2))
        d[0xBA] = lambda: (setattr(self, 'x', self.sp), self.update_nz(self.x), self._tick(2))

        # Stack
        d[0x48] = lambda: (self.push(self.a), self._tick(3))
        d[0x68] = lambda: (setattr(self, 'a', self.pop()), self.update_nz(self.a), self._tick(4))
        d[0x08] = lambda: (self.push((self.reg_sr | 0x30) & 0xFF), self._tick(3))
        d[0x28] = lambda: (setattr(self, 'reg_sr', self.pop() & 0xCF), self._tick(4))

        # Flags
        d[0x18] = lambda: (self.set_flag(self.FC, False), self._tick(2))
        d[0x38] = lambda: (self.set_flag(self.FC, True),  self._tick(2))
        d[0x58] = lambda: (self.set_flag(self.FI, False), self._tick(2))
        d[0x78] = lambda: (self.set_flag(self.FI, True),  self._tick(2))
        d[0xB8] = lambda: (self.set_flag(self.FV, False), self._tick(2))
        d[0xD8] = lambda: (self.set_flag(self.FD, False), self._tick(2))
        d[0xF8] = lambda: (self.set_flag(self.FD, True),  self._tick(2))

        # Branches
        d[0x10] = lambda: self._branch(not self.get_flag_n())   # BPL
        d[0x30] = lambda: self._branch(self.get_flag_n())       # BMI
        d[0x50] = lambda: self._branch(not self.get_flag_v())   # BVC
        d[0x70] = lambda: self._branch(self.get_flag_v())       # BVS
        d[0x90] = lambda: self._branch(not self.get_flag_c())   # BCC
        d[0xB0] = lambda: self._branch(self.get_flag_c())       # BCS
        d[0xD0] = lambda: self._branch(not self.get_flag_z())   # BNE
        d[0xF0] = lambda: self._branch(self.get_flag_z())       # BEQ

        # Jumps
        d[0x4C] = lambda: (setattr(self, 'pc', self._abs()), self._tick(3))
        d[0x6C] = lambda: self._jmp_indirect()
        d[0x20] = lambda: self._jsr()
        d[0x60] = lambda: self._rts()
        d[0x00] = lambda: self._brk()
        d[0x40] = lambda: self._rti()
        d[0xEA] = lambda: self._tick(2)

        # ----- NMOS 6502 illegal / undocumented opcodes -----
        # These are stable side-effect combinations of two legal operations on
        # the same value. Real NMOS chips execute them reliably and cracked
        # games / demos often use them for code-size optimization. We implement
        # the stable ones; the genuinely unstable ones ($8B XAA, $AB LAX#imm,
        # $93/$9B/$9C/$9E/$9F SH*) are mapped to NOPs as a defensive default.

        # SAX  = store (A & X), no flags
        d[0x87] = lambda: self._sax_at(self._zp(),    3)
        d[0x97] = lambda: self._sax_at(self._zp_y(),  4)
        d[0x83] = lambda: self._sax_at(self._ind_x(), 6)
        d[0x8F] = lambda: self._sax_at(self._abs(),   4)

        # LAX  = LDA + LDX simultaneously
        d[0xA7] = lambda: self._lax_from(self._zp(),    3)
        d[0xB7] = lambda: self._lax_from(self._zp_y(),  4)
        d[0xA3] = lambda: self._lax_from(self._ind_x(), 6)
        d[0xB3] = lambda: self._lax_from(self._ind_y(), 5)
        d[0xAF] = lambda: self._lax_from(self._abs(),   4)
        d[0xBF] = lambda: self._lax_from(self._abs_y(), 4)

        # SLO  = ASL memory, then ORA result into A
        d[0x07] = lambda: self._slo(self._zp(),    5)
        d[0x17] = lambda: self._slo(self._zp_x(),  6)
        d[0x03] = lambda: self._slo(self._ind_x(), 8)
        d[0x13] = lambda: self._slo(self._ind_y(), 8)
        d[0x0F] = lambda: self._slo(self._abs(),   6)
        d[0x1F] = lambda: self._slo(self._abs_x(), 7)
        d[0x1B] = lambda: self._slo(self._abs_y(), 7)

        # RLA  = ROL memory, then AND result into A
        d[0x27] = lambda: self._rla(self._zp(),    5)
        d[0x37] = lambda: self._rla(self._zp_x(),  6)
        d[0x23] = lambda: self._rla(self._ind_x(), 8)
        d[0x33] = lambda: self._rla(self._ind_y(), 8)
        d[0x2F] = lambda: self._rla(self._abs(),   6)
        d[0x3F] = lambda: self._rla(self._abs_x(), 7)
        d[0x3B] = lambda: self._rla(self._abs_y(), 7)

        # SRE  = LSR memory, then EOR result into A
        d[0x47] = lambda: self._sre(self._zp(),    5)
        d[0x57] = lambda: self._sre(self._zp_x(),  6)
        d[0x43] = lambda: self._sre(self._ind_x(), 8)
        d[0x53] = lambda: self._sre(self._ind_y(), 8)
        d[0x4F] = lambda: self._sre(self._abs(),   6)
        d[0x5F] = lambda: self._sre(self._abs_x(), 7)
        d[0x5B] = lambda: self._sre(self._abs_y(), 7)

        # RRA  = ROR memory, then ADC result into A
        d[0x67] = lambda: self._rra(self._zp(),    5)
        d[0x77] = lambda: self._rra(self._zp_x(),  6)
        d[0x63] = lambda: self._rra(self._ind_x(), 8)
        d[0x73] = lambda: self._rra(self._ind_y(), 8)
        d[0x6F] = lambda: self._rra(self._abs(),   6)
        d[0x7F] = lambda: self._rra(self._abs_x(), 7)
        d[0x7B] = lambda: self._rra(self._abs_y(), 7)

        # DCP  = DEC memory, then CMP A with result
        d[0xC7] = lambda: self._dcp(self._zp(),    5)
        d[0xD7] = lambda: self._dcp(self._zp_x(),  6)
        d[0xC3] = lambda: self._dcp(self._ind_x(), 8)
        d[0xD3] = lambda: self._dcp(self._ind_y(), 8)
        d[0xCF] = lambda: self._dcp(self._abs(),   6)
        d[0xDF] = lambda: self._dcp(self._abs_x(), 7)
        d[0xDB] = lambda: self._dcp(self._abs_y(), 7)

        # ISC (a.k.a. ISB) = INC memory, then SBC result from A
        d[0xE7] = lambda: self._isc(self._zp(),    5)
        d[0xF7] = lambda: self._isc(self._zp_x(),  6)
        d[0xE3] = lambda: self._isc(self._ind_x(), 8)
        d[0xF3] = lambda: self._isc(self._ind_y(), 8)
        d[0xEF] = lambda: self._isc(self._abs(),   6)
        d[0xFF] = lambda: self._isc(self._abs_x(), 7)
        d[0xFB] = lambda: self._isc(self._abs_y(), 7)

        # ANC  = AND #imm, then copy bit 7 into C
        d[0x0B] = lambda: self._anc()
        d[0x2B] = lambda: self._anc()

        # ALR  = AND #imm + LSR A
        d[0x4B] = lambda: self._alr()
        # ARR  = AND #imm + ROR A (with unusual C/V handling)
        d[0x6B] = lambda: self._arr()
        # AXS / SBX = X = (A & X) - #imm, flags like CMP
        d[0xCB] = lambda: self._axs()
        # Duplicate SBC #imm
        d[0xEB] = lambda: self._sbc(self._imm(), 2)

        # Illegal NOPs — various lengths/addressing modes, all just consume time
        for op in (0x1A, 0x3A, 0x5A, 0x7A, 0xDA, 0xFA):
            d[op] = lambda: self._tick(2)                      # 1-byte NOPs
        for op in (0x80, 0x82, 0x89, 0xC2, 0xE2):
            d[op] = lambda: (self._imm(), self._tick(2))       # 2-byte NOPs (imm)
        for op in (0x04, 0x44, 0x64):
            d[op] = lambda: (self._zp(), self._tick(3))        # NOP zp
        for op in (0x14, 0x34, 0x54, 0x74, 0xD4, 0xF4):
            d[op] = lambda: (self._zp_x(), self._tick(4))      # NOP zp,X
        d[0x0C] = lambda: (self._abs(), self._tick(4))         # NOP abs
        for op in (0x1C, 0x3C, 0x5C, 0x7C, 0xDC, 0xFC):
            d[op] = lambda: (self._abs_x(), self._tick(4))     # NOP abs,X

        # Genuinely unstable / rarely used illegals — provide *something* so
        # programs don't crash on stray bytes; we don't pretend the behaviour
        # is right. (Most games avoid these.)
        d[0x8B] = lambda: (self._imm(), self._tick(2))         # XAA (unstable)
        d[0xAB] = lambda: (self._imm(), self._tick(2))         # LAX #imm (unstable)
        for op in (0x93, 0x9B, 0x9C, 0x9E, 0x9F):
            d[op] = lambda: (self.fetch_byte(), self.fetch_byte(), self._tick(5))

        self._dispatch = d

    # ---------- NMOS 6502 illegal-opcode helpers ----------

    def _sax_at(self, adr, cycles):
        self.mem.write_system_byte(adr, self.a & self.x)
        self.cycles += cycles

    def _lax_from(self, adr, cycles):
        v = self.mem.read_system_byte(adr)
        self.a = v
        self.x = v
        self.update_nz(v)
        self.cycles += cycles

    def _slo(self, adr, cycles):                # ASL + ORA
        val = self.mem.read_system_byte(adr)
        self.mem.write_system_byte(adr, val)    # NMOS RMW dummy write
        new = self._asl(val)
        self.mem.write_system_byte(adr, new)
        self.a |= new
        self.update_nz(self.a)
        self.cycles += cycles

    def _rla(self, adr, cycles):                # ROL + AND
        val = self.mem.read_system_byte(adr)
        self.mem.write_system_byte(adr, val)
        new = self._rol(val)
        self.mem.write_system_byte(adr, new)
        self.a &= new
        self.update_nz(self.a)
        self.cycles += cycles

    def _sre(self, adr, cycles):                # LSR + EOR
        val = self.mem.read_system_byte(adr)
        self.mem.write_system_byte(adr, val)
        new = self._lsr(val)
        self.mem.write_system_byte(adr, new)
        self.a ^= new
        self.update_nz(self.a)
        self.cycles += cycles

    def _rra(self, adr, cycles):                # ROR + ADC
        val = self.mem.read_system_byte(adr)
        self.mem.write_system_byte(adr, val)
        new = self._ror(val)
        self.mem.write_system_byte(adr, new)
        self._adc(new, 0)                       # reuse adc for flag logic
        self.cycles += cycles

    def _dcp(self, adr, cycles):                # DEC + CMP (A vs result)
        val = self.mem.read_system_byte(adr)
        self.mem.write_system_byte(adr, val)
        new = (val - 1) & 0xFF
        self.mem.write_system_byte(adr, new)
        diff = (self.a - new) & 0xFF
        self.set_flag(self.FC, self.a >= new)
        self.update_nz(diff)
        self.cycles += cycles

    def _isc(self, adr, cycles):                # INC + SBC
        val = self.mem.read_system_byte(adr)
        self.mem.write_system_byte(adr, val)
        new = (val + 1) & 0xFF
        self.mem.write_system_byte(adr, new)
        self._sbc(new, 0)
        self.cycles += cycles

    def _anc(self):                             # AND #imm, then C = bit 7
        v = self._imm()
        self.a &= v
        self.update_nz(self.a)
        self.set_flag(self.FC, (self.a & 0x80) != 0)
        self.cycles += 2

    def _alr(self):                             # AND #imm + LSR A
        v = self._imm()
        self.a &= v
        self.set_flag(self.FC, (self.a & 1) != 0)
        self.a = (self.a >> 1) & 0x7F
        self.update_nz(self.a)
        self.cycles += 2

    def _arr(self):                             # AND #imm + ROR A (binary mode)
        v = self._imm()
        self.a &= v
        old_c = 0x80 if self.get_flag_c() else 0
        self.a = (self.a >> 1) | old_c
        self.update_nz(self.a)
        # ARR's C and V come from bits 5 and 6 of the result (binary mode).
        self.set_flag(self.FC, (self.a & 0x40) != 0)
        self.set_flag(self.FV, (((self.a >> 5) ^ (self.a >> 6)) & 1) != 0)
        self.cycles += 2

    def _axs(self):                             # X = (A & X) - #imm, CMP-like flags
        v = self._imm()
        tmp = self.a & self.x
        self.set_flag(self.FC, tmp >= v)
        result = (tmp - v) & 0xFF
        self.update_nz(result)
        self.x = result
        self.cycles += 2


    # ---------- internal helpers ----------

    def _tick(self, n): self.cycles += n
    def _lda_from(self, a, c): self.a = self.mem.read_system_byte(a); self.update_nz(self.a); self._tick(c)
    def _ldx_from(self, a, c): self.x = self.mem.read_system_byte(a); self.update_nz(self.x); self._tick(c)
    def _ldy_from(self, a, c): self.y = self.mem.read_system_byte(a); self.update_nz(self.y); self._tick(c)
    def _sta_at(self, a, c):   self.mem.write_system_byte(a, self.a); self._tick(c)
    def _stx_at(self, a, c):   self.mem.write_system_byte(a, self.x); self._tick(c)
    def _sty_at(self, a, c):   self.mem.write_system_byte(a, self.y); self._tick(c)
    def _inx(self): self.x = (self.x + 1) & 0xFF; self.update_nz(self.x); self._tick(2)
    def _iny(self): self.y = (self.y + 1) & 0xFF; self.update_nz(self.y); self._tick(2)
    def _dex(self): self.x = (self.x - 1) & 0xFF; self.update_nz(self.x); self._tick(2)
    def _dey(self): self.y = (self.y - 1) & 0xFF; self.update_nz(self.y); self._tick(2)

    # ---------- step ----------

    def step(self):
        # Python-level traps (for KERNAL routine interception). The `self.traps`
        # check short-circuits when no traps installed — important for perf.
        # All trap addresses live in the KERNAL ROM region ($E000-$FFFF); only
        # intercept when the KERNAL ROM is actually mapped in. Games that copy
        # their own code under the KERNAL and bank it out (e.g. custom loaders
        # that reuse $FFxx addresses) must run that code normally.
        if self.traps and self.pc in self.traps:
            if self.mem.pla.address_space(self.pc) == AddressSpace.KERNAL_ROM:
                self.traps[self.pc]()
                return True
        if self.nmi_pending:
            self.nmi_pending = False
            self.nmi()
            return True
        if self.irq_line and not self.get_flag_i():
            self.irq()
            return True
        op = self.fetch_byte()
        handler = self._dispatch[op]
        if handler is None:
            print(f"Unknown opcode 0x{op:02X} at {word2hex((self.pc - 1) & 0xFFFF)}")
            return False
        handler()
        if self.trace:
            self.print_state()
        return True

    def print_state(self):
        flags = ('1' if self.get_flag_n() else '0')
        flags += ('1' if self.get_flag_v() else '0')
        flags += '-'
        flags += ('1' if self.get_flag_b() else '0')
        flags += ('1' if self.get_flag_d() else '0')
        flags += ('1' if self.get_flag_i() else '0')
        flags += ('1' if self.get_flag_z() else '0')
        flags += ('1' if self.get_flag_c() else '0')
        print(f"PC={word2hex(self.pc)} A={byte2hex(self.a)} X={byte2hex(self.x)} "
              f"Y={byte2hex(self.y)} SP={byte2hex(self.sp)} SR={byte2hex(self.sr)} "
              f"NV-BDIZC={flags} cyc={self.cycles}")


# =============================================================================
# D64 disk image
# =============================================================================

class D64Image:
    """
    Read-only D64 disk image (Commodore 1541 floppy).

    Supports the standard 35-track layouts: 174 848 bytes (no error info)
    or 175 531 bytes (with one error byte per sector appended). Only the
    sector data is read; error bytes are ignored.

    Sectors per track:
        tracks  1-17 → 21 sectors
        tracks 18-24 → 19 sectors
        tracks 25-30 → 18 sectors
        tracks 31-35 → 17 sectors
    """

    SECTORS_PER_TRACK = (
        21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21, 21,
        19, 19, 19, 19, 19, 19, 19,
        18, 18, 18, 18, 18, 18,
        17, 17, 17, 17, 17,
    )

    def __init__(self, path):
        with open(path, "rb") as f:
            data = f.read()
        if len(data) not in (174848, 175531):
            raise ValueError(
                f"Not a standard 35-track D64: {len(data)} bytes "
                f"(expected 174848 or 175531)")
        self.data = data
        self.path = path

    def sector_offset(self, track, sector):
        if not 1 <= track <= 35:
            raise ValueError(f"track {track} out of range")
        spt = self.SECTORS_PER_TRACK[track - 1]
        if not 0 <= sector < spt:
            raise ValueError(f"sector {sector} out of range for track {track}")
        off = 0
        for t in range(1, track):
            off += self.SECTORS_PER_TRACK[t - 1] * 256
        return off + sector * 256

    def read_sector(self, track, sector):
        off = self.sector_offset(track, sector)
        return self.data[off : off + 256]

    def disk_name(self):
        """Disk name from BAM sector (track 18 sector 0), PETSCII bytes."""
        bam = self.read_sector(18, 0)
        return bytes(bam[0x90:0xA0]).rstrip(b"\xA0")

    def list_directory(self):
        """
        Yield (name_bytes, file_type, first_track, first_sector, size_sectors)
        for each non-deleted file in the directory. Filename is stripped of
        $A0 padding. Walks the T/S chain starting at track 18 sector 1.
        """
        track, sector = 18, 1
        visited = set()
        while track != 0:
            if (track, sector) in visited:
                break                          # safety against malformed chain
            visited.add((track, sector))
            sec = self.read_sector(track, sector)
            for slot in range(8):
                base = slot * 32
                ftype = sec[base + 2]
                if ftype == 0:                 # deleted entry
                    continue
                ft = sec[base + 3]
                fs = sec[base + 4]
                name = bytes(sec[base + 5 : base + 21]).rstrip(b"\xA0")
                size = sec[base + 30] | (sec[base + 31] << 8)
                yield name, ftype, ft, fs, size
            track, sector = sec[0], sec[1]

    def find_file(self, pattern):
        """
        Find first PRG matching `pattern` (bytes). C64 wildcards:
            * matches everything from this position on
            ? matches exactly one character
        Empty pattern matches the first PRG. Case-insensitive comparison
        within PETSCII A-Z range. Returns (track, sector, size_sectors) or None.
        """
        pat = pattern.upper()
        for name, ftype, ft, fs, size in self.list_directory():
            if (ftype & 0x0F) != 0x02:         # 2 = PRG; skip SEQ/USR/REL/DEL
                continue
            if _match_c64_name(name.upper(), pat):
                return ft, fs, size
        return None

    def read_file(self, track, sector):
        """Follow the T/S chain from (track, sector). Returns the file bytes
        (including the 2-byte PRG load address)."""
        out = bytearray()
        visited = set()
        while True:
            if (track, sector) in visited:
                break                          # safety against loops
            visited.add((track, sector))
            sec = self.read_sector(track, sector)
            nxt_t = sec[0]
            nxt_s = sec[1]
            if nxt_t == 0:
                # Last sector: nxt_s = index of last valid data byte (0-based
                # from start of sector, so data is bytes 2..nxt_s inclusive).
                last = nxt_s
                if last < 2:
                    break
                out.extend(sec[2 : last + 1])
                break
            out.extend(sec[2:256])
            track, sector = nxt_t, nxt_s
        return bytes(out)


class T64Image:
    """
    Reader for T64 tape-archive images.

    Despite the name, T64 is not a raw tape signal — it's a simple container:
    a 64-byte header, then a directory of 32-byte records, each pointing at a
    file's raw bytes elsewhere in the file. Unlike .PRG / D64 files, the stored
    bytes do NOT carry the 2-byte load-address prefix; the load address lives
    in the directory record instead.

    We expose the same tiny interface as D64Image (disk_name / list_directory /
    find_file / read_file / read_sector) so the existing LOAD path serves tape
    files unchanged. Files are addressed by directory index rather than
    track/sector, and read_file synthesises the [lo, hi] + data PRG layout the
    loader expects.
    """

    def __init__(self, path):
        with open(path, "rb") as f:
            self.data = f.read()
        d = self.data
        self._name = d[40:64] if len(d) >= 64 else b""
        maxent = (d[34] | (d[35] << 8)) if len(d) >= 36 else 0
        self.entries = []
        for i in range(maxent):
            off = 64 + i * 32
            rec = d[off:off + 32]
            if len(rec) < 32:
                break
            if rec[0] == 0:                        # unused slot
                continue
            start = rec[2] | (rec[3] << 8)
            end = rec[4] | (rec[5] << 8)
            doff = rec[8] | (rec[9] << 8) | (rec[10] << 16) | (rec[11] << 24)
            name = rec[16:32].rstrip(b"\x20\x00")
            self.entries.append({"name": name, "start": start,
                                 "end": end, "doff": doff})
        # Repair unreliable end addresses (a very common T64 defect): if the
        # implied length is zero or overruns the next file / end of image,
        # clamp it to the space actually available.
        offs = sorted(e["doff"] for e in self.entries)
        for e in self.entries:
            length = (e["end"] - e["start"]) & 0xFFFF
            nxt = min([o for o in offs if o > e["doff"]] + [len(d)])
            avail = max(0, nxt - e["doff"])
            if length == 0 or length > avail:
                length = avail
            e["length"] = length

    def disk_name(self):
        return self._name.rstrip(b"\x20\x00") or b"T64 TAPE"

    def list_directory(self):
        out = []
        for e in self.entries:
            blocks = (e["length"] + 253) // 254
            out.append((e["name"].ljust(16)[:16], "PRG", 0, 0, blocks))
        return out

    def find_file(self, pattern):
        pat = pattern.rstrip(b"\x20\x00")
        # On tape, LOAD with no name (or "*") loads the first/next program.
        if pat in (b"", b"*"):
            return (0, 0, 0) if self.entries else None
        wild = pat.endswith(b"*")
        core = pat[:-1] if wild else pat
        for i, e in enumerate(self.entries):
            nm = e["name"]
            if (nm == pat) or (wild and nm.startswith(core)) or nm.startswith(pat):
                return (i, 0, 0)
        return None

    def read_file(self, index, _sector=0):
        """Return the file's PRG bytes: [load_lo, load_hi] + raw data."""
        e = self.entries[index]
        raw = self.data[e["doff"]:e["doff"] + e["length"]]
        return bytes([e["start"] & 0xFF, (e["start"] >> 8) & 0xFF]) + raw

    def read_sector(self, track, sector):
        return bytes(256)          # tape archives have no block-level access


def _match_c64_name(name, pattern):
    """C64-style match: ? = any single char, * = matches the rest. Both are
    bytes. Comparison should already be case-folded by the caller."""
    if len(pattern) == 0:
        return True
    i = 0
    for j, pc in enumerate(pattern):
        if pc == ord("*"):
            return True
        if i >= len(name):
            return False
        if pc != ord("?") and pc != name[i]:
            return False
        i += 1
    return i == len(name)


# =============================================================================
# System — CPU + Memory + chips, ticking together
# =============================================================================

class System:
    """
    Full C64 system. CPU runs, then chips catch up by the cycle count of the
    last instruction. /IRQ is the wire-OR of VIC and CIA1 IRQ lines; /NMI is
    edge-triggered from CIA2.
    """

    def __init__(self, rom_dir="roms", verbose=True):
        # Try ./roms/*.bin first (original ROMs); fall back to embedded Open Roms.
        def _load(filename, blob_name):
            path = os.path.join(rom_dir, filename)
            if os.path.exists(path):
                with open(path, "rb") as f:
                    return f.read(), "file"
            return _get_embedded_rom(blob_name), "embedded"
        basic,   basic_src   = _load("basic.bin",   "basic")
        chargen, chargen_src = _load("chargen.bin", "chargen")
        kernal,  kernal_src  = _load("kernal.bin",  "kernal")
        self.rom_source = "file" if all(s == "file" for s in
                                        (basic_src, chargen_src, kernal_src)) else "mixed-or-embedded"
        if verbose:
            srcs = {"basic": basic_src, "kernal": kernal_src, "chargen": chargen_src}
            if all(v == "file" for v in srcs.values()):
                print(f"ROMs: loaded from {rom_dir}/ (original)")
            elif all(v == "embedded" for v in srcs.values()):
                print("ROMs: using embedded ROMs")
            else:
                summary = ", ".join(f"{k}={v}" for k, v in srcs.items())
                print(f"ROMs: mixed ({summary})")
        self.vic       = Vic()
        self.sid       = Sid()
        self.color_ram = ColorRam()
        self.cia1      = Cia("CIA1")
        self.cia2      = Cia("CIA2")
        self.mem = Memory(basic_rom=basic, char_rom=chargen, kernal_rom=kernal,
                          vic=self.vic, sid=self.sid, color_ram=self.color_ram,
                          cia1=self.cia1, cia2=self.cia2)
        self.chargen_rom = bytes(chargen)
        self.cpu = CPU(self.mem)
        self._d64 = None
        # KERNAL file-I/O state: open files keyed by logical address (LA).
        # Each entry: {'dev': int, 'sa': int, 'name': bytes, 'data': bytes, 'pos': int}
        self._open_files = {}
        self._current_input_la = None    # LA whose data CHRIN/GETIN return
        self._current_output_la = None   # CHKOUT target (we don't actually write)
        # Direct-access / block-command disk state, for loaders that open the
        # command channel (SA 15) and a "#" buffer channel and read raw sectors
        # via "U1"/"B-R" block-read commands (e.g. Lode Runner). da_buffers is
        # keyed by channel number (secondary address of the "#" open); each is
        # {'data': bytearray(256), 'pos': int}. _cmd_out accumulates bytes
        # written to the command channel until a CR triggers execution.
        self._da_buffers = {}
        self._cmd_out = bytearray()
        self._disk_status = b"00, OK,00,00\r"
        self._is_tape = False    # True when the mounted image is a T64 tape
        # Low-level serial (IEC) bus emulation state. Games with custom loaders
        # bypass the high-level LOAD/OPEN and drive the bus directly with
        # LISTEN/SECOND/CIOUT/UNLSN (to OPEN a file by name) then
        # TALK/TKSA/ACPTR/UNTALK (to read it byte-by-byte). We emulate a 1541
        # at that level, serving files straight from the mounted D64.
        self._iec_dev = None             # device currently addressed
        self._iec_mode = None            # 'listen' | 'talk' | None
        self._iec_opening = False        # collecting a filename after OPEN
        self._iec_open_chan = 0          # channel being opened / addressed
        self._iec_name = bytearray()     # filename accumulated via CIOUT
        self._iec_talk_chan = 0          # channel selected for TALK/ACPTR
        self._iec_channels = {}          # channel -> {'data': bytes, 'pos': int}

    def step(self):
        before = self.cpu.cycles
        cur_nmi = self.cia2.irq_line
        if cur_nmi and not self.cpu._prev_nmi:
            self.cpu.nmi_pending = True
        self.cpu._prev_nmi = cur_nmi
        self.cpu.irq_line = self.cia1.irq_line or self.vic.irq_line
        ok = self.cpu.step()
        elapsed = self.cpu.cycles - before
        if elapsed > 0:
            self.vic.tick(elapsed)
            self.cia1.tick(elapsed)
            self.cia2.tick(elapsed)
        return ok

    def run(self, n_cycles):
        target = self.cpu.cycles + n_cycles
        while self.cpu.cycles < target:
            if not self.step():
                return False
        return True

    # ---------- PRG loading & keyboard buffer injection ----------

    def load_prg(self, path):
        """
        Load a Commodore .prg file into RAM.

        PRG format: first 2 bytes = little-endian load address, rest = payload.
        We also patch the BASIC end-of-program zero-page pointers so RUN and
        LIST see the loaded program correctly.

        Returns (load_addr, length, is_basic).
        """
        with open(path, "rb") as f:
            data = f.read()
        if len(data) < 3:
            raise ValueError(f"PRG file too short: {path}")
        load_addr = data[0] | (data[1] << 8)
        payload = data[2:]
        end_addr = (load_addr + len(payload)) & 0xFFFF

        # Write payload into RAM
        self.mem.load_ram(load_addr, payload)

        # Update BASIC end-of-program pointers
        # $2D-$2E: end of BASIC text + 1 (= start of variables)
        # $2F-$30: end of variables (= start of arrays)
        # $31-$32: end of arrays (= start of strings)
        # $AE-$AF: end-of-load address (set by KERNAL LOAD)
        for addr in (0x2D, 0x2F, 0x31, 0xAE):
            self.mem.write_ram_direct(addr,     end_addr & 0xFF)
            self.mem.write_ram_direct(addr + 1, (end_addr >> 8) & 0xFF)

        is_basic = (load_addr == 0x0801)
        return load_addr, len(payload), is_basic

    def type_string(self, s):
        """
        Inject a string into the kernal keyboard buffer at $0277.

        BASIC's input loop reads from this buffer just as if the user typed
        the characters. Use '\r' or '\n' for RETURN. Max 10 chars at a time.
        """
        s = s.replace("\n", "\r")
        for i, ch in enumerate(s[:10]):
            code = ord(ch)
            # Map LF -> CR (PETSCII RETURN = $0D)
            if code == 0x0A:
                code = 0x0D
            self.mem.write_ram_direct(0x0277 + i, code)
        # $C6 = NDX, number of chars currently in keyboard buffer
        self.mem.write_ram_direct(0xC6, min(len(s), 10))

    # ---------- generic subroutine call (used by SID init/play) ----------

    def call_routine(self, address, max_cycles=2_000_000):
        """
        Set PC to `address` and run until the routine RTSs back to a sentinel
        return address ($FFFE). Returns True on clean return, False on timeout.
        """
        SENTINEL = 0xFFFE
        # Push sentinel-1 (JSR pushes addr-1, RTS adds 1 on pop)
        ret = (SENTINEL - 1) & 0xFFFF
        self.cpu.push((ret >> 8) & 0xFF)
        self.cpu.push(ret & 0xFF)
        self.cpu.pc = address
        start = self.cpu.cycles
        while self.cpu.cycles - start < max_cycles:
            if self.cpu.pc == SENTINEL:
                return True
            if not self.step():
                return False
        return False

    # ---------- SID file (.sid) loading ----------

    def load_sid(self, path, song_num=None):
        """
        Load a PSID/RSID file. Calls the tune's Init routine immediately.
        Subsequent frames must call `sid_play_tick()` to drive playback.
        Returns the parsed header dict.
        """
        import struct
        with open(path, "rb") as f:
            data = f.read()
        if data[:4] not in (b"PSID", b"RSID"):
            raise ValueError(f"Not a SID file: {data[:4]!r}")
        # PSID/RSID v1/v2 header layout (big-endian):
        #   $00-$03 magic, $04-$05 version, $06-$07 dataOffset,
        #   $08-$09 load, $0A-$0B init, $0C-$0D play,
        #   $0E-$0F songs, $10-$11 startSong, $12-$15 speed
        version, data_off = struct.unpack(">HH", data[4:8])
        load_addr, init_addr, play_addr = struct.unpack(">HHH", data[8:14])
        songs, start_song = struct.unpack(">HH", data[14:18])
        speed = struct.unpack(">L", data[18:22])[0]
        name     = data[22:54].split(b"\x00", 1)[0].decode("ascii", "replace")
        author   = data[54:86].split(b"\x00", 1)[0].decode("ascii", "replace")
        released = data[86:118].split(b"\x00", 1)[0].decode("ascii", "replace")
        payload = data[data_off:]
        if load_addr == 0:
            load_addr = payload[0] | (payload[1] << 8)
            payload = payload[2:]
        # Boot the kernal first so the C64 is in a sensible state
        if self.cpu.cycles < 2_000_000:
            self.run(3_500_000)
        # Bank ROMs out — PSID code typically uses RAM under ROMs
        self.mem.write_system_byte(Config.ADDR_PROCESSOR_PORT_REG, 0x37)
        # Write payload
        self.mem.load_ram(load_addr, payload)
        # Call init with A = song index (0-based), interrupts disabled
        if song_num is None:
            song_num = start_song - 1
        self.cpu.a = song_num & 0xFF
        self.cpu.x = 0
        self.cpu.y = 0
        self.cpu.set_flag(self.cpu.FI, True)
        self.call_routine(init_addr)
        self._sid_play_addr = play_addr
        return {"format": data[:4].decode("ascii"), "version": version,
                "load": load_addr, "init": init_addr, "play": play_addr,
                "songs": songs, "start_song": start_song,
                "name": name, "author": author, "released": released}

    def sid_play_tick(self):
        """If a SID tune is active, call its Play routine once (one frame)."""
        addr = getattr(self, "_sid_play_addr", 0)
        if addr:
            self.call_routine(addr)

    # ---------- D64 disk image + KERNAL LOAD trap ----------

    # Trap entry points → handler method names. Covers LOAD plus the sequential
    # file-I/O routines (OPEN/CLOSE/CHKIN/CLRCHN/CHRIN/GETIN) used by games that
    # read files byte-by-byte rather than via the high-level $FFD5 LOAD.
    # We also trap the LOAD *implementation* address ($F4A5) because some
    # crackers jump directly there via the $0330 indirect vector instead of
    # through the $FFD5 jump-table entry.
    _KERNAL_TRAPS = {
        0xFFC0: "_trap_open",
        0xFFC3: "_trap_close",
        0xFFC6: "_trap_chkin",
        0xFFC9: "_trap_ckout",
        0xFFCC: "_trap_clrchn",
        0xFFCF: "_trap_chrin",
        0xFFD2: "_trap_chrout",
        0xFFD5: "_trap_load",
        0xFFE4: "_trap_getin",
        0xF4A5: "_trap_load",     # LOAD impl (target of $0330 indirect vector)
        # Low-level serial (IEC) bus primitives, used by custom fast/loaders
        # that open and read files without going through $FFD5/$FFC0.
        0xFFB1: "_trap_iec_listen",   # LISTEN  (A = device)
        0xFF93: "_trap_iec_second",   # SECOND  (A = secondary addr, after LISTEN)
        0xFFA8: "_trap_iec_ciout",    # CIOUT   (A = byte to send)
        0xFFAE: "_trap_iec_unlsn",    # UNLSN
        0xFFB4: "_trap_iec_talk",     # TALK    (A = device)
        0xFF96: "_trap_iec_tksa",     # TKSA    (A = secondary addr, after TALK)
        0xFFA5: "_trap_iec_acptr",    # ACPTR   (returns byte in A)
        0xFFAB: "_trap_iec_untalk",   # UNTALK
    }

    def mount_d64(self, path):
        """Mount a D64 image. LOAD and KERNAL file-I/O calls from the running
        CPU will be served from this image. Pass None to unmount."""
        if path is None:
            self._d64 = None
            self._open_files.clear()
            self._current_input_la = None
            self._current_output_la = None
            self._iec_reset()
            for addr in self._KERNAL_TRAPS:
                self.cpu.traps.pop(addr, None)
            return None
        self._d64 = D64Image(path)
        self._open_files.clear()
        self._current_input_la = None
        self._current_output_la = None
        self._da_buffers.clear()
        self._cmd_out = bytearray()
        self._disk_status = b"00, OK,00,00\r"
        self._is_tape = False
        self._iec_reset()
        for addr, name in self._KERNAL_TRAPS.items():
            self.cpu.traps[addr] = getattr(self, name)
        return self._d64

    def mount_t64(self, path):
        """Mount a T64 tape-archive image. LOAD from device 1 (tape) will be
        served from it. Reuses the same KERNAL LOAD path as disk images; the
        `_is_tape` flag makes the LOAD trap accept device 1."""
        self._d64 = T64Image(path)
        self._open_files.clear()
        self._current_input_la = None
        self._current_output_la = None
        self._da_buffers.clear()
        self._cmd_out = bytearray()
        self._disk_status = b"00, OK,00,00\r"
        self._is_tape = True
        self._iec_reset()
        for addr, name in self._KERNAL_TRAPS.items():
            self.cpu.traps[addr] = getattr(self, name)
        return self._d64

    def _do_rts(self):
        """Execute an RTS: pop return address from stack, set PC = addr + 1."""
        cpu = self.cpu
        lo = cpu.pop()
        hi = cpu.pop()
        cpu.pc = ((hi << 8) | lo) + 1
        cpu.pc &= 0xFFFF
        cpu.cycles += 6   # roughly the cost of an RTS

    def _passthrough_kernal_jmp(self):
        """When a trap fires but we don't want to handle it, simulate executing
        the JMP at the KERNAL jump table entry so the original ROM routine runs.
        The bytes at $FFC0/$FFC3/... are always either JMP abs ($4C) or JMP ind
        ($6C) in any standard KERNAL ROM."""
        cpu = self.cpu
        mem = self.mem
        pc = cpu.pc
        opcode = mem.read_system_byte(pc)
        if opcode == 0x4C:                                   # JMP absolute
            lo = mem.read_system_byte((pc + 1) & 0xFFFF)
            hi = mem.read_system_byte((pc + 2) & 0xFFFF)
            cpu.pc = lo | (hi << 8)
            cpu.cycles += 3
        elif opcode == 0x6C:                                 # JMP indirect
            ptr = (mem.read_system_byte((pc + 1) & 0xFFFF)
                   | (mem.read_system_byte((pc + 2) & 0xFFFF) << 8))
            lo = mem.read_system_byte(ptr)
            hi = mem.read_system_byte((ptr & 0xFF00) | ((ptr + 1) & 0xFF))
            cpu.pc = lo | (hi << 8)
            cpu.cycles += 5
        else:
            # Shouldn't happen with a real KERNAL, but RTS rather than loop.
            self._do_rts()

    def _trap_open(self):
        """KERNAL OPEN ($FFC0). Open a logical file. Parameters in zero page
        (set earlier by SETLFS/SETNAM): $B8=LA, $B9=SA, $BA=DEV,
        $B7=fnlen, $BB/$BC=fnaddr. We handle device 8; everything else
        passes through to the real KERNAL."""
        cpu = self.cpu
        mem = self.mem
        la    = mem.read_ram_direct(0xB8)
        sa    = mem.read_ram_direct(0xB9)
        dev   = mem.read_ram_direct(0xBA)
        fnlen = mem.read_ram_direct(0xB7)
        fnaddr = (mem.read_ram_direct(0xBB)
                  | (mem.read_ram_direct(0xBC) << 8))
        if dev != 8 or self._d64 is None:
            return self._passthrough_kernal_jmp()
        name = bytes(mem.read_ram_direct((fnaddr + i) & 0xFFFF)
                     for i in range(fnlen))
        # Command channel (secondary address 15): used to send disk commands
        # (U1/B-R block read, B-P buffer pointer) and to read drive status.
        if sa == 15:
            self._open_files[la] = {"dev": dev, "sa": sa, "name": name,
                                    "cmd": True}
            cpu.set_flag(cpu.FC, False)
            mem.write_ram_direct(0x90, 0)
            self._do_rts()
            return
        # Direct-access buffer channel ("#" opens a raw 256-byte sector buffer
        # on the drive; the loader fills it with U1 block-read commands).
        if name.startswith(b"#"):
            self._da_buffers[sa] = {"data": bytearray(256), "pos": 0}
            self._open_files[la] = {"dev": dev, "sa": sa, "name": name,
                                    "da_chan": sa}
            cpu.set_flag(cpu.FC, False)
            mem.write_ram_direct(0x90, 0)
            self._do_rts()
            return
        # Special "$" = directory
        if name.startswith(b"$"):
            data = bytes([0x01, 0x08]) + self._build_dir_listing(load_addr=0x0801)
        else:
            found = self._d64.find_file(name)
            if found is None:
                cpu.a = 4                          # FILE NOT FOUND
                cpu.set_flag(cpu.FC, True)
                mem.write_ram_direct(0x90, 0)
                self._do_rts()
                return
            data = self._d64.read_file(found[0], found[1])
        self._open_files[la] = {
            "dev": dev, "sa": sa, "name": name, "data": data, "pos": 0
        }
        cpu.set_flag(cpu.FC, False)
        mem.write_ram_direct(0x90, 0)
        self._do_rts()

    def _trap_close(self):
        """KERNAL CLOSE ($FFC3). A = LA to close. We only handle LAs we
        opened ourselves; anything else passes through."""
        cpu = self.cpu
        la = cpu.a
        if la not in self._open_files:
            return self._passthrough_kernal_jmp()
        del self._open_files[la]
        if self._current_input_la == la:
            self._current_input_la = None
        if self._current_output_la == la:
            self._current_output_la = None
        cpu.set_flag(cpu.FC, False)
        self._do_rts()

    def _trap_chkin(self):
        """KERNAL CHKIN ($FFC6). X = LA. Set current input to that file."""
        cpu = self.cpu
        la = cpu.x
        if la not in self._open_files:
            return self._passthrough_kernal_jmp()
        self._current_input_la = la
        self.mem.write_ram_direct(0x99, self._open_files[la]["dev"])  # DFLTI
        cpu.set_flag(cpu.FC, False)
        self._do_rts()

    def _trap_clrchn(self):
        """KERNAL CLRCHN ($FFCC). Restore default I/O channels."""
        if self._current_input_la is None and self._current_output_la is None:
            return self._passthrough_kernal_jmp()
        self._current_input_la = None
        self._current_output_la = None
        self.mem.write_ram_direct(0x99, 0)    # DFLTI = keyboard
        self.mem.write_ram_direct(0x9A, 3)    # DFLTO = screen
        self.cpu.set_flag(self.cpu.FC, False)
        self._do_rts()

    def _trap_chrin(self):
        """KERNAL CHRIN ($FFCF). Read next byte from current input. Handles
        regular files, direct-access buffer channels, and the command channel
        (which returns the drive status string). Falls through to the real
        KERNAL when no managed file is selected as input."""
        la = self._current_input_la
        if la is None or la not in self._open_files:
            return self._passthrough_kernal_jmp()
        cpu = self.cpu
        mem = self.mem
        f = self._open_files[la]
        if f.get("cmd"):                          # command channel → status
            data = self._disk_status
            pos = f.get("pos", 0)
            if pos < len(data):
                cpu.a = data[pos]
                f["pos"] = pos + 1
                mem.write_ram_direct(0x90, 0x40 if pos + 1 >= len(data) else 0)
            else:
                cpu.a = 0x0D
                mem.write_ram_direct(0x90, 0x40)
            cpu.set_flag(cpu.FC, False)
            self._do_rts()
            return
        if "da_chan" in f:                        # direct-access sector buffer
            buf = self._da_buffers.get(f["da_chan"])
            data = buf["data"] if buf else b""
            pos = buf["pos"] if buf else 0
            if pos < len(data):
                cpu.a = data[pos]
                buf["pos"] = pos + 1
                mem.write_ram_direct(0x90, 0x40 if pos + 1 >= len(data) else 0)
            else:
                cpu.a = 0
                mem.write_ram_direct(0x90, 0x40)
            cpu.set_flag(cpu.FC, False)
            self._do_rts()
            return
        # regular file
        if f["pos"] < len(f["data"]):
            cpu.a = f["data"][f["pos"]]
            f["pos"] += 1
            mem.write_ram_direct(0x90, 0x40 if f["pos"] >= len(f["data"]) else 0)
        else:
            cpu.a = 0
            mem.write_ram_direct(0x90, 0x40)   # EOF
        cpu.set_flag(cpu.FC, False)
        self._do_rts()

    def _trap_ckout(self):
        """KERNAL CKOUT ($FFC9). X = LA. Direct output to a channel we manage
        (e.g. the command channel); otherwise pass through so normal screen /
        serial output keeps working."""
        la = self.cpu.x
        if la not in self._open_files:
            return self._passthrough_kernal_jmp()
        self._current_output_la = la
        self.mem.write_ram_direct(0x9A, self._open_files[la]["dev"])   # DFLTO
        self.cpu.set_flag(self.cpu.FC, False)
        self._do_rts()

    def _trap_chrout(self):
        """KERNAL CHROUT ($FFD2). A = byte. If output is currently directed to
        the command channel, accumulate command bytes and execute on CR. For
        anything else (screen output, unmanaged files) pass through."""
        la = self._current_output_la
        if la is None or la not in self._open_files:
            return self._passthrough_kernal_jmp()
        f = self._open_files[la]
        if f.get("cmd"):
            b = self.cpu.a & 0xFF
            if b == 0x0D:
                self._exec_disk_command(bytes(self._cmd_out))
                self._cmd_out = bytearray()
            else:
                self._cmd_out.append(b)
            self.cpu.set_flag(self.cpu.FC, False)
            self._do_rts()
            return
        if "da_chan" in f:
            # Writing into a direct-access buffer — accept and ignore (the D64
            # image is read-only), keeping the pointer advancing.
            buf = self._da_buffers.get(f["da_chan"])
            if buf and buf["pos"] < 256:
                buf["pos"] += 1
            self.cpu.set_flag(self.cpu.FC, False)
            self._do_rts()
            return
        return self._passthrough_kernal_jmp()

    def _exec_disk_command(self, cmd):
        """Execute a command sent to the drive's command channel. Supports the
        block-read (U1/UA/B-R) and buffer-pointer (B-P) direct-access commands
        that block loaders use; everything else is acknowledged as OK."""
        self._disk_status = b"00, OK,00,00\r"
        if self._d64 is None:
            return
        s = cmd.strip()
        up = s.upper()

        def nums(rest):
            return rest.replace(b":", b" ").replace(b",", b" ").split()

        if up[:2] in (b"U1", b"UA") or up.startswith(b"B-R"):
            pref = 3 if up.startswith(b"B-R") else 2
            parts = nums(s[pref:])
            if len(parts) >= 4:
                try:
                    chan, drive, track, sector = (int(parts[0]), int(parts[1]),
                                                  int(parts[2]), int(parts[3]))
                    data = self._d64.read_sector(track, sector)
                    buf = self._da_buffers.setdefault(
                        chan, {"data": bytearray(256), "pos": 0})
                    buf["data"] = bytearray(data)
                    buf["pos"] = 0
                except (ValueError, IndexError):
                    self._disk_status = b"34,SYNTAX ERROR,00,00\r"
            return
        if up.startswith(b"B-P"):
            parts = nums(s[3:])
            if len(parts) >= 2:
                try:
                    chan, pos = int(parts[0]), int(parts[1])
                    buf = self._da_buffers.get(chan)
                    if buf is not None:
                        buf["pos"] = pos & 0xFF
                except ValueError:
                    pass
            return
        # Other commands (Initialize, Validate, memory cmds, …): acknowledge OK.

    def _trap_getin(self):
        """KERNAL GETIN ($FFE4). Non-blocking get. For files, identical to
        CHRIN (a file is never 'pending', it has bytes or it doesn't)."""
        if self._current_input_la is None or self._current_input_la not in self._open_files:
            return self._passthrough_kernal_jmp()
        return self._trap_chrin()

    # ---------- low-level serial (IEC) bus emulation ----------

    def _iec_reset(self):
        self._iec_dev = None
        self._iec_mode = None
        self._iec_opening = False
        self._iec_open_chan = 0
        self._iec_name = bytearray()
        self._iec_talk_chan = 0
        self._iec_channels = {}

    def _iec_open_current(self):
        """Resolve the filename accumulated over CIOUT into a byte stream on the
        currently-addressed channel, served from the mounted D64."""
        name = bytes(self._iec_name)
        chan = self._iec_open_chan
        if name.startswith(b"$"):
            data = bytes([0x01, 0x08]) + self._build_dir_listing(load_addr=0x0801)
        elif name:
            found = self._d64.find_file(name)
            data = self._d64.read_file(found[0], found[1]) if found else None
        else:
            data = None
        # A None stream means "file not found" — ACPTR will report device-not-
        # present / EOF so the loader can react rather than hang.
        self._iec_channels[chan] = ({"data": data, "pos": 0}
                                    if data is not None else None)

    def _trap_iec_listen(self):
        """LISTEN ($FFB1). A = device number. Command that device to listen."""
        dev = self.cpu.a & 0x1F
        if dev != 8 or self._d64 is None:
            return self._passthrough_kernal_jmp()
        self._iec_dev = dev
        self._iec_mode = "listen"
        self.cpu.set_flag(self.cpu.FC, False)
        self._do_rts()

    def _trap_iec_second(self):
        """SECOND ($FF93). A = secondary address, sent after LISTEN. The high
        nibble is the command: $Fx = OPEN channel x, $Ex = CLOSE, $6x = data."""
        if self._iec_mode != "listen" or self._iec_dev != 8:
            return self._passthrough_kernal_jmp()
        sa = self.cpu.a & 0xFF
        cmd = sa & 0xF0
        chan = sa & 0x0F
        self._iec_open_chan = chan
        if cmd == 0xF0:                    # OPEN — filename bytes follow
            self._iec_opening = True
            self._iec_name = bytearray()
        else:                             # $Ex CLOSE, $6x plain data channel
            self._iec_opening = False
            if cmd == 0xE0:
                self._iec_channels.pop(chan, None)
        self._do_rts()

    def _trap_iec_ciout(self):
        """CIOUT ($FFA8). A = byte to send to the listening device. While an
        OPEN is in progress these bytes form the filename."""
        if self._iec_mode != "listen" or self._iec_dev != 8:
            return self._passthrough_kernal_jmp()
        if self._iec_opening:
            self._iec_name.append(self.cpu.a & 0xFF)
        # Writes to a data/command channel are ignored (image is read-only).
        self._do_rts()

    def _trap_iec_unlsn(self):
        """UNLSN ($FFAE). End the LISTEN transaction; if we were opening a
        file, resolve it now so a subsequent TALK/ACPTR can read it."""
        if self._iec_mode != "listen" or self._iec_dev != 8:
            return self._passthrough_kernal_jmp()
        if self._iec_opening:
            self._iec_open_current()
            self._iec_opening = False
        self._iec_mode = None
        self._iec_dev = None
        self._do_rts()

    def _trap_iec_talk(self):
        """TALK ($FFB4). A = device number. Command that device to talk."""
        dev = self.cpu.a & 0x1F
        if dev != 8 or self._d64 is None:
            return self._passthrough_kernal_jmp()
        self._iec_dev = dev
        self._iec_mode = "talk"
        self.cpu.set_flag(self.cpu.FC, False)
        self._do_rts()

    def _trap_iec_tksa(self):
        """TKSA ($FF96). A = secondary address after TALK; selects the channel
        whose bytes ACPTR will return."""
        if self._iec_mode != "talk" or self._iec_dev != 8:
            return self._passthrough_kernal_jmp()
        self._iec_talk_chan = self.cpu.a & 0x0F
        self._do_rts()

    def _trap_iec_acptr(self):
        """ACPTR ($FFA5). Return the next byte from the talking channel in A,
        updating the KERNAL status byte ($90): bit 6 (EOI) is set on the last
        byte; bit 1 (timeout) when the channel is empty / file not found."""
        if self._iec_mode != "talk" or self._iec_dev != 8:
            return self._passthrough_kernal_jmp()
        cpu = self.cpu
        mem = self.mem
        stream = self._iec_channels.get(self._iec_talk_chan)
        if not stream:
            cpu.a = 0
            mem.write_ram_direct(0x90, 0x42)      # timeout + EOI (nothing there)
            cpu.set_flag(cpu.FC, False)
            self._do_rts()
            return
        data = stream["data"]
        pos = stream["pos"]
        if pos < len(data):
            cpu.a = data[pos] & 0xFF
            stream["pos"] = pos + 1
            mem.write_ram_direct(0x90, 0x40 if stream["pos"] >= len(data) else 0)
        else:
            cpu.a = 0
            mem.write_ram_direct(0x90, 0x42)      # read past end
        cpu.set_flag(cpu.FC, False)
        self._do_rts()

    def _trap_iec_untalk(self):
        """UNTALK ($FFAB). End the TALK transaction."""
        if self._iec_mode != "talk" or self._iec_dev != 8:
            return self._passthrough_kernal_jmp()
        self._iec_mode = None
        self._iec_dev = None
        self._do_rts()

    def _build_dir_listing(self, load_addr=0x0801):
        """
        Generate a fake BASIC program containing the disk directory, so that
        LOAD"$",8 followed by LIST shows the files — matching the 1541's
        behaviour. Each entry becomes one "BASIC line":

            [link_lo] [link_hi] [blocks_lo] [blocks_hi] <content_bytes> 00

        The first line is the disk header (line# 0, reverse-video disk name +
        ID + DOS type). Subsequent lines have line# = block count and content
        '"NAME            " TYPE'. The list ends with a 00 00 link.
        """
        bam = self._d64.read_sector(18, 0)
        disk_name = bytes(bam[0x90:0xA0])      # 16 bytes, $A0-padded by CBM
        id1, id2  = bam[0xA2], bam[0xA3]
        dos1, dos2 = bam[0xA5], bam[0xA6]

        out  = bytearray()
        addr = load_addr

        def emit_line(line_num, content):
            nonlocal addr
            next_addr = addr + 4 + len(content) + 1
            out.append(next_addr & 0xFF)
            out.append((next_addr >> 8) & 0xFF)
            out.append(line_num & 0xFF)
            out.append((line_num >> 8) & 0xFF)
            out.extend(content)
            out.append(0x00)
            addr = next_addr

        # --- Disk header line (line# 0) ---
        # Reverse-video runs to end of line (matching real 1541 behaviour;
        # we can't use the $92 REVERSE-OFF byte here because BASIC's LIST
        # would de-tokenise it as the WAIT keyword).
        header = bytearray()
        header.append(0x12)                     # REVERSE-ON
        header.append(ord('"'))
        header.extend(disk_name)
        header.append(ord('"'))
        header.append(ord(' '))
        header.append(id1); header.append(id2)
        header.append(ord(' '))
        header.append(dos1); header.append(dos2)
        emit_line(0, bytes(header))

        # --- One line per file ---
        type_names = {0: b"DEL", 1: b"SEQ", 2: b"PRG", 3: b"USR", 4: b"REL"}
        for name, ftype, _t, _s, size in self._d64.list_directory():
            line = bytearray()
            blocks_str = str(size)
            # Pad with spaces so the quote starts at a fixed column
            line.extend(b" " * max(0, 3 - len(blocks_str)))
            line.append(ord('"'))
            line.extend(name + b" " * (16 - len(name)))
            line.append(ord('"'))
            line.append(ord(" "))
            line.extend(type_names.get(ftype & 0x0F, b"???"))
            emit_line(size, bytes(line))

        # End-of-program marker (link = 0)
        out.append(0x00)
        out.append(0x00)
        return bytes(out)

    def _trap_load(self):
        """
        Intercept KERNAL LOAD ($FFD5). Reads SETLFS/SETNAM parameters from
        zero page, looks the file up in the mounted D64, copies it into RAM,
        sets the return registers BASIC expects, and RTSes.

        Zero-page parameters established by SETLFS/SETNAM before LOAD:
            $B7      filename length
            $B9      secondary address (bit 0: 0 = use X/Y, 1 = file's own addr)
            $BA      device number (8 = disk)
            $BB,$BC  filename pointer
        CPU registers on entry:
            A        0 = LOAD, anything else = VERIFY (we treat both as load)
            X, Y     load address when secondary address bit 0 == 0
        On exit (per KERNAL contract):
            C clear  → success; X,Y = end+1, $90 = 0, $AE/$AF = end+1
            C set    → error;   A = error code (4 = file not found)
        """
        cpu = self.cpu
        mem = self.mem

        device   = mem.read_ram_direct(0xBA)
        sec_addr = mem.read_ram_direct(0xB9)
        fnlen    = mem.read_ram_direct(0xB7)
        fnaddr   = (mem.read_ram_direct(0xBB)
                    | (mem.read_ram_direct(0xBC) << 8))
        filename = bytes(mem.read_ram_direct((fnaddr + i) & 0xFFFF)
                         for i in range(fnlen))
        load_addr_xy = cpu.x | (cpu.y << 8)

        if self._d64 is None or (device != 8 and
                                 not (device == 1 and self._is_tape)):
            cpu.a = 4                          # FILE NOT FOUND
            cpu.set_flag(cpu.FC, True)
            self._do_rts()
            return

        # Special case: LOAD"$" returns the directory as a fake BASIC program.
        # The filename is anything starting with '$' (real CBM also supports
        # "$:pattern" to filter — we ignore the filter for simplicity).
        if filename.startswith(b"$"):
            payload = self._build_dir_listing(load_addr=0x0801)
            file_data = bytes([0x01, 0x08]) + payload
        else:
            found = self._d64.find_file(filename)
            if found is None:
                cpu.a = 4
                cpu.set_flag(cpu.FC, True)
                self._do_rts()
                return
            track, sector, _size_sectors = found
            file_data = self._d64.read_file(track, sector)
            if len(file_data) < 2:
                cpu.a = 4
                cpu.set_flag(cpu.FC, True)
                self._do_rts()
                return

        file_load = file_data[0] | (file_data[1] << 8)
        payload   = file_data[2:]
        # KERNAL LOAD relocate rule: secondary address == 0 relocates to the
        # caller's X/Y address; ANY non-zero secondary address performs an
        # absolute load to the file's own start address. (The real KERNAL tests
        # the whole SA byte with BNE, not just bit 0 — so LOAD"x",8,8 is
        # absolute, exactly like LOAD"x",8,1.)
        load_to   = file_load if (sec_addr != 0) else load_addr_xy
        end       = (load_to + len(payload)) & 0xFFFF

        mem.load_ram(load_to, payload)

        # Set BASIC's end-of-load pointer ($AE/$AF) and the status byte ($90).
        mem.write_ram_direct(0x90, 0)
        mem.write_ram_direct(0xAE, end & 0xFF)
        mem.write_ram_direct(0xAF, (end >> 8) & 0xFF)

        # If we loaded into the BASIC area, refresh BASIC's pointers so
        # variables start above the freshly-loaded program and RUN works.
        # We also write an explicit end-of-program marker ($00 $00) and reset
        # the string heap pointers — BASIC's own LOAD-completion code does
        # this on the real machine via CLR, but since we're trapping at
        # $FFD5 (before that code runs) some KERNAL variants skip it.
        if load_to == 0x0801:
            # End-of-program marker right after the loaded data
            mem.write_ram_direct(end,     0x00)
            mem.write_ram_direct(end + 1, 0x00)
            var_start = (end + 2) & 0xFFFF
            for addr in (0x2D, 0x2F, 0x31):    # VARTAB / ARYTAB / STREND
                mem.write_ram_direct(addr,     var_start & 0xFF)
                mem.write_ram_direct(addr + 1, (var_start >> 8) & 0xFF)
            # String heap pointers: FRETOP/MEMSIZ point to top of BASIC area
            # ($A000 by default when BASIC ROM is mapped in)
            for addr in (0x33, 0x37):
                mem.write_ram_direct(addr,     0x00)
                mem.write_ram_direct(addr + 1, 0xA0)

        # End address goes back in X/Y; A=0 status OK; carry clear.
        cpu.x = end & 0xFF
        cpu.y = (end >> 8) & 0xFF
        cpu.a = 0
        cpu.set_flag(cpu.FC, False)
        # Crude cycle cost: a few thousand for the directory walk + load.
        cpu.cycles += 1000 + len(payload) * 8
        self._do_rts()

    def reset(self):
        """Soft-reset: PLA back to default, CPU re-reads reset vector."""
        self.mem.reset()
        self.vic.__init__()
        self.sid.__init__()
        self.cia1.__init__("CIA1")
        self.cia2.__init__("CIA2")
        self.cpu.reset()
        self._sid_play_addr = 0


# =============================================================================
# Pygame frontend — text-mode rendering and keyboard input
# =============================================================================

# Standard C64 palette (RGB values from VICE / Pepto's measured palette)
C64_PALETTE = [
    (0x00, 0x00, 0x00),  # 0  black
    (0xFF, 0xFF, 0xFF),  # 1  white
    (0x68, 0x37, 0x2B),  # 2  red
    (0x70, 0xA4, 0xB2),  # 3  cyan
    (0x6F, 0x3D, 0x86),  # 4  purple
    (0x58, 0x8D, 0x43),  # 5  green
    (0x35, 0x28, 0x79),  # 6  blue
    (0xB8, 0xC7, 0x6F),  # 7  yellow
    (0x6F, 0x4F, 0x25),  # 8  orange
    (0x43, 0x39, 0x00),  # 9  brown
    (0x9A, 0x67, 0x59),  # 10 light red
    (0x44, 0x44, 0x44),  # 11 dark grey
    (0x6C, 0x6C, 0x6C),  # 12 grey
    (0x9A, 0xD2, 0x84),  # 13 light green
    (0x6C, 0x5E, 0xB5),  # 14 light blue
    (0x95, 0x95, 0x95),  # 15 light grey
]

# Host key -> C64 keyboard matrix (row, col). Filled lazily because pygame
# constants only exist after `import pygame`.
def _build_key_map(pygame):
    p = pygame
    return {
        # Letters
        p.K_a: (1, 2), p.K_b: (3, 4), p.K_c: (2, 4), p.K_d: (2, 2),
        p.K_e: (1, 6), p.K_f: (2, 5), p.K_g: (3, 2), p.K_h: (3, 5),
        p.K_i: (4, 1), p.K_j: (4, 2), p.K_k: (4, 5), p.K_l: (5, 2),
        p.K_m: (4, 4), p.K_n: (4, 7), p.K_o: (4, 6), p.K_p: (5, 1),
        p.K_q: (7, 6), p.K_r: (2, 1), p.K_s: (1, 5), p.K_t: (2, 6),
        p.K_u: (3, 6), p.K_v: (3, 7), p.K_w: (1, 1), p.K_x: (2, 7),
        p.K_y: (3, 1), p.K_z: (1, 4),
        # Digits
        p.K_0: (4, 3), p.K_1: (7, 0), p.K_2: (7, 3), p.K_3: (1, 0),
        p.K_4: (1, 3), p.K_5: (2, 0), p.K_6: (2, 3), p.K_7: (3, 0),
        p.K_8: (3, 3), p.K_9: (4, 0),
        # Symbols
        p.K_SPACE: (7, 4),
        p.K_RETURN: (0, 1),
        p.K_BACKSPACE: (0, 0),                 # DEL
        p.K_LSHIFT: (1, 7),
        p.K_RSHIFT: (6, 4),
        p.K_COMMA: (5, 7),
        p.K_PERIOD: (5, 4),
        p.K_SLASH: (6, 7),
        p.K_SEMICOLON: (6, 2),
        p.K_QUOTE: (3, 0),                     # ' shares with 7 on C64
        p.K_EQUALS: (6, 5),
        p.K_MINUS: (5, 3),
        p.K_LEFTBRACKET: (5, 6),               # @
        p.K_RIGHTBRACKET: (6, 1),              # *
        p.K_BACKSLASH: (6, 0),                 # £
        # (Arrow keys are handled as joystick-only in _rebuild_matrix; they are
        #  intentionally not mapped to the C64 cursor keys — see the note there.)
        # Function keys
        p.K_F1: (0, 4),
        p.K_F3: (0, 5),
        p.K_F5: (0, 6),
        p.K_F7: (0, 3),
        # Special
        p.K_ESCAPE: (7, 7),                    # RUN/STOP
        p.K_HOME: (6, 3),                      # CLR/HOME
        p.K_TAB: (7, 2),                       # CTRL
        p.K_BACKQUOTE: (7, 1),                 # arrow-left
        p.K_LCTRL: (7, 5),                     # Commodore key
    }


class PygameFrontend:
    """
    Renders the VIC text-mode framebuffer to a pygame window and feeds key
    events into CIA1's keyboard matrix. Runs the emulator in catch-up mode,
    one PAL frame per host frame.
    """

    SCREEN_W = 320
    SCREEN_H = 200
    BORDER_X = 32
    BORDER_Y = 36
    CYCLES_PER_FRAME = 19656    # PAL: 985248 Hz / 50 Hz

    def __init__(self, system, scale=2, target_hz=50):
        import pygame
        import numpy as np
        self.pygame = pygame
        self.np = np
        self.system = system
        self.scale = scale
        self.target_hz = target_hz
        pygame.init()
        pygame.display.set_caption(f"C64 — Python emulator  [{__version__}]")
        self.window = pygame.display.set_mode(
            ((self.SCREEN_W + 2 * self.BORDER_X) * scale,
             (self.SCREEN_H + 2 * self.BORDER_Y) * scale))
        self.frame_surf = pygame.Surface((self.SCREEN_W + 2 * self.BORDER_X,
                                          self.SCREEN_H + 2 * self.BORDER_Y))
        # Precompute chargen as (256, 8, 8) bit array, for both charsets.
        cg = system.chargen_rom
        self._chargen = np.zeros((512, 8, 8), dtype=np.uint8)
        for ch in range(512):
            for y in range(8):
                b = cg[ch * 8 + y] if ch * 8 + y < len(cg) else 0
                for x in range(8):
                    if b & (1 << (7 - x)):
                        self._chargen[ch, y, x] = 1
        self._palette = np.array(C64_PALETTE, dtype=np.uint8)
        self.key_map = _build_key_map(pygame)
        self._keys_down = set()    # host pygame keycodes currently pressed
        # Which control port the numeric-keypad joystick drives: 0 = port 1
        # ($DC01), 1 = port 2 ($DC00). Toggle at runtime with keypad 0.
        # Default is port 2 — the port most C64 games read (Elite, etc.), and
        # the one that does NOT share row lines with the keyboard, so the
        # keypad joystick can't "ghost" into menu keys. A few games use port 1
        # (e.g. Bruce Lee reads $DC01); press keypad 0 to switch for those.
        self._joy_port = 1
        self.shown_fps = 0.0
        self.warp = False    # True = run as fast as possible (no host frame cap)

        # Audio output — pygame.mixer streaming via Channel.queue()
        self.audio_enabled = False
        self.samples_per_frame = system.sid.SAMPLE_RATE // target_hz
        try:
            pygame.mixer.init(frequency=system.sid.SAMPLE_RATE, size=-16,
                              channels=1, buffer=4096)
            self.audio_channel = pygame.mixer.Channel(0)
            self.audio_enabled = True
        except pygame.error as ex:
            print(f"Audio disabled: {ex}")

    def _key_event(self, host_key, pressed):
        """
        Update the CIA1 keyboard matrix from a host pygame keystroke.
        UP and LEFT are virtual on the C64 — they're SHIFT + CRSR-DOWN
        and SHIFT + CRSR-RIGHT respectively. We track which host keys are
        physically down and rebuild the matrix each time so the synthesised
        SHIFT doesn't get stripped when the user is also holding real SHIFT.
        """
        if pressed:
            self._keys_down.add(host_key)
        else:
            self._keys_down.discard(host_key)
        self._rebuild_matrix()

    def _rebuild_matrix(self):
        p = self.pygame
        mat = self.system.cia1.keyboard_matrix
        mat.clear()
        # Joystick: bits 0..4 = up/down/left/right/fire (pressed = 1 in our
        # convention). We mirror state to both port 1 and port 2 so games that
        # use either work — most use port 2, Lode Runner uses port 1.
        # Joystick is the numeric keypad only (8/2/4/6 = directions, 5 = fire).
        # Keypad 0 toggles which control port it drives (handled in the event
        # loop). We drive only the selected port and clear the other, so it
        # behaves like a single joystick plugged into one port — like real HW.
        joy = 0
        for key in self._keys_down:
            if   key == p.K_KP8: joy |= 1 << 0    # up
            elif key == p.K_KP2: joy |= 1 << 1    # down
            elif key == p.K_KP4: joy |= 1 << 2    # left
            elif key == p.K_KP6: joy |= 1 << 3    # right
            elif key in (p.K_KP5, p.K_KP_ENTER): joy |= 1 << 4   # fire
        self.system.cia1.joystick_state[self._joy_port] = joy
        self.system.cia1.joystick_state[1 - self._joy_port] = 0
        # Keyboard matrix. The PC arrow keys map to the authentic C64 cursor
        # keys: the real machine had only TWO cursor keys — CRSR↕ (0,7) and
        # CRSR⇄ (0,2) — with the up/left directions produced by holding SHIFT.
        for key in self._keys_down:
            if key == p.K_UP:
                mat.add((1, 7))                # left shift
                mat.add((0, 7))                # CRSR↕ → with shift = up
            elif key == p.K_LEFT:
                mat.add((1, 7))                # left shift
                mat.add((0, 2))                # CRSR⇄ → with shift = left
            elif key == p.K_DOWN:
                mat.add((0, 7))                # CRSR↕ (down)
            elif key == p.K_RIGHT:
                mat.add((0, 2))                # CRSR⇄ (right)
            else:
                m = self.key_map.get(key)
                if m is not None:
                    mat.add(m)

    def _current_charset_offset(self):
        # $D018 bits 1-3 select character data within VIC bank.
        # In the default setup (VIC bank 0), bit 1 toggles upper/graphics
        # ($1000) vs lower/upper ($1800). chargen ROM has uppercase at
        # offset 0 and lowercase at offset $0800.
        d018 = self.system.vic.regs[0x18]
        return 0x100 if (d018 & 0x02) else 0     # 0x100 chars * 8 bytes = $800

    def _active_chargen(self):
        """
        Build a (256, 8, 8) bitmap of the currently-active character set,
        honouring CIA2's VIC-bank selection and $D018 bits 3-1 (char base).
        Reads from chargen ROM when char_base is in the $1000-$1FFF region
        of VIC banks 0/2 (where the chargen is shadowed); otherwise from RAM.
        Rebuilt each frame so games that swap fonts on the fly work.
        """
        np = self.np
        vic = self.system.vic
        mem = self.system.mem
        bank = mem.vic_bank()
        char_base = ((vic.display_regs[0x18] >> 1) & 0x07) * 0x0800   # 0..0x3800
        if bank in (0, 2) and 0x1000 <= char_base < 0x2000:
            # Chargen ROM shadowed at this position
            cg_off = char_base & 0x0FFF                       # 0 or 0x800
            raw = self.system.chargen_rom[cg_off : cg_off + 2048]
        else:
            full = bank * 0x4000 + char_base
            raw = bytes(mem.ram[full : full + 2048])
        # Convert 2048 bytes → (256, 8) → (256, 8, 8) bits
        arr = np.frombuffer(raw, dtype=np.uint8).reshape(256, 8)
        return np.unpackbits(arr, axis=1).reshape(256, 8, 8)

    def _chargen_for(self, bank, cb_sel):
        """Build a (256,8,8) bit array for one character-base selector
        (D018 bits 3-1) within the given VIC bank."""
        np = self.np
        char_base = (cb_sel & 0x07) * 0x0800
        if bank in (0, 2) and 0x1000 <= char_base < 0x2000:
            cg_off = char_base & 0x0FFF                       # 0 or 0x800
            raw = self.system.chargen_rom[cg_off : cg_off + 2048]
        else:
            full = bank * 0x4000 + char_base
            raw = bytes(self.system.mem.ram[full : full + 2048])
        arr = np.frombuffer(raw, dtype=np.uint8).reshape(256, 8)
        return np.unpackbits(arr, axis=1).reshape(256, 8, 8)

    # Raster line of the top of the 25-row display window (RSEL=1, YSCROLL=3).
    FIRST_DISPLAY_LINE = 51

    def _build_char_masks(self, codes):
        """
        Return the (25,40,8,8) bit masks for the character cells, giving each
        text row the font that was active at its raster position. This makes
        vertical raster splits on $D018 (e.g. a status line in one font over a
        playfield in another) render correctly. Distinct fonts are built once
        and cached, so the common case (1-2 fonts per frame) stays cheap.
        """
        np = self.np
        vic = self.system.vic
        bank = self.system.mem.vic_bank()
        line_d018 = vic.line_d018
        n = len(line_d018)
        cache = {}
        masks = np.empty((25, 40, 8, 8), dtype=np.uint8)
        for r in range(25):
            raster = (self.FIRST_DISPLAY_LINE + r * 8 + 4) % n
            cb_sel = (line_d018[raster] >> 1) & 0x07
            cg = cache.get(cb_sel)
            if cg is None:
                cg = self._chargen_for(bank, cb_sel)
                cache[cb_sel] = cg
            masks[r] = cg[codes[r]]
        return masks

    def _render_charmode_multicolor(self, masks, color_ram, vic):
        """
        Render the background in multicolor character mode (D016 bit 4 set).

        Per character cell the colour RAM nibble decides the sub-mode:
          * bit 3 = 0  -> standard hi-res, but only the low 3 colour bits are
                          available (8 colours); fg = colour & 7, bg = D021.
          * bit 3 = 1  -> multicolor: horizontal pixel pairs (double width)
                          select one of four colours by their 2-bit value:
                              00 = background      (D021)
                              01 = background#1    (D022)
                              10 = background#2    (D023)
                              11 = character col   (colour RAM & 7)

        `masks` is the (25,40,8,8) per-row character bitmap (built with the
        correct per-row font). Returns (pixels[200,320,3], bitmap[200,320]).
        The foreground mask (for sprite priority/collision) counts a pixel as
        foreground when its 2-bit value has bit 1 set (values 2 and 3) for
        multicolor cells, or when the bit is set for hi-res cells.
        """
        np = self.np
        pal = self._palette
        d021 = vic.display_regs[0x21] & 0x0F
        d022 = vic.display_regs[0x22] & 0x0F
        d023 = vic.display_regs[0x23] & 0x0F

        cell_col = (color_ram & 0x07)                       # (25,40)
        mc_cell = (color_ram & 0x08) != 0                   # (25,40) bool

        # --- multicolor interpretation: 2-bit pairs, doubled horizontally ---
        pairs = masks.reshape(25, 40, 8, 4, 2)
        twobit = (pairs[..., 0] << 1) | pairs[..., 1]       # (25,40,8,4) values 0..3
        twobit = np.repeat(twobit, 2, axis=3)               # (25,40,8,8) double-wide

        # colour index per pixel for multicolor cells, via per-cell lookup table
        choices = np.stack([                                # (25,40,4)
            np.full((25, 40), d021, dtype=np.uint8),
            np.full((25, 40), d022, dtype=np.uint8),
            np.full((25, 40), d023, dtype=np.uint8),
            cell_col.astype(np.uint8),
        ], axis=2)
        choices_b = np.broadcast_to(choices[:, :, None, None, :], (25, 40, 8, 8, 4))
        colidx_mc = np.take_along_axis(choices_b, twobit[..., None], axis=4)[..., 0]

        # colour index per pixel for hi-res cells (bg where bit clear)
        colidx_hi = np.where(masks.astype(bool),
                             cell_col[:, :, None, None].astype(np.uint8),
                             np.uint8(d021))

        mc_b = mc_cell[:, :, None, None]
        colidx = np.where(mc_b, colidx_mc, colidx_hi)       # (25,40,8,8)

        # foreground mask for sprite priority / collisions
        fg_mc = twobit >= 2
        fg_hi = masks.astype(bool)
        fg = np.where(mc_b, fg_mc, fg_hi)                   # (25,40,8,8)

        colidx = colidx.transpose(0, 2, 1, 3).reshape(200, 320)
        bitmap = fg.transpose(0, 2, 1, 3).reshape(200, 320).astype(np.uint8)
        pixels = pal[colidx].astype(np.uint8)
        return pixels, bitmap

    def _render_bitmap_rows(self, rows, d018, d016, color_ram, bank_off):
        """
        Render a contiguous span of character rows in VIC bitmap mode (D011
        bit 5 set). `rows` is a range of char-row indices (0..24) that all share
        the same $D018/$D016. Returns (pixels[h,320,3], mask[h,320]) for those
        rows, where h = len(rows)*8.

        Hi-res bitmap (MCM=0): each 8x8 cell has two colours from the video
        matrix byte — high nibble = set-pixel colour, low nibble = clear-pixel.
        Multicolor bitmap (MCM=1): 2-bit pixels (double width): 00=$D021,
        01=matrix high nibble, 10=matrix low nibble, 11=colour-RAM nibble.

        $D018: bit 3 selects the 8 KB bitmap base within the VIC bank; bits 4-7
        select the video-matrix (colour) base.
        """
        np = self.np
        pal = self._palette
        mem = self.system.mem
        bmp_base = bank_off + (((d018 >> 3) & 1) * 0x2000)
        vm_base  = bank_off + (((d018 >> 4) & 0x0F) * 0x400)
        r0 = rows[0]
        nrows = len(rows)
        ncells = nrows * 40
        raw = np.frombuffer(
            bytes(mem.ram[bmp_base + r0 * 320: bmp_base + r0 * 320 + ncells * 8]),
            dtype=np.uint8).reshape(nrows, 40, 8)
        vm = np.frombuffer(
            bytes(mem.ram[vm_base + r0 * 40: vm_base + r0 * 40 + ncells]),
            dtype=np.uint8).reshape(nrows, 40)
        bits = np.unpackbits(raw.reshape(ncells, 8), axis=1).reshape(nrows, 40, 8, 8)

        if not (d016 & 0x10):                      # hi-res bitmap
            fg = pal[(vm >> 4) & 0x0F]             # (nrows,40,3)
            bg = pal[vm & 0x0F]
            px = np.where(bits[..., None].astype(bool),
                          fg[:, :, None, None, :], bg[:, :, None, None, :])
            mask = bits
        else:                                      # multicolor bitmap
            d021 = self.system.vic.display_regs[0x21] & 0x0F
            pb = bits.reshape(nrows, 40, 8, 4, 2)
            twobit = (pb[..., 0] << 1) | pb[..., 1]           # (nrows,40,8,4)
            twobit = np.repeat(twobit, 2, axis=3)             # (nrows,40,8,8)
            cram = color_ram[rows.start:rows.stop] & 0x0F     # (nrows,40)
            choices = np.stack([
                np.full((nrows, 40), d021, dtype=np.uint8),
                ((vm >> 4) & 0x0F).astype(np.uint8),
                (vm & 0x0F).astype(np.uint8),
                cram.astype(np.uint8),
            ], axis=2)                                        # (nrows,40,4)
            cb = np.broadcast_to(choices[:, :, None, None, :],
                                 (nrows, 40, 8, 8, 4))
            colidx = np.take_along_axis(cb, twobit[..., None], axis=4)[..., 0]
            px = pal[colidx]
            mask = (twobit >= 2)

        pixels = px.transpose(0, 2, 1, 3, 4).reshape(nrows * 8, 320, 3).astype(np.uint8)
        maskout = mask.transpose(0, 2, 1, 3).reshape(nrows * 8, 320).astype(np.uint8)
        return pixels, maskout

    def _push_audio(self):
        """Generate and enqueue one frame of SID audio."""
        samples = self.system.sid.generate_samples(self.samples_per_frame, self.np)
        samples = self.np.clip(samples, -1.0, 1.0)
        s16_mono = (samples * 32767.0).astype(self.np.int16)
        # Duplicate mono to stereo for the default pygame mixer config
        s16 = self.np.column_stack((s16_mono, s16_mono))
        sound = self.pygame.sndarray.make_sound(s16)
        # If channel is busy, queue; else play. Keeps a 1-2 frame buffer.
        if not self.audio_channel.get_busy():
            self.audio_channel.play(sound)
        elif self.audio_channel.get_queue() is None:
            self.audio_channel.queue(sound)
        # else: queue full, drop this frame's audio (we're behind)

    def render_frame(self):
        np = self.np
        vic = self.system.vic
        mem = self.system.mem
        dr = vic.display_regs          # latched mid-frame (raster-split safe)
        bg_color   = dr[0x21] & 0x0F
        border     = dr[0x20] & 0x0F
        # Border
        self.frame_surf.fill(C64_PALETTE[border])

        # --- Background (text mode) ---
        # Honor VIC bank + $D018 video matrix base for screen RAM lookup.
        # The base can change mid-frame in a raster split (e.g. The Hobbit:
        # bitmap graphics on top, a text window below with a different $D018),
        # so read each character row's codes from the base that was active at
        # that row's raster line rather than a single global base.
        bank_off = mem.vic_bank() * 0x4000
        ld18 = vic.line_d018
        nld = len(ld18)
        screen_ram = np.empty((25, 40), dtype=np.uint8)
        for r in range(25):
            raster = (self.FIRST_DISPLAY_LINE + r * 8 + 4) % nld
            sb = bank_off + ((ld18[raster] >> 4) & 0x0F) * 0x0400
            screen_ram[r] = np.frombuffer(
                bytes(mem.ram[sb + r * 40: sb + r * 40 + 40]), dtype=np.uint8)
        color_ram = np.frombuffer(
            bytes(self.system.color_ram.ram[:0x400]),
            dtype=np.uint8)[:1000].reshape(25, 40) & 0x0F

        # Char bitmap pulled fresh from VIC memory each frame, so games with
        # custom character sets (e.g. games that build their own fonts in RAM)
        # render correctly. $D018 bits 3-1 select the chargen base.
        # NOTE: in standard C64 text mode, bit 7 of the screen code is NOT a
        # reverse-video flag. The chargen ROM already stores the reverse
        # versions at codes $80-$FF (chargen[$A0] = reverse-space bitmap), so
        # we just index the chargen directly with the full byte.
        # Character bitmaps, one font per row according to the $D018 value
        # active at that row's raster line (handles vertical raster splits).
        codes = (screen_ram & 0xFF).astype(np.int32)
        masks = self._build_char_masks(codes)               # (25,40,8,8)
        # Character display mode: standard hi-res text, or multicolor text
        # (D016 bit 4). Extended-colour / bitmap modes fall back to hi-res.
        if dr[0x16] & 0x10:
            pixels, bitmap = self._render_charmode_multicolor(
                masks, color_ram, vic)
        else:
            bitmap = masks.transpose(0, 2, 1, 3).reshape(200, 320)
            fg_colors_per_pixel = np.repeat(np.repeat(color_ram, 8, axis=0), 8, axis=1)
            fg_rgb = self._palette[fg_colors_per_pixel]
            bg_rgb = self._palette[bg_color]
            pixels = np.where(bitmap[:, :, None], fg_rgb, bg_rgb).astype(np.uint8)

        # --- Bitmap-mode overlay ---
        # Any character row whose $D011 (recorded at its raster line) has BMM
        # set is drawn in bitmap mode instead of text. Contiguous rows sharing
        # $D018/$D016 are rendered together. This makes split screens like
        # Elite (bitmap 3D view above a text dashboard) come out right.
        ld11 = vic.line_d011
        ld16 = vic.line_d016
        ld18 = vic.line_d018
        n = len(ld11)
        r = 0
        while r < 25:
            raster = (self.FIRST_DISPLAY_LINE + r * 8 + 4) % n
            if (ld11[raster] >> 5) & 1:                 # BMM set → bitmap row
                d018 = ld18[raster]
                d016 = ld16[raster]
                end = r
                while end < 25:
                    rr = (self.FIRST_DISPLAY_LINE + end * 8 + 4) % n
                    if not ((ld11[rr] >> 5) & 1):
                        break
                    if ld18[rr] != d018 or (ld16[rr] & 0x10) != (d016 & 0x10):
                        break
                    end += 1
                rp, rm = self._render_bitmap_rows(range(r, end), d018, d016,
                                                  color_ram, bank_off)
                pixels[r * 8:end * 8] = rp
                bitmap[r * 8:end * 8] = rm
                r = end
            else:
                r += 1

        # --- Sprites ---
        # bitmap (200, 320) is the foreground mask used for priority + collisions.
        # sprite_occupancy: per-pixel which sprite (bit 0..7) covers each pixel
        sprite_occupancy = np.zeros((200, 320), dtype=np.uint8)
        # Render in REVERSE order so sprite 0 ends up drawn on top of sprite 7
        # (lower sprite number = higher hardware priority on real VIC-II).
        for s in range(7, -1, -1):
            self._render_sprite(s, pixels, bitmap, sprite_occupancy)
        # Collision detection: any pixel where 2+ sprites overlap
        multi = sprite_occupancy & (sprite_occupancy - 1)    # clears lowest set bit
        if multi.any():
            # OR sprites involved into the collision latch
            cols = sprite_occupancy[multi != 0]
            ss = 0
            for v in cols:
                ss |= int(v)
            old = vic.sprite_sprite_coll
            vic.sprite_sprite_coll |= ss
            if old == 0 and ss:
                vic.irq_status |= 0x04                        # sprite-sprite IRQ src

        # Render to surface
        surf = self.pygame.surfarray.make_surface(pixels.swapaxes(0, 1))
        self.frame_surf.blit(surf, (self.BORDER_X, self.BORDER_Y))
        if self.scale == 1:
            self.window.blit(self.frame_surf, (0, 0))
        else:
            scaled = self.pygame.transform.scale(self.frame_surf,
                                                 self.window.get_size())
            self.window.blit(scaled, (0, 0))
        self.pygame.display.set_caption(
            f"C64 — Python emulator   [{self.shown_fps:.1f} fps]"
            f"   [Joy: Port {self._joy_port + 1}]")
        self.pygame.display.flip()

    def _render_sprite(self, idx, pixels, bg_mask, sprite_occupancy):
        """
        Render sprite `idx` onto `pixels` (200x320x3), respecting priority and
        recording collisions with `bg_mask` (foreground pixel mask).
        Writes the sprite's bit-flag into `sprite_occupancy` everywhere it draws.
        """
        np = self.np
        vic = self.system.vic
        mem = self.system.mem
        enabled = (vic.regs[0x15] >> idx) & 1
        if not enabled:
            return
        # Position (VIC coordinates: X=24, Y=50 is top-left of visible area)
        spr_x = vic.regs[idx * 2] | (((vic.regs[0x10] >> idx) & 1) << 8)
        spr_y = vic.regs[idx * 2 + 1]
        multicolor = (vic.regs[0x1C] >> idx) & 1
        y_expand   = (vic.regs[0x17] >> idx) & 1
        x_expand   = (vic.regs[0x1D] >> idx) & 1
        priority   = (vic.regs[0x1B] >> idx) & 1            # 1 = bg in front
        sprite_color = vic.regs[0x27 + idx] & 0x0F

        # Fetch sprite data via VIC view (pointers live in the displayed matrix)
        screen_base_in_bank = ((vic.display_regs[0x18] >> 4) & 0x0F) * 0x0400
        pointer = mem.read_vic(screen_base_in_bank + 0x03F8 + idx)
        data_addr = pointer * 64
        sd = mem.read_vic_bytes(data_addr, 63)

        # Build pixel grid (h, w) with color-index values:
        #   hi-res:     0=transparent, 1=sprite color
        #   multicolor: 0=transparent, 1=MC0, 2=spritecol, 3=MC1
        if multicolor:
            bits = np.zeros((21, 12), dtype=np.uint8)
            for y in range(21):
                for bx in range(3):
                    b = sd[y * 3 + bx]
                    bits[y, bx * 4 + 0] = (b >> 6) & 0x03
                    bits[y, bx * 4 + 1] = (b >> 4) & 0x03
                    bits[y, bx * 4 + 2] = (b >> 2) & 0x03
                    bits[y, bx * 4 + 3] = b & 0x03
            bits = np.repeat(bits, 2, axis=1)                # multicolor pixel is 2 wide
        else:
            bits_flat = np.unpackbits(np.frombuffer(sd, dtype=np.uint8))
            bits = bits_flat[:21 * 24].reshape(21, 24)
        if x_expand: bits = np.repeat(bits, 2, axis=1)
        if y_expand: bits = np.repeat(bits, 2, axis=0)
        h, w = bits.shape

        # Convert VIC coords to inner-area (0..319, 0..199)
        inner_x = spr_x - 24
        inner_y = spr_y - 50
        # Clip
        src_x0 = max(0, -inner_x)
        src_y0 = max(0, -inner_y)
        src_x1 = min(w, 320 - inner_x)
        src_y1 = min(h, 200 - inner_y)
        if src_x0 >= src_x1 or src_y0 >= src_y1:
            return                                            # off-screen
        dst_x0 = max(0, inner_x)
        dst_y0 = max(0, inner_y)
        dst_x1 = dst_x0 + (src_x1 - src_x0)
        dst_y1 = dst_y0 + (src_y1 - src_y0)

        sprite_slice = bits[src_y0:src_y1, src_x0:src_x1]
        nonzero = sprite_slice != 0
        if not nonzero.any():
            return

        # Build color RGB for each visible pixel
        if multicolor:
            mc0 = vic.regs[0x25] & 0x0F
            mc1 = vic.regs[0x26] & 0x0F
            color_lookup = np.array([
                [0, 0, 0],                                   # idx 0 unused (transparent)
                C64_PALETTE[mc0],
                C64_PALETTE[sprite_color],
                C64_PALETTE[mc1],
            ], dtype=np.uint8)
            rgb_pixels = color_lookup[sprite_slice]          # (h, w, 3)
        else:
            sprite_rgb = np.array(C64_PALETTE[sprite_color], dtype=np.uint8)
            rgb_pixels = np.broadcast_to(sprite_rgb,
                                         sprite_slice.shape + (3,)).copy()

        # Priority mask: if priority bit, only draw where bg is bg (mask==0)
        bg_slice = bg_mask[dst_y0:dst_y1, dst_x0:dst_x1]
        if priority:
            draw_mask = nonzero & (bg_slice == 0)
        else:
            draw_mask = nonzero

        # Sprite-background collision: where sprite non-transparent meets fg pixel
        coll_mask = nonzero & (bg_slice != 0)
        if coll_mask.any():
            old = vic.sprite_data_coll
            vic.sprite_data_coll |= (1 << idx)
            if old == 0:
                vic.irq_status |= 0x02                        # sprite-data IRQ src

        # Write sprite pixels
        target = pixels[dst_y0:dst_y1, dst_x0:dst_x1]
        target[draw_mask] = rgb_pixels[draw_mask]

        # Record where this sprite drew (for sprite-sprite collision pass)
        occ_slice = sprite_occupancy[dst_y0:dst_y1, dst_x0:dst_x1]
        occ_slice |= (nonzero.astype(np.uint8) << idx)

    def run(self):
        clock = self.pygame.time.Clock()
        last = time.perf_counter()
        frames = 0
        running = True
        while running:
            for event in self.pygame.event.get():
                if event.type == self.pygame.QUIT:
                    running = False
                elif event.type == self.pygame.KEYDOWN:
                    # Host hotkeys (not passed to the C64)
                    if event.key == self.pygame.K_F11:
                        self.warp = not self.warp
                        print(f"Warp mode: {'ON' if self.warp else 'OFF'}")
                        continue
                    if event.key == self.pygame.K_F12:
                        print("Soft reset")
                        self.system.reset()
                        continue
                    if event.key == self.pygame.K_KP0:
                        # Toggle the keypad joystick between port 2 and port 1
                        self._joy_port ^= 1
                        # Clear both ports so a direction held across the switch
                        # doesn't linger on the old port.
                        self.system.cia1.joystick_state[0] = 0
                        self.system.cia1.joystick_state[1] = 0
                        print(f"Keypad joystick → Port {self._joy_port + 1}")
                        continue
                    self._key_event(event.key, True)
                elif event.type == self.pygame.KEYUP:
                    self._key_event(event.key, False)
            # SID-file playback (no-op for PRG / native mode)
            self.system.sid_play_tick()
            # Run one frame's worth of CPU cycles
            self.system.run(self.CYCLES_PER_FRAME)
            # Audio out
            if self.audio_enabled:
                self._push_audio()
            self.render_frame()
            frames += 1
            now = time.perf_counter()
            if now - last >= 1.0:
                self.shown_fps = frames / (now - last)
                frames = 0
                last = now
            if not self.warp:
                clock.tick(self.target_hz)
        self.pygame.quit()


# =============================================================================
# Embedded Klaus Dormann 6502 functional test (compressed)
# =============================================================================

_TEST_PROG_B64 = (
    "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"
    "C3xpV08="
)

def _get_test_program():
    return zlib.decompress(base64.b64decode(''.join(_TEST_PROG_B64.split())))


class C64Emu:
    """Headless CPU test runner — no chips, no ROMs, pure RAM mode."""

    def __init__(self):
        self.mem = Memory()
        self.cpu = CPU(self.mem)

    def test_cpu(self, stop_val=-1, pass_pc=0x3463, verbose=False):
        """
        Load and run the Klaus Dormann 6502 functional test.
        Returns True if PC reaches `pass_pc`, False on any infinite-loop trap.
        """
        load_addr = 0x0400
        self.mem.write_system_byte(Config.ADDR_PROCESSOR_PORT_REG, 0)
        self.mem.load_ram(load_addr, _get_test_program())
        self.cpu.pc = load_addr
        self.cpu.trace = verbose

        prev_pc = -1
        steps = 0
        while True:
            if self.cpu.pc == pass_pc:
                print(f"TEST PASSED at PC={word2hex(self.cpu.pc)} "
                      f"after {steps} steps, {self.cpu.cycles} cycles.")
                return True
            if self.cpu.pc == prev_pc:
                print(f"Infinite loop (trap) at PC={word2hex(self.cpu.pc)} "
                      f"after {steps} steps, {self.cpu.cycles} cycles.")
                return False
            if 0 <= stop_val < 0x10000 and self.cpu.pc == stop_val:
                print(f"Debug stop at PC={word2hex(self.cpu.pc)}")
            prev_pc = self.cpu.pc
            if not self.cpu.step():
                return False
            steps += 1
            if steps % 1_000_000 == 0:
                print(f"... {steps:>10,} steps, PC={word2hex(self.cpu.pc)}, "
                      f"cyc={self.cpu.cycles:,}")



# =============================================================================
# Embedded ROMs — local personal copy, embedded by embed_my_roms.py.
# (Replaces the GPL-3 Open Roms that came with the original file.)
#
# These are *not* the original Commodore C64 ROMs. They are clean-room
# reimplementations produced by the MEGA65 Open Roms project:
#   https://github.com/MEGA65/open-roms
#
# Both `basic_generic.rom` and `kernal_generic.rom` are licensed under the
# GNU General Public License v3.0; the bundled chargen font is the
# project's own Open Roms chargen, also GPL-3. They are blackbox-derived
# from public documentation, not from the original ROMs, so redistribution
# is unencumbered.
#
# These bytes were captured from release "dev.210823.fc.1" of open-roms.
# If you have the original C64 ROMs and want full software compatibility,
# place them in ./roms/{basic.bin, chargen.bin, kernal.bin} and they will
# take precedence over these embedded blobs.
# =============================================================================

_ROM_BLOBS = {
    "basic":
        "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"
    ,
    "kernal":
        "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"
    ,
    "chargen":
        "eNrtVr1qG0sUPkGwSiGkcKstRPQKAoNRsUjdfQ4Rw9wixrhyXIj9wYWTyhinuAMOeo7bSWwhDAK9"
        "goKKrUIkVEQLwud+58ys7RsI3EAgEPJJq9H5mfMzzM43kTk5Gb6KKIxMbIyhkTHypcgMh0MT0fkx"
        "tMfnFA+H58Nh7Meh2E8M7LDqvCgURPSyARz3CHNOMZeGipiO3iSvj46OyJzF8Yn4G0Gk+Vw8EZsq"
        "yzzEjwLYY40bkvH+bggJsV4nbxAPAuaSauEXB42wi3xRVxBR44/uqPtqT5HU1YgIjWpIetFNku4L"
        "qqA60jwqG8P4GAr7qGMU0iuDuOZP1BX1/jIDQhr1g7bbDRuEp4H/mBhxZDRgHIYPwWGg+EkyopoW"
        "ingnZ9JXGPZQAeo2QUPrN0Fb+g+aL00SBFj3USAy1mUk/jHqkZLRu3xl7ItdeiDNG2reJpJ0w6am"
        "lwJOwwYSn2qe0Dky4+d5u58k7T6FHpX+66H62/VoeEC9XEsLYbtV1xZ76yXGiYJ5sjzttZv1Wq3e"
        "bPdOl6LxlpqCohiIHhIcJknSbz/3+wcbhKjeaodhXsRRFBc5/LHzZN2MkX0XeEgfMg+FMONnMul2"
        "5Xnsq9Y/OzwkTgadVr32rOpp7eHS85NuXUUTj/n84ECemocYReb7/W69nKSVHqk6HbeO1AJUdrF2"
        "u7DaGZpG/bTeSulk9avyLj3qHo/OTyrlajWdUvqR3H5/73Ze99SW2+vrsc25yG1mreULa+XLuR2P"
        "RX95A+3NJWfj8eV4nPlxLPZrCzusOi8vBDl/3AI3M8acK8zlsSLj27fp+9vbW7bvsuxa/K0g13wu"
        "nogblWUe4ucl7JnGLdh6fzcUjFjv07eIBwFzWbXwy8ptsUC+fCHIeftpcbH4UONc6trmjEY1JH9e"
        "pOniM1dQHWsela0lfCwXU9RxUfAHi7j2H9SVz/62E0Ya9YN2sSi2jGeL/5iYU241YFYUD8Fh4OxJ"
        "Mua9Fop41++kr6KYoQLUbcut1m/LlfRfbj7atCyx7helyFiXC/HPUI+UjN7lK+NU7NIDa95C826Q"
        "ZFFsNL0UcFVskfhK8xTOUffNl9U0TVdTLjwq/ddD9XfhsfWAutOSForVeqctzlodjAMF0aBzNVtt"
        "dvv9brOaXXVE4y17BecZkD8kuEvTdLr64vcPNgjzbr0qiijM8jwLI/hj58m6WSv7rvSQPmQeCiHC"
        "z2CwWMjz2Nd++u7ujimdLNe7/X3VU8vj4dXn/8BXOxi4t38+33uIUWR6Vqu3OoOk0iPVcunWkeVd"
        "U9nFqteLamdoGvXTeiulk9Wvytvx2Hk8Oj+plKrVdErpR3L7/S2HBlc9VrbI8z9RFPRNn3DgKv9D"
        "xqkLfQC16MEYscjNsO+OL1EHI+dvhG56cg5ToEdxBP2x8Dj13L0AxJjgBoBR3I3GM8pX7gbg4wUi"
        "u+NeiRdxha6bysiuDsf/ROD//qHIcgFw+n7jHDwHXv3N/9/L/7/a/e9b/F+9vwd2buT5Ufw/twdG"
        "np/N/89qAVZ+SN/L/8x5ObVTxoGr/A8Zpy70JdSiB2NkIm+KqTu+RF1eOH8rdDOTc5hLPYpz6G+E"
        "x3nm7gUgxhQ3AIzibjWe1bzuBuDjlSK7416JF3GFrjfKyK4Ox//M4P/pnchyAXD66fYSPAde/c3/"
        "38v/v9r971v8X72/7u0/sD+K/93bP7c/m//v9yVWfsz/l///BXax+GI="
    ,
}
def _get_embedded_rom(name):
    return zlib.decompress(base64.b64decode("".join(_ROM_BLOBS[name].split())))


# =============================================================================
# Entry point
# =============================================================================

def _dump_screen(system):
    """Print screen RAM as ASCII — useful for headless verification."""
    def sc(c):
        c &= 0x7F
        if c == 0:        return '@'
        if 1 <= c <= 26:  return chr(ord('A') + c - 1)
        if c == 27:       return '['
        if c == 29:       return ']'
        if c == 32:       return ' '
        if 33 <= c <= 63: return chr(c)
        return '.'
    print("+" + "-" * 40 + "+")
    for row in range(25):
        line = ''.join(sc(system.mem.ram[0x0400 + row * 40 + col]) for col in range(40))
        print("|" + line + "|")
    print("+" + "-" * 40 + "+")


def _launch_prg(system, prg_path, auto_run=True, boot_cycles=3_500_000):
    """Boot the system to READY., then load a PRG and optionally type RUN."""
    print(f"Booting {boot_cycles:,} cycles to reach READY ...")
    system.run(boot_cycles)
    load_addr, length, is_basic = system.load_prg(prg_path)
    kind = "BASIC" if is_basic else "ML"
    print(f"Loaded {prg_path}: ${load_addr:04X}-${load_addr + length - 1:04X} "
          f"({length} bytes, {kind})")
    if auto_run:
        if is_basic:
            print("Auto-typing RUN...")
            system.type_string("RUN\r")
        else:
            print(f"Auto-typing SYS {load_addr}...")
            system.type_string(f"SYS{load_addr}\r")
    else:
        if is_basic:
            print(f"BASIC program loaded — type RUN at the prompt to start.")
        else:
            print(f"ML program loaded — type SYS {load_addr} at the prompt to start.")


def _launch_d64(system, d64_path, auto_run=True, boot_cycles=3_500_000):
    """Mount a D64, boot to READY, then issue LOAD via the keyboard buffer."""
    d64 = system.mount_d64(d64_path)
    name = d64.disk_name().decode("ascii", "replace")
    print(f"Mounted: {d64_path}  (disk name {name!r})")
    print("Directory:")
    files = list(d64.list_directory())
    for fname, ftype, t, s, size in files:
        tstr = ["DEL", "SEQ", "PRG", "USR", "REL"][ftype & 0x0F]
        print(f"  {fname.decode('ascii','replace'):<16}  {tstr}  "
              f"{size} sectors  (first T{t} S{s})")
    if not files:
        print("(empty disk)")
        return

    # Peek at the first PRG to detect BASIC vs ML
    found = d64.find_file(b"*")
    if not found:
        print("No PRG on this disk — booting without autoload.")
        system.run(boot_cycles)
        return
    track, sector, _ = found
    first = d64.read_sector(track, sector)
    load_addr = first[2] | (first[3] << 8)
    is_basic = (load_addr == 0x0801)
    kind = "BASIC" if is_basic else "ML"
    print(f"First PRG load address ${load_addr:04X} → {kind}")

    print(f"Booting {boot_cycles:,} cycles to reach READY ...")
    system.run(boot_cycles)

    if not auto_run:
        print('Type LOAD"NAME",8 (BASIC) or LOAD"NAME",8,1 (ML) at the prompt.')
        return

    if is_basic:
        # 'LOAD"*",8\\r' is exactly 10 chars and fits in one buffer fill
        print('Auto-typing LOAD"*",8 ⏎ then RUN ⏎ ...')
        system.type_string('LOAD"*",8\r')
        system.run(1_500_000)
        system.type_string("RUN\r")
    else:
        # 'LOAD"*",8,1\\r' is 12 chars — feed in two parts.
        print(f'Auto-typing LOAD"*",8,1 ⏎ then SYS {load_addr} ⏎ ...')
        system.type_string('LOAD"*",8')
        system.run(400_000)
        system.type_string(",1\r")
        system.run(1_500_000)
        system.type_string(f"SYS{load_addr}\r")


def _launch_t64(system, t64_path, auto_run=True, boot_cycles=3_500_000):
    """Mount a T64 tape archive, boot to READY, then LOAD from device 1."""
    tape = system.mount_t64(t64_path)
    name = tape.disk_name().decode("ascii", "replace")
    print(f"Mounted tape: {t64_path}  (name {name!r})")
    files = list(tape.list_directory())
    print("Files:")
    for fname, ftype, _t, _s, size in files:
        print(f"  {fname.decode('ascii','replace'):<16}  PRG  {size} blocks")
    if not files:
        print("(empty tape)")
        return

    found = tape.find_file(b"*")
    data = tape.read_file(found[0], found[1])
    load_addr = data[0] | (data[1] << 8)
    is_basic = (load_addr == 0x0801)
    kind = "BASIC" if is_basic else "ML"
    print(f"First file load address ${load_addr:04X} → {kind}")

    print(f"Booting {boot_cycles:,} cycles to reach READY ...")
    system.run(boot_cycles)

    if not auto_run:
        print('Type LOAD"*",1 (BASIC) or LOAD"*",1,1 (ML) at the prompt.')
        return

    if is_basic:
        print('Auto-typing LOAD"*",1 ⏎ then RUN ⏎ ...')
        system.type_string('LOAD"*",1\r')
        system.run(1_500_000)
        system.type_string("RUN\r")
    else:
        print(f'Auto-typing LOAD"*",1,1 ⏎ then SYS {load_addr} ⏎ ...')
        system.type_string('LOAD"*",1')
        system.run(400_000)
        system.type_string(",1\r")
        system.run(1_500_000)
        system.type_string(f"SYS{load_addr}\r")


def main():
    args = sys.argv[1:]
    print(f"c64emu {__version__}")

    if "--cputest" in args:
        ok = C64Emu().test_cpu(verbose=("-v" in args))
        sys.exit(0 if ok else 1)

    # Scan args for options + an optional .prg path
    prg_file = None
    no_autorun = "--no-run" in args
    scale = 2
    if "--scale" in args:
        i = args.index("--scale")
        scale = int(args[i + 1])
    sid_file = None
    d64_file = None
    t64_file = None
    for a in args:
        if a.lower().endswith(".prg") and os.path.exists(a):
            prg_file = a
            break
        if a.lower().endswith(".sid") and os.path.exists(a):
            sid_file = a
            break
        if a.lower().endswith(".d64") and os.path.exists(a):
            d64_file = a
            break
        if a.lower().endswith(".t64") and os.path.exists(a):
            t64_file = a
            break

    if "--headless" in args:
        i = args.index("--headless")
        n = int(args[i + 1]) if i + 1 < len(args) else 1_500_000
        sysm = System()
        if prg_file:
            _launch_prg(sysm, prg_file, auto_run=not no_autorun)
            # Run extra cycles to let RUN execute and produce output
            print("Running PRG for 1,500,000 extra steps...")
            for _ in range(1_500_000):
                if not sysm.step():
                    break
        elif d64_file:
            _launch_d64(sysm, d64_file, auto_run=not no_autorun)
            print("Running for 1,500,000 extra steps...")
            for _ in range(1_500_000):
                if not sysm.step():
                    break
        elif t64_file:
            _launch_t64(sysm, t64_file, auto_run=not no_autorun)
            print("Running for 1,500,000 extra steps...")
            for _ in range(1_500_000):
                if not sysm.step():
                    break
        else:
            print(f"Booting for {n} steps (headless)...")
            for _ in range(n):
                if not sysm.step():
                    break
        _dump_screen(sysm)
        return

    sysm = System()
    if prg_file:
        _launch_prg(sysm, prg_file, auto_run=not no_autorun)
    elif sid_file:
        info = sysm.load_sid(sid_file)
        print(f"SID: {info['name']!r} by {info['author']!r} ({info['released']!r})")
        print(f"     songs={info['songs']} start={info['start_song']} "
              f"load=${info['load']:04X} init=${info['init']:04X} play=${info['play']:04X}")
    elif d64_file:
        _launch_d64(sysm, d64_file, auto_run=not no_autorun)
    elif t64_file:
        _launch_t64(sysm, t64_file, auto_run=not no_autorun)
    front = PygameFrontend(sysm, scale=scale)
    front.run()


if __name__ == "__main__":
    main()
