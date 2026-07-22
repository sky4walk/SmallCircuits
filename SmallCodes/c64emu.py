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
* `python3 c64emu.py --lorenztest DIR` – run the Wolfgang-Lorenz test suite
* `python3 c64emu.py --victest DIR`    – run the VIC-II screenshot test suite
* `python3 c64emu.py --headless N`     – boot, run N steps, dump screen as ASCII
* `python3 c64emu.py --scale 3`        – set window scale (default 2)
* `python3 c64emu.py game.prg`         – boot, then auto-load (& RUN if BASIC)
* `python3 c64emu.py game.prg --no-run`– load but don't auto-RUN
* `python3 c64emu.py tune.sid`         – boot, load PSID, play 50 Hz
* `python3 c64emu.py game.d64`         – mount disk, auto-load & start
* In the window: F8 = sprite-collision on/off, F10 = sprite/collision dump,
  F11 = warp speed toggle, F12 = soft reset.

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
__version__ = "2026.07.20-input-recorder"


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

    # First visible playfield raster (top of the 25-row text area at Y-scroll 3).
    # Used to snapshot each character row's screen/colour RAM at its own line.
    FIRST_DISPLAY_LINE = 51

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
        # Background/border colours per raster line, so a game that changes
        # them mid-frame (e.g. Exploding Fist recolours $D021 for the sky,
        # ground and status bands via raster splits) renders each band in its
        # own colour instead of one latched value.
        self.line_d020 = bytearray(self.LINES_PER_FRAME)
        self.line_d021 = bytearray(self.LINES_PER_FRAME)
        self.line_d022 = bytearray(self.LINES_PER_FRAME)
        self.line_d023 = bytearray(self.LINES_PER_FRAME)
        # $D01B (sprite/background priority) per raster line. Games raster-split
        # this so a sprite is in front of the backdrop in one screen band and
        # behind the foreground in another (Pitfall: Harry is in front up top,
        # behind the ground below). Evaluated per sprite row at render time.
        self.line_d01b = bytearray(self.LINES_PER_FRAME)
        # Per-raster sprite Y position and data pointer for all 8 sprites,
        # stored flat as [raster*8 + sprite]. A game can reposition sprites
        # mid-frame via raster IRQs (sprite multiplexing) to draw figures taller
        # than 21px or show more than 8 sprites; recording Y+pointer per line
        # lets the renderer redraw each sprite at every position it occupied.
        self.line_spr_y = bytearray(self.LINES_PER_FRAME * 8)
        self.line_spr_ptr = bytearray(self.LINES_PER_FRAME * 8)
        # Sprite X low byte per line, and the $D010 X-MSB byte per line. The game
        # rewrites X together with Y when multiplexing (each mid-frame copy sits
        # at its own horizontal position), so X must be replayed per line too.
        self.line_spr_x = bytearray(self.LINES_PER_FRAME * 8)
        self.line_spr_msb = bytearray(self.LINES_PER_FRAME)
        # VIC bank active when the sprite pointers were fetched on each raster,
        # so sprite DATA is read from the bank live at display time (see
        # read_vic_bytes_bank) even across a mid-frame $DD00 bank switch.
        self.line_spr_bank = bytearray(self.LINES_PER_FRAME)
        # --- Canonical per-line sprite display state ---
        # line_spr_row[r*8+i] is the sprite row (0..20) sprite i DISPLAYS on
        # raster r, or 0xFF when it isn't displaying there. It is produced by a
        # line-level model of the VIC's sprite display sequencer (see tick()):
        # display starts on the line where raster matches the Y register, a row
        # counter walks 0..20, and the Y-expansion flip-flop makes each row
        # repeat when $D017 is set — including mid-sprite toggles. The frame
        # renderer and the $D01E/$D01F collision logic BOTH consume these
        # records, so "where is sprite pixel data" has one source of truth,
        # like row_gfx_mode() is for the background graphics.
        self.line_spr_row = bytearray(b"\xFF" * (self.LINES_PER_FRAME * 8))
        # Remaining per-line sprite attributes so mid-frame register splits
        # (colour / multicolor / expansion / priority changed per zone, as
        # multiplexers do) render and collide with the value active on each
        # line: sprite colours $D027-2E, MC flags $D01C, X-expand $D01D,
        # shared MC colours $D025/26.
        self.line_spr_col = bytearray(self.LINES_PER_FRAME * 8)
        self.line_d01c = bytearray(self.LINES_PER_FRAME)
        self.line_d01d = bytearray(self.LINES_PER_FRAME)
        self.line_d025 = bytearray(self.LINES_PER_FRAME)
        self.line_d026 = bytearray(self.LINES_PER_FRAME)
        # Sequencer state per sprite: displaying?, current row, Y-expand
        # flip-flop; _spr_disp_mask mirrors the displaying set as a bitmask so
        # tick() can skip the per-sprite loop when nothing is active.
        self._spr_disp = [False] * 8
        self._spr_row = [0] * 8
        self._spr_ff = [False] * 8
        self._spr_disp_mask = 0
        # --- Canonical per-line DISPLAY-LOGIC state (badline / idle / border) ---
        # A line-level model of the VIC's display logic: a badline (DEN armed
        # at raster $30, raster in $30..$F7, raster&7 == YSCROLL) starts a text
        # row: the row's screen/colour data is fetched THERE (not on a fixed
        # schedule), RC walks 0..7, and when no badline follows the sequencer
        # drops to IDLE state, displaying the byte at $3FFF. This is what FLD
        # (badline suppression via YSCROLL) and DEN blanking actually do, and
        # renderer + collision both consume these records.
        self.line_idle = bytearray(b"\x01" * self.LINES_PER_FRAME)
        self.line_text_row = bytearray(b"\xFF" * self.LINES_PER_FRAME)
        self.line_rc = bytearray(self.LINES_PER_FRAME)
        self.line_vborder = bytearray(self.LINES_PER_FRAME)
        # Per-row graphics mode/base, recorded at the row's badline and refined
        # mid-row (RC==4) so raster splits keep the old sampling semantics.
        self.row_mode_d011 = bytearray(25)
        self.row_mode_d016 = bytearray(25)
        self.row_mode_d018 = bytearray(25)
        # VIC bank ($DD00) active when each row was fetched. The font base is
        # bank*0x4000 + char_base; games that switch $DD00 mid-frame (e.g. Pole
        # Position II: bank 2 status line over a bank 3 road) need the font
        # read from the row's OWN bank, not the render-time bank.
        self.row_mode_bank = bytearray([0xFF] * 25)   # 0xFF = not yet captured
        self._den_frame = True
        self._vborder = True
        self._display_state = False
        self._rc = 0
        self._disp_row = 0
        self._vcbase_row = 0
        self._bl_estab = 0
        self._bl_cond = False
        self._bl_since = 0
        self._bl_line = -1
        self._bl_fetch_pend = None
        self._bl_rc_pend = False
        self._bl_cond13 = None
        self._bl_cond12 = None
        self._bl_w11 = False
        self._bl_eol_pend = False
        # Per-character-row snapshot of the 40 screen codes and 40 colour-RAM
        # nibbles as they were when the VIC fetched that row (its badline).
        # Reading the whole screen once at frame end tears when a game rewrites
        # screen RAM mid-frame without vblank sync (crack-intro scrollers do
        # exactly this); snapshotting per row makes such scrolls render the way
        # the VIC actually drew them, line by line.
        self.line_screen = bytearray(25 * 40)
        self.line_color  = bytearray(25 * 40)
        self.color_ram   = None            # set by System alongside .mem
        self.mem = None                    # set by System after Memory exists
        self.raster = 0
        self._line_cycles = 0
        self.ba = True             # bus available to CPU (low on badlines)
        self._badline = False
        self.ba_debt = 0        # batch: cycles the CPU owes for badline DMA
        self.raster_compare = 0
        self.irq_status = 0
        self._raster_irq_pending = False
        self._raster_irq_fired_line = -1   # edge guard: fire once per entry
                                           # into the compare line, not while
                                           # raster==compare holds
        self._d021_splits = {}
        self._vc_offset = 0
        self.irq_enable = 0
        # Sprite-sprite ($D01E) and sprite-data ($D01F) collision latches.
        # Bits are set as collisions occur; reading clears the register.
        self.sprite_sprite_coll = 0
        self.sprite_data_coll = 0
        # F8 runtime toggle: when False, _collide_at_raster is skipped so the
        # sprite-collision latches never set. Purely a diagnostic switch to test
        # whether per-raster collision is what a game is reacting to.
        self.collision_enabled = True
        # F10 diagnostic recorders (do not affect emulation). Accumulate the
        # collision bits/rasters of the current frame, snapshotting the last
        # complete frame so an F10 press reports a stable, whole-frame picture.
        self._dbg_dc_frame = 0        # sprite-data ($D01F) bits this frame
        self._dbg_sc_frame = 0        # sprite-sprite ($D01E) bits this frame
        self._dbg_dc_rasters = []     # [(raster, sprite-bits), ...] this frame
        self._dbg_dc_last = 0         # snapshot: last complete frame
        self._dbg_sc_last = 0
        self._dbg_dc_rasters_last = []
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

    VSP_BASE = 15          # cycle whose mid-line badline gives VC offset 0
    VSP_WINDOW_END = 48    # last stamp that still starts this line's fetch

    def _line_display_bookkeeping(self, r, d011, defer_eol=False):
        self.line_idle[r] = 0
        self.line_text_row[r] = self._disp_row
        self.line_rc[r] = self._rc
        if self._rc == 4:
            # Mid-row refinement: raster splits that change mode/bases
            # inside a row keep the old "sampled at row centre"
            # semantics for that row's rendering and collision.
            self.row_mode_d011[self._disp_row] = d011
            self.row_mode_d016[self._disp_row] = self.regs[0x16]
            self.row_mode_d018[self._disp_row] = self.regs[0x18]
            if self.mem is not None:
                self.row_mode_bank[self._disp_row] = self.mem.vic_bank()
        if defer_eol:
            # cycle mode: the RC==7 / advance decision belongs to cycle 58
            # (Bauer), where the LIVE badline condition decides whether the
            # display stays on and RC wraps — see _bl_resolve_eol.
            self._bl_eol_pend = True
            return
        if self._rc == 7:
            self._vcbase_row = self._disp_row + 1
            self._display_state = False
        else:
            self._rc += 1

    def _bl_resolve_eol(self):
        """Cycle 58, Bauer verbatim: if RC==7 the video logic goes idle
        and VCBASE advances; a badline condition present NOW forces the
        display state back on (the next line continues as display, no
        second ghost advance); in display state RC increments (7 wraps
        to 0)."""
        self._bl_eol_pend = False
        if self._rc == 7:
            self._vcbase_row = self._disp_row + 1
            self._display_state = False
        d011 = self.regs[0x11]
        r = self.raster
        cond = (self._den_frame and 0x30 <= r <= 0xF7
                and (r & 7) == (d011 & 7)
                and self._vcbase_row < 25)
        if cond:
            self._display_state = True
            self._disp_row = self._vcbase_row
        if self._display_state:
            self._rc = (self._rc + 1) & 7

    def _bl_resolve_rc(self):
        """Cycle 14: the RC reset happens only if the badline condition
        still holds NOW; then this line's display bookkeeping runs."""
        self._bl_rc_pend = False
        c13 = (self._bl_cond13 if self._bl_cond13 is not None
               else self._bl_cond)
        c12 = self._bl_cond12 if self._bl_cond12 is not None else c13
        if self._bl_w11:
            reset = c13
        else:
            reset = c12 or c13
        if reset:
            self._rc = 0
        if self._display_state:
            self._line_display_bookkeeping(
                self._bl_line, self.regs[0x11],
                defer_eol=getattr(self, "_bl_defer", False))
        else:
            r = self._bl_line
            self.line_idle[r] = 1
            self.line_text_row[r] = 0xFF
            self.line_rc[r] = 0

    def _bl_check(self, C, from_write=False):
        """Commit the badline for the current line if the condition holds
        and a qualifying cycle (>=12) has been reached. Establishes coming
        from mid-line $D011 WRITES only apply to lines that are still idle
        (matching the VIC's observable behaviour and our row bookkeeping);
        the line-start path decides fresh lines without that guard."""
        if self._bl_estab is not None or not self._bl_cond:
            return
        if from_write and not self.line_idle[self._bl_line]:
            return
        # Qualification floor: the condition counts from cycle 0 — the
        # dmadelay references prove a condition true only during the first
        # cycles of the line still commits the badline (ref03 vs ref04).
        T = self._bl_since
        if T > 54 or T > C:
            return
        self._bl_estab = T
        r = self._bl_line
        if T <= 14:
            if T == 14 and getattr(self, "_bl_defer", False):
                # a condition arising only in cycle 14 misses the first
                # c-access of the fetch window (cycle 15): the row fetch
                # starts one character late and the VC deficit of 1 char
                # persists — ref18 vs ref04 measure exactly -8 px.
                self._vc_offset += -1
            d011 = self.regs[0x11]
            self._display_state = True
            if getattr(self, "_bl_defer", False):
                # cycle mode: the RC decision ALWAYS goes through the
                # cond12/cond13 rule — establishes from a cycle-14 write
                # come too late for the reset (the create@14 dmadelay
                # variants); resolve fires on the next tick with the
                # already-frozen snapshots.
                self._bl_rc_pend = True
            else:
                # batch: always immediate (pre-timeline semantics; chunk-
                # boundary jitter must never defer bookkeeping = flicker).
                self._rc = 0
            self._disp_row = row = self._vcbase_row
            self.row_mode_d011[row] = d011
            self.row_mode_d016[row] = self.regs[0x16]
            self.row_mode_d018[row] = self.regs[0x18]
            self.line_idle[r] = 0
            self.line_text_row[r] = row
            self.line_rc[r] = 0
            if not getattr(self, "_bl_defer", False):
                # batch: charge the CPU the badline DMA steal (~40 cycles).
                # Without this the CPU runs ~5% fast and raster-IRQ frame
                # governors (Pitstop II) mis-measure their deadlines.
                self.ba_debt += 40
            # The c-accesses only run if the condition still holds when the
            # fetch window opens (cycle 15). A badline whose condition dies
            # before that keeps the STALE matrix latches — the row repeats
            # old content (dmadelay class B). Decide now if we're already
            # past 15, else defer to the tick.
            if C >= 15 or not getattr(self, "_bl_defer", False):
                self._fetch_row(row)
            else:
                self._bl_fetch_pend = row
        else:
            if getattr(self, "_bl_defer", False):
                self._vc_offset += -(T - self.VSP_BASE)
            else:
                self.ba_debt += max(55 - T, 0)
                # batch scheduler: pre-timeline semantics — ASSIGN the
                # offset (never accumulate; instruction-level write jitter
                # would otherwise make it wander frame to frame = flicker,
                # Pitstop II) and keep the old window cut at cycle 48.
                if T > self.VSP_WINDOW_END:
                    self._bl_estab = None
                    return
                self._vc_offset = -(T - self.VSP_BASE)
            self._trigger_badline_now(r, self.regs[0x11])

    def _trigger_badline_now(self, r, val):
        """Establish a badline for the CURRENT line retroactively (the
        condition was made true by a mid-line YSCROLL/DEN write). Fetches the
        row honouring the persistent VC offset (VSP)."""
        row = self._vcbase_row
        self._display_state = True
        self._disp_row = row
        self._rc = 1                 # this line shows RC 0; tick
        self.line_idle[r] = 0        # already ran, next line is RC 1
        self.line_text_row[r] = row
        self.line_rc[r] = 0
        self.row_mode_d011[row] = val
        self.row_mode_d016[row] = self.regs[0x16]
        self.row_mode_d018[row] = self.regs[0x18]
        self._fetch_row(row)

    def _fetch_row(self, row):
        """Copy a text row's 40 matrix + colour bytes into the canonical row
        snapshot, addressed via VC = row*40 + the persistent VSP offset
        (wrapped inside the 1 KB video matrix, as the 10-bit VC does)."""
        if self.mem is None:
            return
        _bank = self.mem.vic_bank()
        if row < 25:
            self.row_mode_bank[row] = _bank      # font must use THIS bank too
        base = (_bank * 0x4000
                + ((self.regs[0x18] >> 4) & 0x0F) * 0x400)
        vc = (row * 40 + self._vc_offset) % 1024
        if vc + 40 <= 1024:
            self.line_screen[row * 40:row * 40 + 40] = \
                self.mem.ram[base + vc:base + vc + 40]
            if self.color_ram is not None:
                self.line_color[row * 40:row * 40 + 40] = \
                    self.color_ram.ram[vc:vc + 40]
        else:                                   # wrap inside the matrix
            k = 1024 - vc
            self.line_screen[row * 40:row * 40 + k] = \
                self.mem.ram[base + vc:base + 1024]
            self.line_screen[row * 40 + k:row * 40 + 40] = \
                self.mem.ram[base:base + 40 - k]
            if self.color_ram is not None:
                self.line_color[row * 40:row * 40 + k] = \
                    self.color_ram.ram[vc:1024]
                self.line_color[row * 40 + k:row * 40 + 40] = \
                    self.color_ram.ram[0:40 - k]

        # mirror of the VIC's internal 40x12-bit matrix latches: the last
        # row actually c-fetched. A suppressed badline fetch displays THIS.
        self._latch_screen = bytes(self.line_screen[row * 40:row * 40 + 40])
        self._latch_color = bytes(self.line_color[row * 40:row * 40 + 40])

    def write(self, offset, val):
        offset &= 0x3F
        val &= 0xFF
        if (offset in (0x22, 0x23)
                and not getattr(self, "_bl_defer", False)
                and self._line_cycles < 16):
            # Colour-ladder writes land in cycles ~6-16 of their target line
            # (raster busy-wait + 2 STAs); the visible pixels only start at
            # ~cycle 16, so on hardware the WHOLE line shows the new colour.
            # Our snapshot is taken at line start — apply the write
            # retroactively or IRQ jitter wobbles each stripe by one line
            # (Pitstop II horizon).
            if offset == 0x22:
                self.line_d022[self.raster] = val
            else:
                self.line_d023[self.raster] = val
        if offset in (0x18, 0x16) and not getattr(self, "_bl_defer", False):
            # Late split writes (batch mode): the real chip's c/g-accesses
            # for a row run in cycles 15-54, so a $D018/$D016 write landing
            # in cycles 0-14 of the row's badline still applies to THIS
            # row. Our batch line-start fetch has already run by then —
            # refresh the row records and re-fetch so IRQ jitter around the
            # line boundary can't alternate the fetched screen (Pitstop II
            # split flicker: the D018 write wanders r66/c60 <-> r67/c2).
            r = self.raster
            if (self._line_cycles < 15 and not self.line_idle[r]
                    and self.line_rc[r] == 0):
                row = self.line_text_row[r]
                if row < 25:
                    self.regs[offset] = val
                    if offset == 0x18:
                        self.row_mode_d018[row] = val
                        self.line_d018[r] = val
                        self._fetch_row(row)   # also refreshes row_mode_bank
                    else:
                        self.row_mode_d016[row] = val
                        self.line_d016[r] = val
        if offset == self.REG_RASTER_LINE:
            prev_match = (self.raster == self.raster_compare)
            self.raster_compare = (self.raster_compare & 0x100) | val
            if not prev_match and self.raster == self.raster_compare:
                # The raster-IRQ comparison is continuous on the real chip:
                # a WRITE that makes compare == current line transitions the
                # comparison false->true and triggers the IRQ immediately —
                # Pitstop II arms its next ladder rung on the target line's
                # first cycles and relies on exactly this (without it the
                # whole IRQ chain sleeps a frame: the split-view garble).
                # Honour the same per-entry edge guard so a write inside the
                # compare line can't double-fire (Pole Position II timer).
                if self._raster_irq_fired_line != self.raster:
                    self._raster_irq_pending = True
                    self._raster_irq_fired_line = self.raster
        elif offset == self.REG_CTRL1:
            self.regs[offset] = val
            self.raster_compare = (self.raster_compare & 0xFF) | ((val & 0x80) << 1)
            # DEN is armed if set at ANY point during raster line $30 — the
            # per-line state machine samples it at line start, so a write
            # during the line must arm the frame too (dentest den01-49-*).
            if self.raster == 0x30 and (val & 0x10):
                self._den_frame = True
            # The border unit's comparisons are asymmetric in time: the bottom
            # (SET) comparison counts at cycle 63 — so a mid-line RSEL flip
            # away from the compare line cancels the closing (the classic
            # border-opening trick). The top (RESET) comparison fires at the
            # left edge AND at cycle 63 — once a line has opened, a later
            # DEN-off write cannot close it again; conversely a DEN/RSEL write
            # that makes this line the top line opens it retroactively.
            rb = self.raster
            state = bool(self.line_vborder[rb])
            rsel_n = (val >> 3) & 1
            bot = 251 if rsel_n else 247
            top = 51 if rsel_n else 55
            if rb == bot:
                state = True
            elif rb in (247, 251) and state:
                # tick closed this line under the old RSEL; new RSEL says this
                # is not the bottom line -> closing never happens (cycle 63)
                state = bool(self.line_vborder[(rb - 1) % self.LINES_PER_FRAME])
            if rb == top and (val & 0x10):
                state = False
            self._vborder = state
            self.line_vborder[rb] = 1 if state else 0
            # The badline condition is evaluated continuously by the VIC, but
            # the row's DMA fetch window starts around cycle 15 — a YSCROLL
            # write establishing the match EARLY in the line starts a badline
            # there (linecrunch/FLD variants rely on it), while a late write
            # leaves the line as it was. Our tick sampled the condition at
            # line start; honour early mid-line writes retroactively.
            r = self.raster
            cyc = self._line_cycles
            if cyc == 11:
                self._bl_w11 = True
            if getattr(self, "_bl_line", None) == r:
                # timeline update: condition held with the OLD value up to
                # this cycle — commit if it qualified; then track the new
                # condition state from here.
                self._bl_check(min(cyc, 54), from_write=True)
                new_cond = (self._den_frame and 0x30 <= r <= 0xF7
                            and (r & 7) == (val & 7)
                            and self._vcbase_row < 25)
                if new_cond != self._bl_cond:
                    self._bl_cond = new_cond
                    self._bl_since = cyc
                if new_cond and cyc <= 54:
                    self._bl_check(min(max(cyc, 12), 54), from_write=True)
        elif offset == self.REG_IRQ_STATUS:
            self.irq_status &= ~(val & 0x0F)
        elif offset == self.REG_IRQ_ENABLE:
            self.irq_enable = val & 0x0F
        else:
            self.regs[offset] = val
            # The VIC's sprite Y-compare runs continuously during the line, not
            # once at line start like our per-line sequencer step in tick().
            # Multiplexers routinely write the next segment's Y (or enable the
            # sprite) DURING the very line it should trigger on — Pitfall
            # builds its vine and crocodiles from such back-to-back segments.
            # So: a write that makes an enabled, idle sprite's Y match the
            # current raster starts its display right here, mid-line.
            if offset <= 0x0F and (offset & 1):
                i = offset >> 1
                if (not self._spr_disp[i] and (self.regs[0x15] >> i) & 1
                        and val == (self.raster & 0xFF)):
                    self._start_sprite_display_now(i)
            elif offset == 0x15 and val:
                r8 = self.raster & 0xFF
                for i in range(8):
                    if ((val >> i) & 1 and not self._spr_disp[i]
                            and self.regs[i * 2 + 1] == r8):
                        self._start_sprite_display_now(i)
            elif offset == 0x21:
                # Mid-line background-colour split: record the intra-line
                # cycle so the renderer can recolour flat background pixels in
                # horizontal segments (per-cycle $D021 raster bars — the
                # spritesplit tests paint one through the opened border).
                segs = self._d021_splits.get(self.raster)
                cur = (segs[-1][1] if segs
                       else self.line_d021[self.raster] & 0x0F)
                if (val & 0x0F) != cur:
                    if segs is None:
                        segs = self._d021_splits[self.raster] = []
                    segs.append((self._line_cycles, val & 0x0F))

    def _start_sprite_display_now(self, i):
        """Arm sprite i's display from a mid-line Y-compare hit (Y or $D015
        written during the very line it matches). The VIC fetches the first
        sprite data at the end of this line, so display begins on the NEXT
        line — the sequencer in tick() records row 0 from there."""
        self._spr_disp[i] = True
        self._spr_disp_mask |= (1 << i)
        self._spr_row[i] = 0
        self._spr_ff[i] = False

    def tick(self, cycles):
        self._line_cycles += cycles
        if self._bl_estab is None and self._bl_cond:
            self._bl_check(self._line_cycles if self._line_cycles < 54 else 54)
        if self._bl_cond12 is None and self._line_cycles >= 12:
            self._bl_cond12 = self._bl_cond
        if self._bl_cond13 is None and self._line_cycles >= 13:
            # RC-reset decision (empirically pinned by the dmadelay
            # boundary pairs): the condition counts if it was true at ANY
            # point during cycle 12 — i.e. at the start of 12 OR the start
            # of 13. Exception: a $D011 write in cycle 11 (the RMW dummy
            # write pattern) makes only the post-cycle-12 state count.
            self._bl_cond13 = self._bl_cond
        if self._bl_rc_pend and self._line_cycles >= 14:
            self._bl_resolve_rc()
        if self._bl_eol_pend and self._line_cycles >= 58:
            self._bl_resolve_eol()
        if self._bl_fetch_pend is not None and self._line_cycles >= 15:
            row = self._bl_fetch_pend
            if self._bl_cond:
                self._fetch_row(row)
            elif getattr(self, "_latch_screen", None) is not None:
                self.line_screen[row * 40:row * 40 + 40] = self._latch_screen
                self.line_color[row * 40:row * 40 + 40] = self._latch_color
            self._bl_fetch_pend = None
        if self._raster_irq_pending and self._line_cycles >= 2:
            self._raster_irq_pending = False
            self.irq_status |= 0x01
        while self._line_cycles >= self.CYCLES_PER_LINE:
            self._line_cycles -= self.CYCLES_PER_LINE
            self.raster = (self.raster + 1) % self.LINES_PER_FRAME
            if self.raster == 0:
                # New frame: freeze this frame's collision recording for F10.
                self._dbg_dc_last = self._dbg_dc_frame
                self._dbg_sc_last = self._dbg_sc_frame
                self._dbg_dc_rasters_last = self._dbg_dc_rasters
                self._dbg_dc_frame = 0
                self._dbg_sc_frame = 0
                self._dbg_dc_rasters = []
                self._d021_splits = {}
            self.line_d018[self.raster] = self.regs[0x18]
            self.line_d011[self.raster] = self.regs[0x11]
            self.line_d016[self.raster] = self.regs[0x16]
            self.line_d020[self.raster] = self.regs[0x20]
            self.line_d021[self.raster] = self.regs[0x21]
            self.line_d022[self.raster] = self.regs[0x22]
            self.line_d023[self.raster] = self.regs[0x23]
            self.line_d01b[self.raster] = self.regs[0x1b]
            # --- Display-logic state machine (badline / idle / vborder) ---
            # Hardware rules at line granularity: DEN sampled at raster $30
            # arms the frame; a badline (raster $30..$F7, raster&7 == YSCROLL)
            # fetches a text row and enters display state with RC=0; RC walks
            # to 7, then the sequencer goes idle until the next badline. The
            # vertical border flip-flop opens at line 51/55 (RSEL) when DEN is
            # set and closes at 251/247. FLD and DEN blanking fall out of
            # these rules; renderer and collision consume the records.
            r = self.raster
            d011 = self.regs[0x11]
            if r == 0:
                self._vcbase_row = 0
                self._vc_offset = 0
            if r == 0x30:
                self._den_frame = bool(d011 & 0x10)
            rsel = (d011 >> 3) & 1
            if r == (251 if rsel else 247):
                self._vborder = True
            elif r == (51 if rsel else 55) and (d011 & 0x10):
                self._vborder = False
            self.line_vborder[r] = 1 if self._vborder else 0
            # Badline condition timeline: the VIC evaluates the condition
            # per cycle; it qualifies from cycle 12 and latches. We commit at
            # the earliest qualifying cycle T (via _bl_check), so writes that
            # kill the condition before cycle 12 correctly PREVENT the
            # badline, and writes creating it mid-fetch give the DMA-delay
            # offset — both probed cycle-exactly by the dmadelay tests.
            self._bl_estab = None
            self._bl_cond = (self._den_frame and 0x30 <= r <= 0xF7
                             and (r & 7) == (d011 & 7)
                             and self._vcbase_row < 25)
            self._bl_since = 0
            self._bl_line = r
            self._bl_fetch_pend = None
            self._bl_rc_pend = False
            self._bl_cond13 = None
            self._bl_cond12 = None
            self._bl_w11 = False
            self._bl_eol_pend = False
            # commit at line start when the condition holds (cycle-0
            # qualification); mid-line establishes come via tick/write.
            self._bl_check(self._line_cycles)
            if self._bl_rc_pend:
                # RC reset (and with it this line's display bookkeeping)
                # depends on the badline condition AT CYCLE 14 — deferred
                # to _bl_resolve_rc. A condition that dies before cycle 14
                # leaves RC untouched: with RC=7 the line still advances
                # VCBASE at its end, shifting every following row (the
                # dmadelay class-B band shift).
                pass
            elif self._display_state:
                self._line_display_bookkeeping(
                    r, d011, defer_eol=getattr(self, "_bl_defer", False))
            else:
                self.line_idle[r] = 1
                self.line_text_row[r] = 0xFF
                self.line_rc[r] = 0
            mem = self.mem
            if mem is not None:
                ras8 = self.raster * 8
                regs = self.regs
                self.line_spr_y[ras8:ras8 + 8] = regs[1:16:2]
                self.line_spr_x[ras8:ras8 + 8] = regs[0:16:2]
                self.line_spr_msb[self.raster] = regs[0x10]
                self.line_spr_col[ras8:ras8 + 8] = regs[0x27:0x2F]
                self.line_d01c[self.raster] = regs[0x1C]
                self.line_d01d[self.raster] = regs[0x1D]
                self.line_d025[self.raster] = regs[0x25]
                self.line_d026[self.raster] = regs[0x26]
                _sbank = mem.vic_bank()
                self.line_spr_bank[self.raster] = _sbank
                pbase = (_sbank * 0x4000
                         + ((regs[0x18] >> 4) & 0x0F) * 0x400 + 0x3F8)
                self.line_spr_ptr[ras8:ras8 + 8] = mem.ram[pbase:pbase + 8]
                # --- Sprite display sequencer (line-level VIC model) ---
                # A sprite starts displaying on the line where the raster's low
                # byte matches its Y register (if enabled); a row counter then
                # walks 0..20. With Y-expansion the flip-flop makes every row
                # display on two lines; clearing $D017 mid-sprite resumes
                # single-line stepping from the current row, setting it starts
                # doubling — matching the observable line-level behaviour that
                # the spritesplit tests exercise and multiplexers rely on.
                en = regs[0x15]
                if en or self._spr_disp_mask:
                    r8 = self.raster & 0xFF
                    disp = self._spr_disp
                    srow = self._spr_row
                    sff = self._spr_ff
                    d017 = regs[0x17]
                    _spr_dma_n = 0
                    for i in range(8):
                        if not disp[i]:
                            if (en >> i) & 1 and regs[i * 2 + 1] == r8:
                                # Y match: the VIC fetches the sprite's first
                                # data at the END of this line; display begins
                                # on the NEXT line (sprite Y=50 tops out level
                                # with text row 0 at raster 51).
                                disp[i] = True
                                srow[i] = 0
                                sff[i] = False
                                self._spr_disp_mask |= (1 << i)
                            self.line_spr_row[ras8 + i] = 0xFF
                            continue
                        self.line_spr_row[ras8 + i] = srow[i]
                        _spr_dma_n += 1
                        if (d017 >> i) & 1:
                            if sff[i]:
                                srow[i] += 1
                            sff[i] = not sff[i]
                        else:
                            srow[i] += 1
                            sff[i] = False
                        if srow[i] > 20:
                            disp[i] = False
                            self._spr_disp_mask &= ~(1 << i)
                            # The DMA-off decision and the Y compare share the
                            # same cycle window: a sprite whose Y matches the
                            # line its display ENDS on re-triggers immediately
                            # (back-to-back multiplex segments — Pitfall's
                            # vine and crocodiles chain exactly like this).
                            if (en >> i) & 1 and regs[i * 2 + 1] == r8:
                                disp[i] = True
                                srow[i] = 0
                                sff[i] = False
                                self._spr_disp_mask |= (1 << i)
                    if _spr_dma_n and not getattr(self, "_bl_defer", False):
                        # batch: sprite DMA steals ~2 cycles per active
                        # sprite per line plus ~3 cycles BA lead — the
                        # second big timing term after badlines. Without it
                        # the CPU still runs fast and frame governors
                        # (Pitstop II) drift against their real deadlines.
                        self.ba_debt += 2 * _spr_dma_n + 3
                else:
                    self.line_spr_row[ras8:ras8 + 8] = b"\xFF" * 8
            if self.raster == self.raster_compare:
                # Don't assert immediately: on hardware the raster IRQ is
                # raised a cycle into the line and the CPU only recognises an
                # interrupt asserted at least two cycles before the end of the
                # current instruction — a net ~2-3 cycle latency our
                # line-boundary tick otherwise lacks. Raster-IRQ stabilizers
                # (double-IRQ + `inc $d012`) budget exactly for this margin:
                # without it, the re-read of $D012 lands one line early and
                # the routine's anchor drifts one line per frame (dentest).
                # Edge guard: the compare raises the IRQ ONCE per entry into
                # the line. A handler that dwells in the compare line (Pole
                # Position II's banner IRQ at raster 254) must not re-trigger
                # — otherwise the frame-timer at $7C09 decrements twice and
                # the whole pre-race animation runs at double speed.
                if self._raster_irq_fired_line != self.raster:
                    self._raster_irq_pending = True
                    self._raster_irq_fired_line = self.raster
            else:
                if self._raster_irq_fired_line == self.raster_compare:
                    # left the compare line: re-arm for its next entry
                    self._raster_irq_fired_line = -1
            if self.raster == self.SAMPLE_LINE:
                # Latch the registers active during the visible playfield so the
                # per-frame renderer is immune to mid-frame raster splits.
                self.display_regs[:] = self.regs
            if (self.mem is not None and self.collision_enabled
                    and (self.regs[0x15] or self._spr_disp_mask)):
                # Accumulate sprite collisions on this raster line as the beam
                # draws it, so $D01E/$D01F read mid-frame reflect the collisions
                # up to the current line (games read at several rasters to tell
                # which band a collision came from).
                self._collide_at_raster(self.raster)

    @staticmethod
    def _row_bits(d0, d1, d2, mc, xex):
        """Bitmask for one sprite row: bit `c` (LSB) set when local column `c`
        is non-transparent. Handles multicolor (2-wide) and X-expand. In the
        sprite's own space; caller shifts by X."""
        local = 0
        if mc:
            for bi, dv in enumerate((d0, d1, d2)):
                for p in range(4):
                    if (dv >> (6 - 2 * p)) & 3:
                        local |= (0b11 << (bi * 8 + p * 2))
        else:
            for bi, dv in enumerate((d0, d1, d2)):
                for bit in range(8):
                    if (dv >> (7 - bit)) & 1:
                        local |= 1 << (bi * 8 + bit)
        if xex:
            exp = 0
            for c in range(24):
                if (local >> c) & 1:
                    exp |= (0b11 << (2 * c))
            local = exp
        return local

    def _sprite_colbits_at(self, i, r):
        """Column bitmask (bit == VIC X) of sprite i's non-transparent pixels on
        raster line r, or 0 if the sprite does not display on r.

        All state comes from the canonical per-line recordings written by the
        sprite display sequencer in tick() — the same records the frame
        renderer draws from — so collision and rendering can never disagree
        about where a sprite's pixels are, which attributes were active on the
        line, or which row of the sprite the beam was showing."""
        ras8 = r * 8
        row = self.line_spr_row[ras8 + i]
        if row == 0xFF:
            return 0
        mem = self.mem
        da = self.line_spr_ptr[ras8 + i] * 64 + row * 3
        local = self._row_bits(mem.read_vic(da), mem.read_vic(da + 1),
                               mem.read_vic(da + 2),
                               (self.line_d01c[r] >> i) & 1,
                               (self.line_d01d[r] >> i) & 1)
        if not local:
            return 0
        x = self.line_spr_x[ras8 + i] | (((self.line_spr_msb[r] >> i) & 1) << 8)
        return local << x

    def row_gfx_mode(self, row):
        """CANONICAL per-character-row graphics mode decision.

        Returns (bmm, mcm, d018) for text row `row` (0..24) as recorded by the
        display-logic state machine: captured at the row's badline and refined
        mid-row (RC==4), so it reflects the registers active when the row was
        actually fetched/displayed — including FLD-displaced rows. This is the
        single source of truth for "what mode is this row in / which bases
        does it use": the frame renderer, the sprite-priority foreground mask
        and the $D01F sprite-data collision all derive from here."""
        return ((self.row_mode_d011[row] >> 5) & 1,
                (self.row_mode_d016[row] >> 4) & 1,
                self.row_mode_d018[row])

    def _foreground_bits_at(self, r, col0=0, col1=40):
        """Foreground (non-background) column bitmask (bit == VIC X) of the
        displayed graphics on raster line r, restricted to character columns
        [col0, col1) for speed. Handles character modes (hi-res + per-cell
        multicolor) AND bitmap mode (hi-res + multicolor); bit c set == VIC
        X-coordinate c is a foreground pixel.

        Mode/base decisions come from row_gfx_mode() — the same canonical
        per-row source the frame renderer uses — so collision, priority and
        rendering can never disagree about what a row contains."""
        sy = r - 51
        if sy < 0 or sy >= 200:
            return 0
        mem = self.mem
        if self.line_idle[r]:
            # Idle state: the sequencer displays the byte at $3FFF ($39FF with
            # ECM) across the whole line, foreground colour black. Set bits
            # ARE foreground graphics and do collide with sprites.
            byte = mem.read_vic(0x39FF if (self.line_d011[r] & 0x40)
                                else 0x3FFF)
            if not byte:
                return 0
            bits = 0
            for col in range(col0, col1):
                vx0 = 24 + col * 8
                for bx in range(8):
                    if (byte >> (7 - bx)) & 1:
                        bits |= (1 << (vx0 + bx))
            return bits
        char_row = self.line_text_row[r]
        if char_row >= 25:
            return 0
        cy = self.line_rc[r]
        bmm, mcm, d018 = self.row_gfx_mode(char_row)
        if bmm:
            # Bitmap mode. Bit3 of $D018 picks the 8 KB bitmap base in the VIC
            # bank; each 8x8 cell is 8 bytes, 40 cells per row (stride 320).
            # Hi-res: a set bit is foreground. Multicolor: a 2-bit pixel is
            # foreground when its high bit is set (values 10/11), and each such
            # pixel is two VIC-X wide.
            bmbase = ((d018 >> 3) & 1) * 0x2000
            row_off = bmbase + char_row * 320 + cy
            bits = 0
            for col in range(col0, col1):
                byte = mem.read_vic(row_off + col * 8)
                if not byte:
                    continue
                vx0 = 24 + col * 8
                if mcm:
                    for p in range(4):
                        if ((byte >> (6 - 2 * p)) & 3) >= 2:
                            bits |= (0b11 << (vx0 + p * 2))
                else:
                    for bx in range(8):
                        if (byte >> (7 - bx)) & 1:
                            bits |= (1 << (vx0 + bx))
            return bits
        # --- character modes ---
        ls = self.line_screen
        lc = self.line_color
        if ls is None or lc is None:
            return 0
        base = char_row * 40
        char_base = ((d018 >> 1) & 0x07) * 0x0800
        bits = 0
        for col in range(col0, col1):
            byte = mem.read_vic(char_base + ls[base + col] * 8 + cy)
            if not byte:
                continue
            vx0 = 24 + col * 8
            if mcm and (lc[base + col] & 0x08):
                for p in range(4):
                    if ((byte >> (6 - 2 * p)) & 3) >= 2:
                        bits |= (0b11 << (vx0 + p * 2))
            else:
                for bx in range(8):
                    if (byte >> (7 - bx)) & 1:
                        bits |= (1 << (vx0 + bx))
        return bits

    def _collide_at_raster(self, r):
        """Accumulate sprite-sprite ($D01E) and sprite-data ($D01F) collisions
        occurring on raster line r into their latches, as real hardware does
        while the beam draws. Called once per raster so a game that reads the
        latches mid-frame (clearing them) sees the collisions of each screen band
        separately — the technique many titles use to localise collisions."""
        lrow = self.line_spr_row
        ras8 = r * 8
        active = []
        allbits = 0
        for i in range(8):
            if lrow[ras8 + i] == 0xFF:
                continue
            cb = self._sprite_colbits_at(i, r)
            if cb:
                active.append((i, cb))
                allbits |= cb
        if not active:
            return
        # sprite-sprite: any pair sharing a column on this line
        if len(active) >= 2:
            ss = 0
            for a in range(len(active)):
                ia, ba = active[a]
                for b in range(a + 1, len(active)):
                    ib, bb = active[b]
                    if ba & bb:
                        ss |= (1 << ia) | (1 << ib)
            if ss:
                old = self.sprite_sprite_coll
                self.sprite_sprite_coll |= ss
                self._dbg_sc_frame |= ss
                if old == 0:
                    self.irq_status |= 0x04
        # sprite-data: sprite pixels over foreground graphics on this line.
        # Only decode the character columns the sprites actually span.
        lo = (allbits & -allbits).bit_length() - 1
        hi = allbits.bit_length() - 1
        col0 = (lo - 24) >> 3
        col1 = ((hi - 24) >> 3) + 1
        if col0 < 0:
            col0 = 0
        if col1 > 40:
            col1 = 40
        if col0 >= col1:
            return
        fg = self._foreground_bits_at(r, col0, col1)
        if fg:
            sd = 0
            for i, cb in active:
                if cb & fg:
                    sd |= (1 << i)
            if sd:
                old = self.sprite_data_coll
                self.sprite_data_coll |= sd
                self._dbg_dc_frame |= sd
                if len(self._dbg_dc_rasters) < 96:
                    self._dbg_dc_rasters.append((r, sd))
                if old == 0:
                    self.irq_status |= 0x02

    def clock(self):
        # One PHI2 tick for cycle-accurate mode. Reuses tick() for the raster
        # advance + per-line recording + raster-IRQ, then computes BA. A line is
        # a "badline" when the beam is in the display window and its low 3 raster
        # bits match Y-scroll with the display enabled; the VIC then holds BA low
        # across the character-fetch window (~cycles 12..54), stalling CPU reads.
        self.tick(1)
        cyc = self._line_cycles
        self._badline = (0x30 <= self.raster <= 0xF7
                         and (self.raster & 7) == (self.regs[0x11] & 7)
                         and (self.regs[0x11] & 0x10) != 0)
        self.ba = not (self._badline and 12 <= cyc <= 54)


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
        # Hardware envelope model: 8-bit counter, 15-bit LFSR-style rate
        # counter with EXACT-match semantics (the famous ADSR delay bug
        # emerges from this naturally), exponential-divider for decay and
        # release. env_state: 1=attack, 2=decay/sustain, 0=release.
        self.env = 0             # 8-bit envelope counter
        self.env_state = 0
        self.rate_cnt = 0        # 15-bit rate counter (0..0x7FFF)
        self.exp_cnt = 0         # exponential divider counter
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
                self.env_state = 1    # attack triggered (env laeuft weiter)
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
    # Envelope rate-counter periods (in CPU cycles) per ADSR nibble — the
    # 15-bit rate counter must hit these values EXACTLY; a just-missed match
    # forces a full 32768-cycle wrap (~33 ms): the ADSR delay bug that
    # hard-restart players deliberately manage.
    RATE_PERIODS = (9, 32, 63, 95, 149, 220, 267, 313,
                    392, 977, 1954, 3126, 3907, 11720, 19532, 31251)

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
        # --- Sample-accurate write timing ---
        # Register writes are queued with their CPU cycle and replayed in
        # segments by generate_samples(). _cpu is wired by System.
        self._cpu = None
        self._queue = []
        self._gen_t = None              # CPU cycle count at last generate
        # Output DC blocker (the real C64's audio out is AC-coupled). Needed
        # because the volume DAC carries a DC offset — the $D418 digi trick —
        # which must move the output momentarily but not sit on it.
        self._dcb_x = 0.0
        self._dcb_y = 0.0
        # SID model: "6581" (classic, default) or "8580". Selects the cutoff
        # curve, resonance range, filter saturation and volume-DAC DC level.
        self.model = "6581"
        self._fc_table = None            # built lazily per model
        self._digi_dc = 0.9

    def set_model(self, model):
        model = str(model)
        if "8580" in model:
            self.model = "8580"
            self._digi_dc = 0.15         # 8580: kaum Volume-DC -> leise Digis
        else:
            self.model = "6581"
            self._digi_dc = 0.9
        self._fc_table = None
        print(f"SID-Modell: {self.model}")

    # 6581 cutoff anchors (register -> Hz): the famous S-curve — the bottom
    # third barely moves off ~220 Hz, the musically usable action sits in
    # the upper-middle register range, the top saturates around 12 kHz.
    _FC_6581 = ((0, 220), (384, 240), (640, 300), (768, 380), (896, 600),
                (1024, 1100), (1152, 2100), (1280, 3500), (1408, 5300),
                (1536, 7000), (1664, 8800), (1792, 10300), (1920, 11400),
                (2047, 12000))

    def _build_fc_table(self, np):
        if self.model == "8580":
            # essentially linear: ~30 Hz .. ~12.2 kHz
            self._fc_table = (30.0 + np.arange(2048) * (12200.0 - 30.0) / 2047.0
                              ).astype(np.float32)
        else:
            xs = np.array([p[0] for p in self._FC_6581], dtype=np.float64)
            ys = np.array([p[1] for p in self._FC_6581], dtype=np.float64)
            self._fc_table = np.interp(np.arange(2048), xs, ys
                                       ).astype(np.float32)

    def read(self, offset):
        offset &= 0x1F
        if offset == 0x1B:                # OSC3 readout
            return (int(self.voices[2].phase) >> 16) & 0xFF
        if offset == 0x1C:                # ENV3 readout
            return self.voices[2].env & 0xFF
        return 0                          # writeable regs read as 0

    def write(self, offset, val):
        """CPU write to a SID register. The raw register value is visible to
        reads immediately, but the AUDIBLE effect is queued with the current
        CPU cycle and applied sample-accurately during generate_samples() —
        the renderer replays the queue in segments, so mid-frame gate flips,
        multispeed player calls and $D418 volume digis land at the right
        sample instead of being quantised to 20 ms frame boundaries."""
        offset &= 0x1F
        val &= 0xFF
        self.regs[offset] = val
        t = self._cpu.cycles if self._cpu is not None else None
        self._queue.append((t, offset, val))
        if len(self._queue) > 20000:
            # No consumer (audio disabled / headless): keep state correct and
            # the queue bounded by applying eagerly.
            for _, o, v in self._queue:
                self._apply_write(o, v)
            self._queue.clear()

    def _apply_write(self, offset, val):
        """Apply a register write's audible effect to the synthesis state.
        Called by the renderer at the write's sample position."""
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
        """Render one frame of audio, replaying the timestamped register-write
        queue: audio is generated in segments between writes, and each write's
        audible effect lands at its true sample position. This is what makes
        multispeed players tight and $D418 volume digis audible at all."""
        q = self._queue
        self._queue = []
        t1 = self._cpu.cycles if self._cpu is not None else None
        t0 = self._gen_t
        self._gen_t = t1
        out = np.empty(n_samples, dtype=np.float32)
        if (t1 is None or t0 is None or t1 <= t0
                or not q or q[0][0] is None):
            for _, off, val in q:
                self._apply_write(off, val)
            out[:] = self._render_chunk(n_samples, np)
        else:
            span = t1 - t0
            pos = 0
            MIN_CHUNK = 4          # >= 11 kHz effective update rate is plenty
            for (t, off, val) in q:
                sp = int((t - t0) * n_samples / span) if t is not None else pos
                sp = min(max(sp, pos), n_samples)
                if sp - pos >= MIN_CHUNK:
                    out[pos:sp] = self._render_chunk(sp - pos, np)
                    pos = sp
                self._apply_write(off, val)
            if pos < n_samples:
                out[pos:] = self._render_chunk(n_samples - pos, np)
        # AC coupling: one-pole DC blocker so the volume DAC's DC offset (and
        # the 12-bit waveforms' baseline) produce transients, not a bias.
        # y[n] = x[n] - x[n-1] + R*y[n-1], vectorised via the closed form
        # y[n] = k[n] * (R*y_prev + cumsum(d/k)[n]) with k[n] = R^n.
        R = 0.9985
        d = np.empty(n_samples, dtype=np.float64)
        d[0] = out[0] - self._dcb_x
        if n_samples > 1:
            d[1:] = np.diff(out.astype(np.float64))
        k = R ** np.arange(n_samples, dtype=np.float64)
        y = k * (R * self._dcb_y + np.cumsum(d / k))
        self._dcb_x = float(out[-1])
        self._dcb_y = float(y[-1])
        return y.astype(np.float32)

    def _render_chunk(self, n_samples, np):
        cycles_per_sample = self.CPU_CLOCK / self.SAMPLE_RATE
        # --- Phase 1: all three oscillator accumulators ---------------------
        # Computed up front (before any waveform) because voices are coupled:
        # hard sync resets a voice's accumulator whenever its neighbour's
        # accumulator wraps, and ring modulation XORs the neighbour's MSB into
        # the triangle. Source voice for voice i is voice (i+2) % 3
        # (0<-2, 1<-0, 2<-1), as on the real chip.
        idx = np.arange(1, n_samples + 1, dtype=np.float64)
        steps = [v.freq * cycles_per_sample for v in self.voices]
        raws = [v.phase + idx * steps[i] for i, v in enumerate(self.voices)]
        accs = [None] * 3
        for i, v in enumerate(self.voices):
            if v.control & 0x08:                       # TEST: oscillator held
                accs[i] = np.zeros(n_samples, dtype=np.int64)
                v.phase = 0.0
                continue
            raw = raws[i]
            if v.control & 0x02 and steps[(i + 2) % 3] > 0:
                # Hard sync: reset at every wrap of the (unsynced) source ramp.
                src = self.voices[(i + 2) % 3]
                src_hi = np.floor(
                    np.concatenate(([src.phase], raws[(i + 2) % 3]))
                    / (1 << 24))
                wraps = np.flatnonzero(src_hi[1:] > src_hi[:-1])
                if len(wraps):
                    tmp = np.zeros(n_samples, dtype=np.float64)
                    tmp[wraps] = raw[wraps]
                    raw = raw - np.maximum.accumulate(tmp)
            ph = np.mod(raw, float(1 << 24))
            accs[i] = ph.astype(np.int64)
            v.phase = float(ph[-1])

        # --- Phase 2: 12-bit DAC waveforms, combined by AND -----------------
        v_out = [self._gen_voice(i, accs, n_samples, np, steps[i])
                 for i in range(3)]

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
        # The volume DAC carries a DC offset: changing $D418 moves the output
        # baseline even with all voices silent — the mechanism 4-bit sample
        # playback ("volume digis") is built on. The DC itself is removed by
        # the output AC coupling; only the CHANGES remain audible.
        out = direct + filtered + np.float32(self._digi_dc)
        out *= self.master_vol / 15.0 / 3.0
        return out

    def _gen_voice(self, i, accs, n_samples, np, phase_step):
        """One voice's (waveform * envelope), from the precomputed accumulator.

        Waveforms are generated as 12-bit DAC values (0..$FFF) like the chip's
        waveform selector outputs, and SELECTING SEVERAL AT ONCE combines them
        with a bitwise AND — the classic approximation of the analog bus fight
        on the real DAC. This is what makes $51 (pulse+triangle) sound thin
        and hollow instead of like a mixed chord (Giana 2 plays almost
        entirely on $50/$51). Ring modulation (bit 2) XORs the sync source's
        accumulator MSB into the triangle's mirror decision, turning the
        triangle into sum/difference metallic tones."""
        v = self.voices[i]
        acc = accs[i]
        ctrl = v.control
        wave = None
        if ctrl & 0x10:                              # TRIANGLE (with ring mod)
            eff = acc
            if ctrl & 0x04:
                eff = acc ^ accs[(i + 2) % 3]
            mirrored = np.where(eff & 0x800000, ~acc & 0xFFFFFF, acc)
            tri = (mirrored >> 11) & 0xFFF
            wave = tri
        if ctrl & 0x20:                              # SAWTOOTH
            saw = acc >> 12
            wave = saw if wave is None else (wave & saw)
        if ctrl & 0x40:                              # PULSE
            if ctrl & 0x08:                          # TEST forces pulse high
                pulse = np.full(n_samples, 0xFFF, dtype=np.int64)
            else:
                pulse = np.where((acc >> 12) >= v.pulse_width, 0xFFF, 0)
            wave = pulse if wave is None else (wave & pulse)
        if ctrl & 0x80:                              # NOISE
            noise = self._gen_noise(v, n_samples, np, phase_step)
            wave = noise if wave is None else (wave & noise)
        if wave is None:                             # no waveform selected
            return np.zeros(n_samples, dtype=np.float32)

        env = self._envelope_chunk(v, n_samples, np)
        return ((wave.astype(np.float32) / 2047.5) - 1.0) * env

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
        out = np.empty(n_samples, dtype=np.int64)
        lfsr = v.noise_lfsr
        acc = v.noise_acc
        cur = int(v.noise_out)
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
                # 8-bit output tapped from LFSR bits 22,20,16,13,11,7,4,2,
                # presented as the top bits of the 12-bit waveform value.
                b = ((((lfsr >> 22) & 1) << 7) | (((lfsr >> 20) & 1) << 6) |
                     (((lfsr >> 16) & 1) << 5) | (((lfsr >> 13) & 1) << 4) |
                     (((lfsr >> 11) & 1) << 3) | (((lfsr >>  7) & 1) << 2) |
                     (((lfsr >>  4) & 1) << 1) |  ((lfsr >>  2) & 1))
                cur = b << 4
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

        # Cutoff via the per-model curve table: 6581 = measured-shape S-curve
        # (flat bottom, steep middle, saturating top), 8580 = linear.
        if self._fc_table is None:
            self._build_fc_table(np)
        fc_hz = float(self._fc_table[self.filter_cutoff & 0x7FF])
        # SVF coefficient (Chamberlin form). The two-integrator loop is only
        # stable while fc stays below ~fs/6, i.e. f <= 1.0 — beyond that the
        # state diverges to +/-inf and then NaN, which silences ALL later audio
        # (a wide-open low-pass, as e.g. Lazy Jones uses, hit exactly this).
        # Clamp to 1.0; the low-pass pass-band gain at f<=1 is still ~1.0 so
        # nothing gets quieter. Damping floored at 0.1 keeps high-resonance
        # tunes bounded too (poles stay inside the unit circle for all f<=1).
        # f capped at 0.9 (~7.5 kHz at 44.1 kHz) and damping floored by an
        # f-dependent bound: the Chamberlin loop is only stable when damping
        # stays above ~f²/2; without this, high cutoff + high resonance
        # diverges. The real 6581 is mushy up top anyway.
        f = min(2.0 * np.sin(np.pi * fc_hz / self.SAMPLE_RATE), 0.9)
        # Resonance per model: the 6581's Q is famously weak (~0.7..1.7),
        # the 8580 resonates properly (~0.7..2.6) — SID resonance colours,
        # it never screams like a synth's Q=10.
        res = self.filter_resonance / 15.0
        if self.model == "8580":
            damping = max(1.414 - res * 1.03, 0.38, 0.62 * f)
        else:
            damping = max(1.414 - res * 0.83, 0.59, 0.62 * f)

        low  = self._flt_low
        band = self._flt_band
        # Recover if a previous frame left the state non-finite (e.g. an older
        # build blew up): a single NaN would otherwise poison audio forever.
        if not (np.isfinite(low) and np.isfinite(band)):
            low = band = 0.0
        # Pre-allocate only outputs we need
        want_lp = mode & 0x01
        want_bp = mode & 0x02
        want_hp = mode & 0x04
        lp = np.empty(n_samples, dtype=np.float32) if want_lp else None
        bp = np.empty(n_samples, dtype=np.float32) if want_bp else None
        hp = np.empty(n_samples, dtype=np.float32) if want_hp else None

        # Per-sample SVF recursion. Sequential by nature — can't fully vectorise.
        sat = self.model == "6581"
        for i in range(n_samples):
            high = input_arr[i] - low - damping * band
            band += f * high
            if sat:
                # 6581 integrator saturation: EXACTLY transparent up to
                # |band|=0.9, soft-compressing beyond — the growl appears
                # only when the filter is driven hot. (A curve applied to
                # every sample would act as cumulative damping inside the
                # feedback loop and crush the whole mix.)
                if band > 0.9:
                    band = 0.9 + (band - 0.9) / (1.0 + band - 0.9)
                elif band < -0.9:
                    band = -0.9 + (band + 0.9) / (1.0 - band - 0.9)
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

    @staticmethod
    def _exp_period(e):
        """Exponential-divider period by envelope value (decay/release)."""
        if e >= 0x5D: return 1
        if e >= 0x36: return 2
        if e >= 0x1A: return 4
        if e >= 0x0E: return 8
        if e >= 0x06: return 16
        if e >= 0x01: return 30
        return 1

    def _envelope_chunk(self, v, n_samples, np):
        """Cycle-driven hardware envelope: linear attack, piecewise-
        exponential decay/release via the divider thresholds, sustain as an
        EQUALITY comparison (raising sustain mid-decay lets the counter fall
        through — real chip quirk), counter frozen at zero, and the ADSR
        delay bug from exact-match rate counting."""
        out = np.empty(n_samples, dtype=np.float32)
        env = v.env
        state = v.env_state
        rate_cnt = v.rate_cnt
        exp_cnt = v.exp_cnt
        cps = self.CPU_CLOCK / self.SAMPLE_RATE
        acc = 0.0
        ad, sr_reg = v.attack_decay, v.sustain_release
        sustain = ((sr_reg >> 4) & 0x0F) * 0x11
        if state == 1:
            target = self.RATE_PERIODS[(ad >> 4) & 0x0F]
        elif state == 2:
            target = self.RATE_PERIODS[ad & 0x0F]
        else:
            target = self.RATE_PERIODS[sr_reg & 0x0F]
        scale = np.float32(1.0 / 255.0)
        for i in range(n_samples):
            acc += cps
            k = int(acc)
            acc -= k
            while k > 0:
                ctp = (target - rate_cnt) & 0x7FFF
                if ctp == 0:
                    ctp = 0x8000
                if k < ctp:
                    rate_cnt = (rate_cnt + k) & 0x7FFF
                    break
                k -= ctp
                rate_cnt = 0
                # --- rate pulse ---
                if state == 1:                        # attack: linear up
                    exp_cnt = 0
                    if env < 0xFF:
                        env += 1
                    if env == 0xFF:
                        state = 2
                        target = self.RATE_PERIODS[ad & 0x0F]
                else:
                    exp_cnt += 1
                    if exp_cnt >= self._exp_period(env):
                        exp_cnt = 0
                        if state == 2:                # decay to sustain
                            if env != sustain and env > 0:
                                env -= 1
                        else:                          # release to zero
                            if env > 0:
                                env -= 1
            out[i] = env * scale
        v.env = env
        v.env_state = state
        v.rate_cnt = rate_cnt
        v.exp_cnt = exp_cnt
        return out


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
        self.port_a_in_fn = None
        self.port_a_write_hook = None
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
        in_a = (self.port_a_in_fn() if self.port_a_in_fn is not None
                else self.port_a_in)
        a = ((self.pra & self.ddra) | (in_a & ~self.ddra)) & 0xFF
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
        if offset == self.R_PRA:
            if self.port_a_write_hook is not None:
                self.port_a_write_hook()
            self.pra = val
        elif offset == self.R_DDRA and self.port_a_write_hook is not None:
            self.port_a_write_hook()
            self.ddra = val
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

    def clock(self):
        # One PHI2 tick for cycle-accurate mode: decrement the timers by a single
        # cycle. (The fine ICR/IRQ-delay quirks the Lorenz CIA tests check are the
        # next tuning step; per-cycle decrement is already far closer than batch.)
        self.tick(1)


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

    def read_vic_bytes_bank(self, addr, n, bank):
        """Read n bytes via the VIC view of a SPECIFIC bank (0..3). Used for
        sprite data, whose pointer is recorded per raster: a game that switches
        $DD00 mid-frame (e.g. Pole Position II, bank 2 status band over a bank 3
        road) must fetch each sprite's shape from the bank live when that sprite
        displayed, not the render-time bank."""
        base = bank * 0x4000
        shadow = bank in (0, 2)
        out = bytearray(n)
        for i in range(n):
            a = (addr + i) & 0x3FFF
            if shadow and 0x1000 <= a < 0x2000:
                out[i] = self.rom[0xD000 + (a & 0x0FFF)]
            else:
                out[i] = self.ram[base + a]
        return bytes(out)

    def read_vic_block(self, addr, n):
        """Read n bytes via the VIC view as one fast RAM slice, with the
        character-ROM shadow ($1000-$1FFF in banks 0/2) overlaid — i.e. exactly
        what the VIC would fetch. Use this for bulk fetches (bitmap data,
        video matrix) so the renderer sees the same memory as read_vic()."""
        addr &= 0x3FFF
        bank = self.vic_bank()
        base = bank * 0x4000
        out = bytearray(self.ram[base + addr: base + addr + n])
        if bank in (0, 2):
            lo = max(addr, 0x1000)
            hi = min(addr + n, 0x2000)
            if lo < hi:
                ro = 0xD000 + (lo & 0x0FFF)
                out[lo - addr: hi - addr] = self.rom[ro: ro + (hi - lo)]
        return bytes(out)

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

    # "Magic constant" for the unstable ANE/XAA ($8B) and LXA/LAX-#imm ($AB)
    # opcodes, whose result is (A | magic) & …  . The real value is chip- and
    # temperature-dependent; 0xEE is what the Wolfgang-Lorenz suite and most
    # real programs (e.g. Wizball) expect. Override to model a different die.
    ANE_MAGIC = 0xEE
    LXA_MAGIC = 0xEE

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
        # Cycle-accurate ("clock") mode state: the active microcode generator
        # and the bus access it is currently waiting on. None => idle, the next
        # clock() begins a new instruction. Batch step() ignores these.
        self._micro = None
        self._pending = None
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
        self.pc = (self.pc + 1) & 0xFFFF
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

    # Read-access variants: indexed READS cost +1 cycle when indexing crosses
    # a page boundary (the 6502 re-reads with the fixed high byte). Stores and
    # RMW instructions always pay the fixed penalty (their dispatch cycle
    # counts already include it), so they keep using the plain variants.
    def _abs_x_rd(self):
        base = self.fetch_word()
        ea = (base + self.x) & 0xFFFF
        if (base ^ ea) & 0xFF00:
            self.cycles += 1
        return ea

    def _abs_y_rd(self):
        base = self.fetch_word()
        ea = (base + self.y) & 0xFFFF
        if (base ^ ea) & 0xFF00:
            self.cycles += 1
        return ea

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

    def _ind_y_rd(self):
        zp = self.fetch_byte()
        lo = self.mem.read_system_byte(zp)
        hi = self.mem.read_system_byte((zp + 1) & 0xFF)
        base = make_word(lo, hi)
        ea = (base + self.y) & 0xFFFF
        if (base ^ ea) & 0xFF00:
            self.cycles += 1
        return ea

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
        d[0x1D] = lambda: self._ora(M.read_system_byte(self._abs_x_rd()), 4)
        d[0x19] = lambda: self._ora(M.read_system_byte(self._abs_y_rd()), 4)
        d[0x01] = lambda: self._ora(M.read_system_byte(self._ind_x()), 6)
        d[0x11] = lambda: self._ora(M.read_system_byte(self._ind_y_rd()), 5)

        # AND
        d[0x29] = lambda: self._and(self._imm(), 2)
        d[0x25] = lambda: self._and(M.read_system_byte(self._zp()), 3)
        d[0x35] = lambda: self._and(M.read_system_byte(self._zp_x()), 4)
        d[0x2D] = lambda: self._and(M.read_system_byte(self._abs()), 4)
        d[0x3D] = lambda: self._and(M.read_system_byte(self._abs_x_rd()), 4)
        d[0x39] = lambda: self._and(M.read_system_byte(self._abs_y_rd()), 4)
        d[0x21] = lambda: self._and(M.read_system_byte(self._ind_x()), 6)
        d[0x31] = lambda: self._and(M.read_system_byte(self._ind_y_rd()), 5)

        # EOR
        d[0x49] = lambda: self._eor(self._imm(), 2)
        d[0x45] = lambda: self._eor(M.read_system_byte(self._zp()), 3)
        d[0x55] = lambda: self._eor(M.read_system_byte(self._zp_x()), 4)
        d[0x4D] = lambda: self._eor(M.read_system_byte(self._abs()), 4)
        d[0x5D] = lambda: self._eor(M.read_system_byte(self._abs_x_rd()), 4)
        d[0x59] = lambda: self._eor(M.read_system_byte(self._abs_y_rd()), 4)
        d[0x41] = lambda: self._eor(M.read_system_byte(self._ind_x()), 6)
        d[0x51] = lambda: self._eor(M.read_system_byte(self._ind_y_rd()), 5)

        # ADC
        d[0x69] = lambda: self._adc(self._imm(), 2)
        d[0x65] = lambda: self._adc(M.read_system_byte(self._zp()), 3)
        d[0x75] = lambda: self._adc(M.read_system_byte(self._zp_x()), 4)
        d[0x6D] = lambda: self._adc(M.read_system_byte(self._abs()), 4)
        d[0x7D] = lambda: self._adc(M.read_system_byte(self._abs_x_rd()), 4)
        d[0x79] = lambda: self._adc(M.read_system_byte(self._abs_y_rd()), 4)
        d[0x61] = lambda: self._adc(M.read_system_byte(self._ind_x()), 6)
        d[0x71] = lambda: self._adc(M.read_system_byte(self._ind_y_rd()), 5)

        # SBC
        d[0xE9] = lambda: self._sbc(self._imm(), 2)
        d[0xE5] = lambda: self._sbc(M.read_system_byte(self._zp()), 3)
        d[0xF5] = lambda: self._sbc(M.read_system_byte(self._zp_x()), 4)
        d[0xED] = lambda: self._sbc(M.read_system_byte(self._abs()), 4)
        d[0xFD] = lambda: self._sbc(M.read_system_byte(self._abs_x_rd()), 4)
        d[0xF9] = lambda: self._sbc(M.read_system_byte(self._abs_y_rd()), 4)
        d[0xE1] = lambda: self._sbc(M.read_system_byte(self._ind_x()), 6)
        d[0xF1] = lambda: self._sbc(M.read_system_byte(self._ind_y_rd()), 5)

        # CMP / CPX / CPY
        d[0xC9] = lambda: self._cmp_reg(self.a, self._imm(), 2)
        d[0xC5] = lambda: self._cmp_reg(self.a, M.read_system_byte(self._zp()), 3)
        d[0xD5] = lambda: self._cmp_reg(self.a, M.read_system_byte(self._zp_x()), 4)
        d[0xCD] = lambda: self._cmp_reg(self.a, M.read_system_byte(self._abs()), 4)
        d[0xDD] = lambda: self._cmp_reg(self.a, M.read_system_byte(self._abs_x_rd()), 4)
        d[0xD9] = lambda: self._cmp_reg(self.a, M.read_system_byte(self._abs_y_rd()), 4)
        d[0xC1] = lambda: self._cmp_reg(self.a, M.read_system_byte(self._ind_x()), 6)
        d[0xD1] = lambda: self._cmp_reg(self.a, M.read_system_byte(self._ind_y_rd()), 5)
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
        d[0xBD] = lambda: self._lda_from(self._abs_x_rd(), 4)
        d[0xB9] = lambda: self._lda_from(self._abs_y_rd(), 4)
        d[0xA1] = lambda: self._lda_from(self._ind_x(), 6)
        d[0xB1] = lambda: self._lda_from(self._ind_y_rd(), 5)

        d[0xA2] = lambda: (setattr(self, 'x', self._imm()), self.update_nz(self.x), self._tick(2))
        d[0xA6] = lambda: self._ldx_from(self._zp(), 3)
        d[0xB6] = lambda: self._ldx_from(self._zp_y(), 4)
        d[0xAE] = lambda: self._ldx_from(self._abs(), 4)
        d[0xBE] = lambda: self._ldx_from(self._abs_y_rd(), 4)

        d[0xA0] = lambda: (setattr(self, 'y', self._imm()), self.update_nz(self.y), self._tick(2))
        d[0xA4] = lambda: self._ldy_from(self._zp(), 3)
        d[0xB4] = lambda: self._ldy_from(self._zp_x(), 4)
        d[0xAC] = lambda: self._ldy_from(self._abs(), 4)
        d[0xBC] = lambda: self._ldy_from(self._abs_x_rd(), 4)

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
        d[0xB3] = lambda: self._lax_from(self._ind_y_rd(), 5)
        d[0xAF] = lambda: self._lax_from(self._abs(),   4)
        d[0xBF] = lambda: self._lax_from(self._abs_y_rd(), 4)

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
            d[op] = lambda: (self._abs_x_rd(), self._tick(4))  # NOP abs,X

        # Genuinely unstable / rarely used illegals. ANE ($8B) and LXA ($AB)
        # follow the (A | magic) & ... model that the Wolfgang-Lorenz suite and
        # most real programs expect (magic constant configurable, see ANE_MAGIC
        # / LXA_MAGIC). The SH* stores write reg & (H+1) with the documented
        # page-crossing corruption of the target's high byte.
        d[0x8B] = lambda: self._ane()                          # ANE / XAA
        d[0xAB] = lambda: self._lxa()                          # LXA / LAX #imm
        d[0x93] = lambda: self._sha_ind_y()                    # SHA / AHX (zp),Y
        d[0x9F] = lambda: self._sha_abs_y()                    # SHA / AHX abs,Y
        d[0x9E] = lambda: self._shx_abs_y()                    # SHX / SXA abs,Y
        d[0x9C] = lambda: self._shy_abs_x()                    # SHY / SYA abs,X
        d[0x9B] = lambda: self._shs_abs_y()                    # SHS / TAS abs,Y
        d[0xBB] = lambda: self._las_abs_y()                    # LAS / LAE abs,Y

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

    def _arr(self):                             # AND #imm + ROR A (ARR, $6B)
        v = self._imm()
        t = self.a & v
        carry_in = self.get_flag_c()
        if self.get_flag_d():
            # Decimal mode: the rotate is done, N/Z/V come from the rotated
            # value, then a BCD fix-up adjusts each nibble (and sets C on the
            # high-nibble carry). This matches the real NMOS 6510 (and VICE).
            res = (t >> 1) | (0x80 if carry_in else 0)
            self.set_flag(self.FN, carry_in)
            self.set_flag(self.FZ, res == 0)
            self.set_flag(self.FV, ((t ^ res) & 0x40) != 0)
            if (t & 0x0F) + (t & 0x01) > 0x05:
                res = (res & 0xF0) | ((res + 0x06) & 0x0F)
            if (t & 0xF0) + (t & 0x10) > 0x50:
                res = (res + 0x60) & 0xFF
                self.set_flag(self.FC, True)
            else:
                self.set_flag(self.FC, False)
            self.a = res & 0xFF
        else:
            # Binary mode: C and V come from bits 6 and 5 of the result.
            self.a = (t >> 1) | (0x80 if carry_in else 0)
            self.update_nz(self.a)
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

    def _ane(self):                             # ANE / XAA ($8B) — unstable
        # A = (A | magic) & X & imm. The "magic" byte is chip-/temperature-
        # dependent on real hardware; ANE_MAGIC selects the modelled die.
        v = self._imm()
        self.a = (self.a | self.ANE_MAGIC) & self.x & v
        self.update_nz(self.a)
        self.cycles += 2

    def _lxa(self):                             # LXA / LAX #imm ($AB) — unstable
        # A = X = (A | magic) & imm. Same magic-constant caveat as ANE.
        v = self._imm()
        r = (self.a | self.LXA_MAGIC) & v
        self.a = r
        self.x = r
        self.update_nz(r)
        self.cycles += 2

    def _sh_store(self, base, index, reg_val, cycles):
        # Store opcodes SHA/SHX/SHY/SHS: the value written is reg & (H+1) where H
        # is the high byte of the base address. When the indexed address crosses
        # a page boundary the high byte of the target gets replaced by the value
        # itself — the documented "unstable" behaviour the Lorenz suite checks.
        H = (base >> 8) & 0xFF
        value = reg_val & ((H + 1) & 0xFF)
        addr = (base + index) & 0xFFFF
        if (base & 0xFF) + index > 0xFF:            # page crossed
            addr = (addr & 0x00FF) | (value << 8)
        self.mem.write_system_byte(addr, value)
        self._tick(cycles)

    def _sha_abs_y(self):                       # SHA/AHX $9F  (abs,Y)
        self._sh_store(self.fetch_word(), self.y, self.a & self.x, 5)

    def _sha_ind_y(self):                       # SHA/AHX $93  ((zp),Y)
        zp = self.fetch_byte()
        base = make_word(self.mem.read_system_byte(zp),
                         self.mem.read_system_byte((zp + 1) & 0xFF))
        self._sh_store(base, self.y, self.a & self.x, 6)

    def _shx_abs_y(self):                       # SHX/SXA $9E  (abs,Y)
        self._sh_store(self.fetch_word(), self.y, self.x, 5)

    def _shy_abs_x(self):                       # SHY/SYA $9C  (abs,X)
        self._sh_store(self.fetch_word(), self.x, self.y, 5)

    def _shs_abs_y(self):                       # SHS/TAS $9B  (abs,Y)
        self.sp = self.a & self.x               # SP = A & X
        self._sh_store(self.fetch_word(), self.y, self.a & self.x, 5)

    def _las_abs_y(self):                       # LAS / LAE / LAR $BB  (abs,Y)
        # A = X = SP = (memory AND SP). Sets N/Z from the result.
        t = self.mem.read_system_byte(self._abs_y_rd()) & self.sp
        self.a = t
        self.x = t
        self.sp = t
        self.update_nz(t)
        self._tick(4)


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

    # ------------------------------------------------------------------
    # Cycle-accurate ("clock") execution. One clock() == one PHI2 cycle.
    # Each opcode is a microcode generator (see _CYC_TABLE) yielding exactly
    # one bus access per cycle: ('R',addr) / ('W',addr,val) / ('I',). The CPU
    # can be stalled mid-instruction: when the VIC pulls BA low (badline /
    # sprite DMA) a READ cycle is repeated instead of advancing — the real
    # 6510 behaviour every timing test relies on. Writes always proceed.
    # This runs alongside the batch step()/dispatch, which is untouched; the
    # System selects which to use via cycle_accurate.
    # ------------------------------------------------------------------
    def clock(self, ba=True):
        if self._micro is None:
            self._micro = self._cyc_instruction()
            try:
                self._pending = next(self._micro)
            except StopIteration:
                # A KERNAL trap fired (the sequencer returned without yielding a
                # bus cycle); it already did its work, so this tick has no CPU
                # bus access. VIC/CIA still advance in System.clock().
                self._micro = None
                return
        kind = self._pending[0]
        if kind == 'R':
            if not ba:                       # BA low -> stall the read cycle
                self.cycles += 1
                return
            try:
                self._pending = self._micro.send(
                    self.mem.read_system_byte(self._pending[1] & 0xFFFF))
            except StopIteration:
                self._micro = None
        elif kind == 'W':
            self.mem.write_system_byte(self._pending[1] & 0xFFFF,
                                       self._pending[2] & 0xFF)
            try:
                self._pending = self._micro.send(None)
            except StopIteration:
                self._micro = None
        else:                                # 'I' internal cycle (no bus)
            try:
                self._pending = self._micro.send(None)
            except StopIteration:
                self._micro = None
        self.cycles += 1

    def _cyc_instruction(self):
        # KERNAL traps (same policy as step()): only when KERNAL ROM is mapped.
        if self.traps and self.pc in self.traps and \
           self.mem.pla.address_space(self.pc) == AddressSpace.KERNAL_ROM:
            self.traps[self.pc]()
            return
        if self.nmi_pending:
            self.nmi_pending = False
            yield from _cyc_irqseq(self, 0xFFFA, False)
            return
        if self.irq_line and not self.get_flag_i():
            yield from _cyc_irqseq(self, 0xFFFE, False)
            return
        op = yield ('R', self.pc)
        self.pc = (self.pc + 1) & 0xFFFF
        handler = _CYC_TABLE[op]
        if handler is None:
            print(f"Unknown opcode 0x{op:02X} at "
                  f"{word2hex((self.pc - 1) & 0xFFFF)} (cycle mode)")
            return
        yield from handler(self)

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
# Cycle-accurate microcode core (used by CPU.clock / cycle_accurate mode)
#
# Each opcode is a generator yielding one bus access per PHI2 cycle. Addressing
# is factored into ~10 templates (ADDR_R for reads with page-cross dummy read,
# ADDR_W for writes/RMW with the always-present dummy read); operations reuse
# the CPU's own semantics (update_nz / _adc / _sbc) so results match the batch
# core exactly. Verified against the Klaus 6502 functional test.
# =============================================================================
_FN, _FV, _FB, _FD, _FI, _FZ, _FC = 7, 6, 4, 3, 2, 1, 0


def _a_zp(c):
    a = yield ('R', c.pc); c.pc = (c.pc + 1) & 0xFFFF
    return a
def _a_zpx(c):
    a = yield ('R', c.pc); c.pc = (c.pc + 1) & 0xFFFF
    yield ('R', a); return (a + c.x) & 0xFF
def _a_zpy(c):
    a = yield ('R', c.pc); c.pc = (c.pc + 1) & 0xFFFF
    yield ('R', a); return (a + c.y) & 0xFF
def _a_abs(c):
    lo = yield ('R', c.pc); c.pc = (c.pc + 1) & 0xFFFF
    hi = yield ('R', c.pc); c.pc = (c.pc + 1) & 0xFFFF
    return lo | (hi << 8)
def _a_abx_r(c):
    lo = yield ('R', c.pc); c.pc = (c.pc + 1) & 0xFFFF
    hi = yield ('R', c.pc); c.pc = (c.pc + 1) & 0xFFFF
    b = lo | (hi << 8); a = (b + c.x) & 0xFFFF
    if (b & 0xFF00) != (a & 0xFF00): yield ('R', (b & 0xFF00) | (a & 0xFF))
    return a
def _a_aby_r(c):
    lo = yield ('R', c.pc); c.pc = (c.pc + 1) & 0xFFFF
    hi = yield ('R', c.pc); c.pc = (c.pc + 1) & 0xFFFF
    b = lo | (hi << 8); a = (b + c.y) & 0xFFFF
    if (b & 0xFF00) != (a & 0xFF00): yield ('R', (b & 0xFF00) | (a & 0xFF))
    return a
def _a_abx_w(c):
    lo = yield ('R', c.pc); c.pc = (c.pc + 1) & 0xFFFF
    hi = yield ('R', c.pc); c.pc = (c.pc + 1) & 0xFFFF
    b = lo | (hi << 8); a = (b + c.x) & 0xFFFF
    yield ('R', (b & 0xFF00) | (a & 0xFF)); return a
def _a_aby_w(c):
    lo = yield ('R', c.pc); c.pc = (c.pc + 1) & 0xFFFF
    hi = yield ('R', c.pc); c.pc = (c.pc + 1) & 0xFFFF
    b = lo | (hi << 8); a = (b + c.y) & 0xFFFF
    yield ('R', (b & 0xFF00) | (a & 0xFF)); return a
def _a_inx(c):
    p = yield ('R', c.pc); c.pc = (c.pc + 1) & 0xFFFF
    yield ('R', p); p = (p + c.x) & 0xFF
    lo = yield ('R', p); hi = yield ('R', (p + 1) & 0xFF)
    return lo | (hi << 8)
def _a_iny_r(c):
    p = yield ('R', c.pc); c.pc = (c.pc + 1) & 0xFFFF
    lo = yield ('R', p); hi = yield ('R', (p + 1) & 0xFF)
    b = lo | (hi << 8); a = (b + c.y) & 0xFFFF
    if (b & 0xFF00) != (a & 0xFF00): yield ('R', (b & 0xFF00) | (a & 0xFF))
    return a
def _a_iny_w(c):
    p = yield ('R', c.pc); c.pc = (c.pc + 1) & 0xFFFF
    lo = yield ('R', p); hi = yield ('R', (p + 1) & 0xFF)
    b = lo | (hi << 8); a = (b + c.y) & 0xFFFF
    yield ('R', (b & 0xFF00) | (a & 0xFF)); return a
_ADDR_R = {'zp': _a_zp, 'zpx': _a_zpx, 'zpy': _a_zpy, 'abs': _a_abs,
           'abx': _a_abx_r, 'aby': _a_aby_r, 'inx': _a_inx, 'iny': _a_iny_r}
_ADDR_W = {'zp': _a_zp, 'zpx': _a_zpx, 'zpy': _a_zpy, 'abs': _a_abs,
           'abx': _a_abx_w, 'aby': _a_aby_w, 'inx': _a_inx, 'iny': _a_iny_w}


def _oLDA(c, v): c.a = v; c.update_nz(v)
def _oLDX(c, v): c.x = v; c.update_nz(v)
def _oLDY(c, v): c.y = v; c.update_nz(v)
def _oORA(c, v): c.a = c.a | v; c.update_nz(c.a)
def _oAND(c, v): c.a = c.a & v; c.update_nz(c.a)
def _oEOR(c, v): c.a = c.a ^ v; c.update_nz(c.a)
def _oADC(c, v): c._adc(v, 0)
def _oSBC(c, v): c._sbc(v, 0)
def _cyc_cmp(c, r, v):
    t = (r - v) & 0xFF; c.set_flag(_FC, r >= v); c.update_nz(t)
def _oCMP(c, v): _cyc_cmp(c, c.a, v)
def _oCPX(c, v): _cyc_cmp(c, c.x, v)
def _oCPY(c, v): _cyc_cmp(c, c.y, v)
def _oBIT(c, v):
    c.set_flag(_FZ, (c.a & v) == 0); c.set_flag(_FN, v & 0x80); c.set_flag(_FV, v & 0x40)
def _oLAX(c, v): c.a = v; c.x = v; c.update_nz(v)
def _oNOPr(c, v): pass
_READ_OPS = {'LDA': _oLDA, 'LDX': _oLDX, 'LDY': _oLDY, 'ORA': _oORA, 'AND': _oAND,
             'EOR': _oEOR, 'ADC': _oADC, 'SBC': _oSBC, 'CMP': _oCMP, 'CPX': _oCPX,
             'CPY': _oCPY, 'BIT': _oBIT, 'LAX': _oLAX, 'NOP': _oNOPr}
_STORE_OPS = {'STA': lambda c: c.a, 'STX': lambda c: c.x, 'STY': lambda c: c.y,
              'SAX': lambda c: c.a & c.x}

def _rASL(c, v): c.set_flag(_FC, v & 0x80); v = (v << 1) & 0xFF; c.update_nz(v); return v
def _rLSR(c, v): c.set_flag(_FC, v & 1); v >>= 1; c.update_nz(v); return v
def _rROL(c, v):
    nc = v & 0x80; v = ((v << 1) | c.get_flag(_FC)) & 0xFF; c.set_flag(_FC, nc); c.update_nz(v); return v
def _rROR(c, v):
    nc = v & 1; v = (v >> 1) | (c.get_flag(_FC) << 7); c.set_flag(_FC, nc); c.update_nz(v); return v
def _rINC(c, v): v = (v + 1) & 0xFF; c.update_nz(v); return v
def _rDEC(c, v): v = (v - 1) & 0xFF; c.update_nz(v); return v
def _rSLO(c, v): v = _rASL(c, v); c.a = c.a | v; c.update_nz(c.a); return v
def _rRLA(c, v): v = _rROL(c, v); c.a = c.a & v; c.update_nz(c.a); return v
def _rSRE(c, v): v = _rLSR(c, v); c.a = c.a ^ v; c.update_nz(c.a); return v
def _rRRA(c, v): v = _rROR(c, v); c._adc(v, 0); return v
def _rDCP(c, v): v = (v - 1) & 0xFF; _cyc_cmp(c, c.a, v); return v
def _rISC(c, v): v = (v + 1) & 0xFF; c._sbc(v, 0); return v
_RMW_OPS = {'ASL': _rASL, 'LSR': _rLSR, 'ROL': _rROL, 'ROR': _rROR, 'INC': _rINC,
            'DEC': _rDEC, 'SLO': _rSLO, 'RLA': _rRLA, 'SRE': _rSRE, 'RRA': _rRRA,
            'DCP': _rDCP, 'ISC': _rISC}


def _cyc_mk_read(mode, op):
    fn = _READ_OPS[op]
    def run(c):
        if mode == 'imm':
            v = yield ('R', c.pc); c.pc = (c.pc + 1) & 0xFFFF
        else:
            ad = yield from _ADDR_R[mode](c); v = yield ('R', ad)
        fn(c, v)
    return run
def _cyc_mk_store(mode, op):
    fn = _STORE_OPS[op]
    def run(c):
        ad = yield from _ADDR_W[mode](c); yield ('W', ad, fn(c))
    return run
def _cyc_mk_rmw(mode, op):
    fn = _RMW_OPS[op]
    def run(c):
        ad = yield from _ADDR_W[mode](c)
        v = yield ('R', ad); yield ('W', ad, v); yield ('W', ad, fn(c, v))
    return run
def _cyc_mk_acc(op):
    fn = _RMW_OPS[op]
    def run(c):
        yield ('R', c.pc); c.a = fn(c, c.a)
    return run
def _cyc_mk_imp(fn):
    def run(c):
        yield ('R', c.pc); fn(c)
    return run
def _cyc_mk_br(bit, want):
    def run(c):
        off = yield ('R', c.pc); c.pc = (c.pc + 1) & 0xFFFF
        if c.get_flag(bit) != want: return
        yield ('R', c.pc)
        t = (c.pc + ((off ^ 0x80) - 0x80)) & 0xFFFF
        if (t & 0xFF00) != (c.pc & 0xFF00): yield ('R', (c.pc & 0xFF00) | (t & 0xFF))
        c.pc = t
    return run


def _cyc_irqseq(c, vec, brk):
    yield ('R', c.pc)
    if brk: c.pc = (c.pc + 1) & 0xFFFF
    yield ('W', 0x100 + c.sp, (c.pc >> 8) & 0xFF); c.sp = (c.sp - 1) & 0xFF
    yield ('W', 0x100 + c.sp, c.pc & 0xFF); c.sp = (c.sp - 1) & 0xFF
    pv = (c.reg_sr | 0x30) if brk else ((c.reg_sr & ~(1 << _FB)) | 0x20)
    yield ('W', 0x100 + c.sp, pv); c.sp = (c.sp - 1) & 0xFF
    lo = yield ('R', vec); hi = yield ('R', vec + 1)
    c.set_flag(_FI, True); c.pc = lo | (hi << 8)
def _o_jmp(c):
    lo = yield ('R', c.pc); c.pc = (c.pc + 1) & 0xFFFF
    hi = yield ('R', c.pc); c.pc = lo | (hi << 8)
def _o_jmpi(c):
    lo = yield ('R', c.pc); c.pc = (c.pc + 1) & 0xFFFF
    hi = yield ('R', c.pc); c.pc = (c.pc + 1) & 0xFFFF
    p = lo | (hi << 8)
    tl = yield ('R', p); th = yield ('R', (p & 0xFF00) | ((p + 1) & 0xFF))
    c.pc = tl | (th << 8)
def _o_jsr(c):
    lo = yield ('R', c.pc); c.pc = (c.pc + 1) & 0xFFFF
    yield ('I',)
    yield ('W', 0x100 + c.sp, (c.pc >> 8) & 0xFF); c.sp = (c.sp - 1) & 0xFF
    yield ('W', 0x100 + c.sp, c.pc & 0xFF); c.sp = (c.sp - 1) & 0xFF
    hi = yield ('R', c.pc); c.pc = lo | (hi << 8)
def _o_rts(c):
    yield ('R', c.pc); yield ('I',)
    c.sp = (c.sp + 1) & 0xFF; lo = yield ('R', 0x100 + c.sp)
    c.sp = (c.sp + 1) & 0xFF; hi = yield ('R', 0x100 + c.sp)
    yield ('R', c.pc); c.pc = ((lo | (hi << 8)) + 1) & 0xFFFF
def _o_rti(c):
    yield ('R', c.pc); yield ('I',)
    c.sp = (c.sp + 1) & 0xFF; p = yield ('R', 0x100 + c.sp)
    c.reg_sr = (p & ~(1 << _FB)) | (1 << 5)
    c.sp = (c.sp + 1) & 0xFF; lo = yield ('R', 0x100 + c.sp)
    c.sp = (c.sp + 1) & 0xFF; hi = yield ('R', 0x100 + c.sp)
    c.pc = lo | (hi << 8)
def _o_brk(c):
    yield from _cyc_irqseq(c, 0xFFFE, True)
def _o_pha(c):
    yield ('R', c.pc); yield ('W', 0x100 + c.sp, c.a); c.sp = (c.sp - 1) & 0xFF
def _o_php(c):
    yield ('R', c.pc); yield ('W', 0x100 + c.sp, c.reg_sr | 0x30); c.sp = (c.sp - 1) & 0xFF
def _o_pla(c):
    yield ('R', c.pc); yield ('I',)
    c.sp = (c.sp + 1) & 0xFF; c.a = yield ('R', 0x100 + c.sp); c.update_nz(c.a)
def _o_plp(c):
    yield ('R', c.pc); yield ('I',)
    c.sp = (c.sp + 1) & 0xFF; p = yield ('R', 0x100 + c.sp)
    c.reg_sr = (p & ~(1 << _FB)) | (1 << 5)

def _iCLC(c): c.set_flag(_FC, 0)
def _iSEC(c): c.set_flag(_FC, 1)
def _iCLI(c): c.set_flag(_FI, 0)
def _iSEI(c): c.set_flag(_FI, 1)
def _iCLD(c): c.set_flag(_FD, 0)
def _iSED(c): c.set_flag(_FD, 1)
def _iCLV(c): c.set_flag(_FV, 0)
def _iTAX(c): c.x = c.a; c.update_nz(c.x)
def _iTAY(c): c.y = c.a; c.update_nz(c.y)
def _iTXA(c): c.a = c.x; c.update_nz(c.a)
def _iTYA(c): c.a = c.y; c.update_nz(c.a)
def _iTSX(c): c.x = c.sp; c.update_nz(c.x)
def _iTXS(c): c.sp = c.x
def _iINX(c): c.x = (c.x + 1) & 0xFF; c.update_nz(c.x)
def _iINY(c): c.y = (c.y + 1) & 0xFF; c.update_nz(c.y)
def _iDEX(c): c.x = (c.x - 1) & 0xFF; c.update_nz(c.x)
def _iDEY(c): c.y = (c.y - 1) & 0xFF; c.update_nz(c.y)
def _iNOP(c): pass


_CYC_TABLE = [None] * 256
def _cyc_fill():
    R, W, M = _cyc_mk_read, _cyc_mk_store, _cyc_mk_rmw
    e = {
        0xA9: R('imm','LDA'),0xA5: R('zp','LDA'),0xB5: R('zpx','LDA'),0xAD: R('abs','LDA'),
        0xBD: R('abx','LDA'),0xB9: R('aby','LDA'),0xA1: R('inx','LDA'),0xB1: R('iny','LDA'),
        0xA2: R('imm','LDX'),0xA6: R('zp','LDX'),0xB6: R('zpy','LDX'),0xAE: R('abs','LDX'),0xBE: R('aby','LDX'),
        0xA0: R('imm','LDY'),0xA4: R('zp','LDY'),0xB4: R('zpx','LDY'),0xAC: R('abs','LDY'),0xBC: R('abx','LDY'),
        0x85: W('zp','STA'),0x95: W('zpx','STA'),0x8D: W('abs','STA'),0x9D: W('abx','STA'),
        0x99: W('aby','STA'),0x81: W('inx','STA'),0x91: W('iny','STA'),
        0x86: W('zp','STX'),0x96: W('zpy','STX'),0x8E: W('abs','STX'),
        0x84: W('zp','STY'),0x94: W('zpx','STY'),0x8C: W('abs','STY'),
        0x09: R('imm','ORA'),0x05: R('zp','ORA'),0x15: R('zpx','ORA'),0x0D: R('abs','ORA'),
        0x1D: R('abx','ORA'),0x19: R('aby','ORA'),0x01: R('inx','ORA'),0x11: R('iny','ORA'),
        0x29: R('imm','AND'),0x25: R('zp','AND'),0x35: R('zpx','AND'),0x2D: R('abs','AND'),
        0x3D: R('abx','AND'),0x39: R('aby','AND'),0x21: R('inx','AND'),0x31: R('iny','AND'),
        0x49: R('imm','EOR'),0x45: R('zp','EOR'),0x55: R('zpx','EOR'),0x4D: R('abs','EOR'),
        0x5D: R('abx','EOR'),0x59: R('aby','EOR'),0x41: R('inx','EOR'),0x51: R('iny','EOR'),
        0x69: R('imm','ADC'),0x65: R('zp','ADC'),0x75: R('zpx','ADC'),0x6D: R('abs','ADC'),
        0x7D: R('abx','ADC'),0x79: R('aby','ADC'),0x61: R('inx','ADC'),0x71: R('iny','ADC'),
        0xE9: R('imm','SBC'),0xE5: R('zp','SBC'),0xF5: R('zpx','SBC'),0xED: R('abs','SBC'),
        0xFD: R('abx','SBC'),0xF9: R('aby','SBC'),0xE1: R('inx','SBC'),0xF1: R('iny','SBC'),0xEB: R('imm','SBC'),
        0xC9: R('imm','CMP'),0xC5: R('zp','CMP'),0xD5: R('zpx','CMP'),0xCD: R('abs','CMP'),
        0xDD: R('abx','CMP'),0xD9: R('aby','CMP'),0xC1: R('inx','CMP'),0xD1: R('iny','CMP'),
        0xE0: R('imm','CPX'),0xE4: R('zp','CPX'),0xEC: R('abs','CPX'),
        0xC0: R('imm','CPY'),0xC4: R('zp','CPY'),0xCC: R('abs','CPY'),
        0x24: R('zp','BIT'),0x2C: R('abs','BIT'),
        0x06: M('zp','ASL'),0x16: M('zpx','ASL'),0x0E: M('abs','ASL'),0x1E: M('abx','ASL'),
        0x46: M('zp','LSR'),0x56: M('zpx','LSR'),0x4E: M('abs','LSR'),0x5E: M('abx','LSR'),
        0x26: M('zp','ROL'),0x36: M('zpx','ROL'),0x2E: M('abs','ROL'),0x3E: M('abx','ROL'),
        0x66: M('zp','ROR'),0x76: M('zpx','ROR'),0x6E: M('abs','ROR'),0x7E: M('abx','ROR'),
        0xE6: M('zp','INC'),0xF6: M('zpx','INC'),0xEE: M('abs','INC'),0xFE: M('abx','INC'),
        0xC6: M('zp','DEC'),0xD6: M('zpx','DEC'),0xCE: M('abs','DEC'),0xDE: M('abx','DEC'),
        0x0A: _cyc_mk_acc('ASL'),0x4A: _cyc_mk_acc('LSR'),0x2A: _cyc_mk_acc('ROL'),0x6A: _cyc_mk_acc('ROR'),
        0x18: _cyc_mk_imp(_iCLC),0x38: _cyc_mk_imp(_iSEC),0x58: _cyc_mk_imp(_iCLI),0x78: _cyc_mk_imp(_iSEI),
        0xB8: _cyc_mk_imp(_iCLV),0xD8: _cyc_mk_imp(_iCLD),0xF8: _cyc_mk_imp(_iSED),
        0xAA: _cyc_mk_imp(_iTAX),0xA8: _cyc_mk_imp(_iTAY),0x8A: _cyc_mk_imp(_iTXA),0x98: _cyc_mk_imp(_iTYA),
        0xBA: _cyc_mk_imp(_iTSX),0x9A: _cyc_mk_imp(_iTXS),0xE8: _cyc_mk_imp(_iINX),0xC8: _cyc_mk_imp(_iINY),
        0xCA: _cyc_mk_imp(_iDEX),0x88: _cyc_mk_imp(_iDEY),0xEA: _cyc_mk_imp(_iNOP),
        0x48: _o_pha,0x08: _o_php,0x68: _o_pla,0x28: _o_plp,
        0x4C: _o_jmp,0x6C: _o_jmpi,0x20: _o_jsr,0x60: _o_rts,0x40: _o_rti,0x00: _o_brk,
        0x10: _cyc_mk_br(_FN,0),0x30: _cyc_mk_br(_FN,1),0x50: _cyc_mk_br(_FV,0),0x70: _cyc_mk_br(_FV,1),
        0x90: _cyc_mk_br(_FC,0),0xB0: _cyc_mk_br(_FC,1),0xD0: _cyc_mk_br(_FZ,0),0xF0: _cyc_mk_br(_FZ,1),
        0xA3: R('inx','LAX'),0xA7: R('zp','LAX'),0xAF: R('abs','LAX'),0xB3: R('iny','LAX'),
        0xB7: R('zpy','LAX'),0xBF: R('aby','LAX'),
        0x87: W('zp','SAX'),0x97: W('zpy','SAX'),0x8F: W('abs','SAX'),0x83: W('inx','SAX'),
        0x07: M('zp','SLO'),0x17: M('zpx','SLO'),0x0F: M('abs','SLO'),0x1F: M('abx','SLO'),
        0x1B: M('aby','SLO'),0x03: M('inx','SLO'),0x13: M('iny','SLO'),
        0x27: M('zp','RLA'),0x37: M('zpx','RLA'),0x2F: M('abs','RLA'),0x3F: M('abx','RLA'),
        0x3B: M('aby','RLA'),0x23: M('inx','RLA'),0x33: M('iny','RLA'),
        0x47: M('zp','SRE'),0x57: M('zpx','SRE'),0x4F: M('abs','SRE'),0x5F: M('abx','SRE'),
        0x5B: M('aby','SRE'),0x43: M('inx','SRE'),0x53: M('iny','SRE'),
        0x67: M('zp','RRA'),0x77: M('zpx','RRA'),0x6F: M('abs','RRA'),0x7F: M('abx','RRA'),
        0x7B: M('aby','RRA'),0x63: M('inx','RRA'),0x73: M('iny','RRA'),
        0xC7: M('zp','DCP'),0xD7: M('zpx','DCP'),0xCF: M('abs','DCP'),0xDF: M('abx','DCP'),
        0xDB: M('aby','DCP'),0xC3: M('inx','DCP'),0xD3: M('iny','DCP'),
        0xE7: M('zp','ISC'),0xF7: M('zpx','ISC'),0xEF: M('abs','ISC'),0xFF: M('abx','ISC'),
        0xFB: M('aby','ISC'),0xE3: M('inx','ISC'),0xF3: M('iny','ISC'),
    }
    for op, fn in e.items(): _CYC_TABLE[op] = fn
    for op in (0x1A,0x3A,0x5A,0x7A,0xDA,0xFA): _CYC_TABLE[op] = _cyc_mk_imp(_iNOP)
    for op in (0x80,0x82,0x89,0xC2,0xE2): _CYC_TABLE[op] = _cyc_mk_read('imm','NOP')
    for op in (0x04,0x44,0x64): _CYC_TABLE[op] = _cyc_mk_read('zp','NOP')
    for op in (0x14,0x34,0x54,0x74,0xD4,0xF4): _CYC_TABLE[op] = _cyc_mk_read('zpx','NOP')
    _CYC_TABLE[0x0C] = _cyc_mk_read('abs','NOP')
    for op in (0x1C,0x3C,0x5C,0x7C,0xDC,0xFC): _CYC_TABLE[op] = _cyc_mk_read('abx','NOP')
_cyc_fill()


# =============================================================================
# D64 disk image
# =============================================================================

class Via:
    """MOS 6522 VIA — the 1541 has two ($1800 serial bus, $1C00 drive
    mechanics). Ports with data direction, both timers (T1 one-shot and
    free-run, T2 one-shot), IFR/IER interrupt logic. Port inputs come from
    callbacks so the serial bus / mechanics can be wired in later milestones."""

    def __init__(self, name="VIA"):
        self.name = name
        self.ora = 0
        self.orb = 0
        self.ddra = 0
        self.ddrb = 0
        self.t1_counter = 0xFFFF
        self.t1_latch = 0xFFFF
        self.t1_running = False
        self.t2_counter = 0xFFFF
        self.t2_latch_lo = 0
        self.t2_running = False
        self.acr = 0
        self.pcr = 0
        self.sr = 0
        self.ifr = 0
        self.ier = 0
        self.port_a_in = lambda: 0xFF
        self.port_b_in = lambda: 0xFF

    def _set_flag(self, bit):
        self.ifr |= bit

    def irq(self):
        return (self.ifr & self.ier & 0x7F) != 0

    def read(self, off):
        off &= 0x0F
        if off == 0x0:
            self.ifr &= ~0x18
            return ((self.orb & self.ddrb)
                    | (self.port_b_in() & ~self.ddrb)) & 0xFF
        if off == 0x1 or off == 0xF:
            if off == 0x1:
                self.ifr &= ~0x03
            return ((self.ora & self.ddra)
                    | (self.port_a_in() & ~self.ddra)) & 0xFF
        if off == 0x2: return self.ddrb
        if off == 0x3: return self.ddra
        if off == 0x4:
            self.ifr &= ~0x40
            return self.t1_counter & 0xFF
        if off == 0x5: return (self.t1_counter >> 8) & 0xFF
        if off == 0x6: return self.t1_latch & 0xFF
        if off == 0x7: return (self.t1_latch >> 8) & 0xFF
        if off == 0x8:
            self.ifr &= ~0x20
            return self.t2_counter & 0xFF
        if off == 0x9: return (self.t2_counter >> 8) & 0xFF
        if off == 0xA: return self.sr
        if off == 0xB: return self.acr
        if off == 0xC: return self.pcr
        if off == 0xD:
            v = self.ifr & 0x7F
            if v & self.ier:
                v |= 0x80
            return v
        if off == 0xE: return self.ier | 0x80
        return 0xFF

    def write(self, off, val):
        off &= 0x0F
        val &= 0xFF
        if off == 0x0:
            self.orb = val
            self.ifr &= ~0x18
        elif off == 0x1 or off == 0xF:
            self.ora = val
            if off == 0x1:
                self.ifr &= ~0x03
        elif off == 0x2: self.ddrb = val
        elif off == 0x3: self.ddra = val
        elif off == 0x4 or off == 0x6:
            self.t1_latch = (self.t1_latch & 0xFF00) | val
        elif off == 0x5:
            self.t1_latch = (self.t1_latch & 0x00FF) | (val << 8)
            self.t1_counter = self.t1_latch
            self.ifr &= ~0x40
            self.t1_running = True
        elif off == 0x7:
            self.t1_latch = (self.t1_latch & 0x00FF) | (val << 8)
            self.ifr &= ~0x40
        elif off == 0x8:
            self.t2_latch_lo = val
        elif off == 0x9:
            self.t2_counter = (val << 8) | self.t2_latch_lo
            self.ifr &= ~0x20
            self.t2_running = True
        elif off == 0xA: self.sr = val
        elif off == 0xB: self.acr = val
        elif off == 0xC: self.pcr = val
        elif off == 0xD: self.ifr &= ~val
        elif off == 0xE:
            if val & 0x80:
                self.ier |= (val & 0x7F)
            else:
                self.ier &= ~(val & 0x7F)

    def tick(self, cycles):
        if self.t1_running:
            self.t1_counter -= cycles
            while self.t1_counter < 0:
                self._set_flag(0x40)
                if self.acr & 0x40:
                    self.t1_counter += self.t1_latch + 2
                    if self.t1_latch == 0:
                        self.t1_counter = 0
                        break
                else:
                    self.t1_counter &= 0xFFFF
                    self.t1_running = False
                    break
        if self.t2_running and not (self.acr & 0x20):
            self.t2_counter -= cycles
            if self.t2_counter < 0:
                self._set_flag(0x20)
                self.t2_counter &= 0xFFFF
                self.t2_running = False


class IecBus:
    """IEC serial bus — ATN/CLK/DATA as open-collector wired-AND between the
    C64 (CIA2 port A, inverting 7406 drivers: output bit 1 = line pulled low)
    and the 1541 (VIA1 port B, same driver arrangement). Includes the 1541's
    ATN auto-acknowledge gate: whenever the ATNA output does not match the
    ATN line, DATA is pulled low in hardware — this is how a drive answers
    an attention call even before its CPU reacts.

    Line state convention: True = pulled low = asserted.
    Input polarities of both receivers are calibratable (CPU_IN_INV /
    DRV_IN_INV) and were validated empirically against the original KERNAL
    and DOS ROMs talking to each other."""

    CPU_IN_INV = False     # $DD00 bits 6/7 read the electrical line level
    DRV_IN_INV = True      # 1541 receivers invert: pulled line reads 1

    def __init__(self, cia2, via1):
        self.cia2 = cia2
        self.via1 = via1
        self._atn_prev = False

    def _cpu_out(self):
        eff = self.cia2.pra & self.cia2.ddra
        return bool(eff & 0x08), bool(eff & 0x10), bool(eff & 0x20)

    def _drv_out(self):
        eff = self.via1.orb & self.via1.ddrb
        # The ATNA XOR gate is fed by the PB4 PIN level: driven by ORB when
        # DDR makes it an output, but pulled HIGH when configured as input.
        # Fastloaders exploit exactly this to neutralise the auto-acknowledge
        # hardware (set DDRB bit4=0 -> pin high -> gate matches asserted ATN).
        atna = bool((self.via1.orb | ~self.via1.ddrb) & 0x10)
        return bool(eff & 0x08), bool(eff & 0x02), atna

    def lines(self):
        atn, cclk, cdata = self._cpu_out()
        dclk, ddata, atna = self._drv_out()
        clk = cclk or dclk
        data = cdata or ddata or (atn != atna)     # auto-acknowledge XOR
        return atn, clk, data

    def poll(self):
        """Propagate ATN edges into the drive's VIA1 CA1 interrupt flag —
        the wire the whole 1541 attention handling hangs on."""
        atn, _, _ = self.lines()
        if atn != self._atn_prev:
            self._atn_prev = atn
            if atn:
                self.via1._set_flag(0x02)          # CA1: ATN asserted edge

    def cia2_port_a_in(self):
        _, clk, data = self.lines()
        v = 0xFF
        if clk != self.CPU_IN_INV:
            v &= ~0x40
        if data != self.CPU_IN_INV:
            v &= ~0x80
        return v

    def via1_port_b_in(self):
        atn, clk, data = self.lines()
        v = 0xFF
        # Device-number jumpers on PB5/PB6: both closed (0) = device 8.
        v &= ~0x60
        if clk != self.DRV_IN_INV:
            v &= ~0x04
        if data != self.DRV_IN_INV:
            v &= ~0x01
        if atn != self.DRV_IN_INV:
            v &= ~0x80
        return v


class DriveMemory:
    """1541 address space: 2 KB RAM (mirrored below $1800), VIA1 at $1800,
    VIA2 at $1C00, 16 KB DOS ROM in the upper half."""

    def __init__(self, rom, via1, via2):
        self.ram = bytearray(0x0800)
        self.rom = rom
        self.via1 = via1
        self.via2 = via2

    def read_system_byte(self, addr):
        addr &= 0xFFFF
        if addr >= 0x8000:
            return self.rom[addr & 0x3FFF]
        if 0x1800 <= addr < 0x1C00:
            return self.via1.read(addr)
        if 0x1C00 <= addr < 0x2000:
            return self.via2.read(addr)
        return self.ram[addr & 0x07FF]

    def write_system_byte(self, addr, val):
        addr &= 0xFFFF
        if addr >= 0x8000:
            return
        if 0x1800 <= addr < 0x1C00:
            self.via1.write(addr, val)
        elif 0x1C00 <= addr < 0x2000:
            self.via2.write(addr, val)
        else:
            self.ram[addr & 0x07FF] = val & 0xFF

    def read_system_word(self, addr):
        return (self.read_system_byte(addr)
                | (self.read_system_byte(addr + 1) << 8))


class Drive:
    """Commodore 1541 disk drive — milestone M0: the drive computer itself.
    Reuses the emulator's 6502 core with the 1541 memory map and boots the
    original DOS ROM to its idle loop. Serial bus and GCR disk follow in
    later milestones ($ python3 c64emu.py --drive game.d64)."""

    def __init__(self, dos_rom):
        self.via1 = Via("VIA1")
        self.via2 = Via("VIA2")
        self.mem = DriveMemory(bytes(dos_rom), self.via1, self.via2)
        self.cpu = CPU(self.mem)
        self.cpu.reset()
        self._cycle_debt = 0.0
        self._clock_base = None
        self._idle_streak = 0
        self.idle_until = 0          # c64-cycle horizon while provably idle
        self._d64 = None
        self._dirty = set()
        self._motor_prev = False
        self.blocks_read = 0
        self.tracks = []

    @property
    def led(self):
        return bool(self.via2.orb & self.via2.ddrb & 0x08)

    @property
    def motor(self):
        return bool(self.via2.orb & self.via2.ddrb & 0x04)

    # ------------------------------------------------------------------
    # M2: the spinning GCR disk
    # ------------------------------------------------------------------
    GCR_TAB = (0x0A, 0x0B, 0x12, 0x13, 0x0E, 0x0F, 0x16, 0x17,
               0x09, 0x19, 0x1A, 0x1B, 0x0D, 0x1D, 0x1E, 0x15)
    # Raw GCR bytes per track by speed zone (approx. real capacities)
    ZONE_TRACK_LEN = (7692, 7142, 6666, 6250)
    ZONE_CYC_PER_BYTE = (26, 28, 30, 32)

    @staticmethod
    def _zone(track):
        if track <= 17: return 0
        if track <= 24: return 1
        if track <= 30: return 2
        return 3

    def _gcr_encode(self, data):
        """Encode a byte string to GCR (4 data bytes -> 5 GCR bytes)."""
        out = bytearray()
        for i in range(0, len(data), 4):
            b = data[i:i + 4]
            bits = 0
            for byte in b:
                bits = (bits << 5) | self.GCR_TAB[byte >> 4]
                bits = (bits << 5) | self.GCR_TAB[byte & 0x0F]
            out += bits.to_bytes(5, 'big')
        return bytes(out)

    def insert_disk(self, d64):
        """Build the rotating GCR image from a D64: per track a byte stream
        of SYNC marks, GCR header blocks, gaps and GCR data blocks — exactly
        what the DOS expects to see passing under the read head."""
        bam = d64.read_sector(18, 0)
        id1, id2 = bam[0xA2], bam[0xA3]
        self._d64 = d64                  # for writing changes back
        self._dirty = set()              # tracks written since last flush
        self._motor_prev = False
        self.tracks = []
        for track in range(1, 36):
            zone = self._zone(track)
            spt = d64.SECTORS_PER_TRACK[track - 1]
            buf = bytearray()
            sync = bytearray()

            def emit(bs, is_sync=False):
                buf.extend(bs)
                sync.extend((1 if is_sync else 0,) * len(bs))

            for sector in range(spt):
                data = d64.read_sector(track, sector)
                # header block: 08 cks S T ID2 ID1 0F 0F
                cks = sector ^ track ^ id2 ^ id1
                hdr = bytes((0x08, cks, sector, track, id2, id1, 0x0F, 0x0F))
                emit(b"\xFF" * 5, is_sync=True)
                emit(self._gcr_encode(hdr))
                emit(b"\x55" * 9)
                # data block: 07 <256 bytes> cks 00 00
                dcks = 0
                for byte in data:
                    dcks ^= byte
                blk = bytes((0x07,)) + bytes(data) + bytes((dcks, 0, 0))
                emit(b"\xFF" * 5, is_sync=True)
                emit(self._gcr_encode(blk))
                emit(b"\x55" * 9)
            # pad to nominal track length with gap bytes
            pad = self.ZONE_TRACK_LEN[zone] - len(buf)
            if pad > 0:
                emit(b"\x55" * pad)
            self.tracks.append((buf, sync))
        # Disk-change: the write-protect photo sensor goes dark while the
        # disk is out of the slot — loaders watch VIA2 PB4 for exactly this
        # flicker to detect a swap. Simulate ~0.6s of "no disk in slot".
        self._wp_flicker_until = self.cpu.cycles + 600_000
        self.blocks_read = 0             # Zaehler startet pro Diskette bei 0
        self.halftrack = 36              # head parked over track 18
        self.disk_pos = 0
        self._byte_frac = 0.0
        self._head_byte = 0xFF
        self._head_sync = False
        self._prev_step_phase = self.via2.orb & 0x03
        self._prev_sync = False
        # VIA2 wiring: port A = byte under the head, PB7 = /SYNC, PB4 = not
        # write-protected.
        self.via2.port_a_in = lambda: self._head_byte
        self.via2.port_b_in = self._via2_port_b_in

    def _via2_port_b_in(self):
        v = 0xFF
        if self._head_sync:
            v &= ~0x80                   # /SYNC active (low) under a sync mark
        if self.cpu.cycles < getattr(self, "_wp_flicker_until", 0):
            v &= ~0x10                   # WP sensor dark: disk being swapped
        return v

    def _disk_tick(self, cycles):
        """Advance the rotating disk under the head and deliver byte-ready
        pulses to the CPU's Set-Overflow pin (the DOS reads with CLV/BVC *)."""
        # stepper: VIA2 PB0/PB1 phase changes move the head by half tracks
        phase = self.via2.orb & 0x03
        if phase != self._prev_step_phase:
            d = (phase - self._prev_step_phase) & 0x03
            if d == 1 and self.halftrack < 70:
                self.halftrack += 1
            elif d == 3 and self.halftrack > 2:
                self.halftrack -= 1
            self._prev_step_phase = phase
        motor = bool(self.via2.orb & self.via2.ddrb & 0x04)
        if self._motor_prev and not motor:
            self.flush_writes()           # job done: persist written tracks
        self._motor_prev = motor
        if not motor:
            return                        # motor off: disk not spinning
        track = self.halftrack >> 1
        if track < 1 or track > 35 or not self.tracks:
            return
        data, sync = self.tracks[track - 1]
        zone = self._zone(track)
        self._byte_frac += cycles / self.ZONE_CYC_PER_BYTE[zone]
        n = int(self._byte_frac)
        if n <= 0:
            return
        self._byte_frac -= n
        pos = self.disk_pos
        tl = len(data)
        if (self.via2.pcr & 0xE0) == 0xC0:
            # WRITE mode: CB2 (R/W head control) driven low — every byte
            # slot takes the VIA2 port A output register onto the track.
            # Sync marks: only runs of >=2 written $FF bytes count (legal
            # GCR data can contain a single $FF = 8 one-bits, but never the
            # 10+ one-bits of a true sync).
            val = self.via2.ora
            for _ in range(min(n, 4)):
                pos = (pos + 1) % tl
                data[pos] = val
                if val == 0xFF and data[pos - 1] == 0xFF:
                    sync[pos] = 1
                    sync[pos - 1] = 1
                else:
                    sync[pos] = 0
                self.cpu.set_flag(self.cpu.FV, True)
                self.via2._set_flag(0x02)
            self._dirty.add(track)
            self._head_sync = False
            self.disk_pos = pos
            return
        # deliver at most a few byte events; skipping is harmless in gaps
        for _ in range(min(n, 4)):
            pos = (pos + 1) % tl
            if sync[pos]:
                self._head_sync = True
            else:
                if self._head_sync:
                    # first byte after a sync mark — count data blocks for
                    # the title-bar counter (every 2nd sync is a data block)
                    self._sync_toggle = not getattr(self, '_sync_toggle', False)
                    if self._sync_toggle is False:
                        self.blocks_read += 1
                self._head_sync = False
                self._head_byte = data[pos]
                # byte-ready -> CPU SO pin: sets the 6502 overflow flag
                self.cpu.set_flag(self.cpu.FV, True)
                self.via2._set_flag(0x02)      # CA1 byte-ready flag too
        self.disk_pos = pos

    # DOS idle/job-scan loop of the stock 1541 ROM: while the PC is in here
    # with the motor off and no interrupt pending, the drive is provably
    # doing nothing — the M4 fast path skips the clock forward in one jump,
    # but never past the next VIA timer event, so every job-scheduler IRQ
    # still executes exactly like before. Any bus activity (ATN edge -> CA1
    # flag -> pending IRQ) wakes it instantly.
    IDLE_LO, IDLE_HI = 0xEBFF, 0xEC9F

    _GCR_DEC = None

    @classmethod
    def _gcr_decode_group(cls, g):
        """Decode 5 GCR bytes back into 4 data bytes (None if invalid)."""
        if cls._GCR_DEC is None:
            cls._GCR_DEC = {v: i for i, v in enumerate(cls.GCR_TAB)}
        bits = int.from_bytes(g, 'big')
        out = bytearray()
        try:
            for k in range(7, -1, -2):
                hi = cls._GCR_DEC[(bits >> (5 * (k))) & 0x1F]
                lo = cls._GCR_DEC[(bits >> (5 * (k - 1))) & 0x1F]
                out.append((hi << 4) | lo)
        except KeyError:
            return None
        return bytes(out)

    def _decode_gcr_at(self, data, pos, count):
        """Decode `count` data bytes starting at track position pos."""
        tl = len(data)
        need = (count + 3) // 4 * 5
        raw = bytes(data[(pos + i) % tl] for i in range(need))
        out = bytearray()
        for i in range(0, need, 5):
            grp = self._gcr_decode_group(raw[i:i + 5])
            if grp is None:
                return None
            out += grp
        return bytes(out[:count])

    def flush_writes(self):
        """Decode all written (dirty) GCR tracks back into sectors and save
        the D64 file — savegames become real. Called on motor stop, disk
        swap and emulator exit."""
        if not self._dirty or self._d64 is None:
            return
        written = 0
        for tno in sorted(self._dirty):
            data, sync = self.tracks[tno - 1]
            tl = len(data)
            # find sync starts (position after a sync run)
            i = 0
            last_hdr = None
            starts = [p for p in range(tl)
                      if sync[p] and not sync[(p + 1) % tl]]
            for p in starts:
                blk = self._decode_gcr_at(data, (p + 1) % tl, 4)
                if blk is None:
                    continue
                if blk[0] == 0x08:                     # header block
                    hdr = self._decode_gcr_at(data, (p + 1) % tl, 8)
                    if hdr is not None:
                        last_hdr = (hdr[3], hdr[2])    # track, sector
                elif blk[0] == 0x07 and last_hdr:      # data block
                    full = self._decode_gcr_at(data, (p + 1) % tl, 260)
                    if full is None:
                        continue
                    payload = full[1:257]
                    cks = 0
                    for b in payload:
                        cks ^= b
                    if cks == full[257]:
                        t, sct = last_hdr
                        if (1 <= t <= 35
                                and sct < self._d64.SECTORS_PER_TRACK[t - 1]):
                            self._d64.write_sector(t, sct, payload)
                            written += 1
                    last_hdr = None
        self._dirty.clear()
        if written:
            self._d64.save()
            print(f"1541: {written} Sektoren nach "
                  f"{getattr(self._d64, 'path', '?')} geschrieben")

    def sync_to(self, cpu_cycles):
        """Catch the drive up to the C64 clock (M3 fastloader timing).
        Called before every C64 instruction and — crucially — on demand from
        the $DD00 read/write hooks, so both sides of a cycle-counted 2-bit
        transfer see each other's line edges with instruction-level accuracy
        instead of batch-level lag."""
        if self._clock_base is None:
            self._clock_base = cpu_cycles - self.cpu.cycles
        target = cpu_cycles - self._clock_base
        cpu = self.cpu
        via1, via2 = self.via1, self.via2
        while cpu.cycles < target:
            if ((via1.ifr & via1.ier) or (via2.ifr & via2.ier)):
                cpu.irq_line = True
                self._idle_streak = 0
            elif (self._idle_streak >= 150
                    and self.IDLE_LO <= cpu.pc <= self.IDLE_HI
                    and not (via2.orb & via2.ddrb & 0x04)):
                # Idle fast path: jump to the next VIA event or the target,
                # whichever comes first.
                skip = target - cpu.cycles
                if via1.t1_running:
                    skip = min(skip, via1.t1_counter + 1)
                if via2.t1_running:
                    skip = min(skip, via2.t1_counter + 1)
                if via1.t2_running and not (via1.acr & 0x20):
                    skip = min(skip, via1.t2_counter + 1)
                if via2.t2_running and not (via2.acr & 0x20):
                    skip = min(skip, via2.t2_counter + 1)
                if skip > 0:
                    cpu.cycles += skip
                    via1.tick(skip)
                    via2.tick(skip)
                    continue
                cpu.irq_line = False
            else:
                cpu.irq_line = False
            before = cpu.cycles
            if not cpu.step():
                self._clock_base = None      # JAM: resync when it recovers
                break
            elapsed = cpu.cycles - before
            via1.tick(elapsed)
            via2.tick(elapsed)
            if self.tracks:
                self._disk_tick(elapsed)
            if self.IDLE_LO <= cpu.pc <= self.IDLE_HI:
                self._idle_streak += 1
            else:
                self._idle_streak = 0
        # Publish an idle horizon: while provably idle (streak proven, motor
        # off, nothing pending), the C64 side may skip calling us entirely
        # until the next VIA event — bus hooks invalidate this instantly.
        if (self._idle_streak >= 150
                and not ((via1.ifr & via1.ier) or (via2.ifr & via2.ier))
                and not (via2.orb & via2.ddrb & 0x04)):
            horizon = 1 << 20
            if via1.t1_running:
                horizon = min(horizon, via1.t1_counter + 1)
            if via2.t1_running:
                horizon = min(horizon, via2.t1_counter + 1)
            if via1.t2_running and not (via1.acr & 0x20):
                horizon = min(horizon, via1.t2_counter + 1)
            if via2.t2_running and not (via2.acr & 0x20):
                horizon = min(horizon, via2.t2_counter + 1)
            self.idle_until = (self._clock_base or 0) + cpu.cycles + horizon
        else:
            self.idle_until = 0

    def run(self, cycles):
        self._cycle_debt += cycles
        cpu = self.cpu
        via1, via2 = self.via1, self.via2
        while self._cycle_debt > 0:
            cpu.irq_line = via1.irq() or via2.irq()
            before = cpu.cycles
            if not cpu.step():
                self._cycle_debt = 0
                break
            elapsed = cpu.cycles - before
            via1.tick(elapsed)
            via2.tick(elapsed)
            if self.tracks:
                self._disk_tick(elapsed)
            self._cycle_debt -= elapsed


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
        self.data = bytearray(data)
        self.path = path

    def write_sector(self, track, sector, payload):
        """Overwrite one 256-byte sector in the image (write support)."""
        off = self.sector_offset(track, sector)
        self.data[off:off + 256] = payload

    def save(self):
        """Persist the (possibly modified) image back to its file."""
        with open(self.path, "wb") as f:
            f.write(bytes(self.data))

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

    def __init__(self, rom_dir="roms", verbose=True, cycle_accurate=False):
        # cycle_accurate=True switches from the fast instruction-batch scheduler
        # to a per-PHI2 clock (VIC -> CPU-if-bus-free -> CIAs). The batch path
        # stays the default for interactive speed; the clock path is for the
        # Lorenz timing tests / accurate BA (badline) behaviour.
        self.cycle_accurate = cycle_accurate
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
        self.vic.mem = self.mem            # lets VIC record sprite pointers/Y
        self.vic.color_ram = self.color_ram   # for per-row colour-RAM snapshots
        self.chargen_rom = bytes(chargen)
        self.cpu = CPU(self.mem)
        self.sid._cpu = self.cpu          # cycle timestamps for write queue
        self._d64 = None
        # --- 1541 drive emulation (M0: drive computer boots alongside) ---
        # Opt-in via --drive; the KERNAL trap loader stays the default path.
        self.drive = None
        self.disk_blocks = 0              # blocks served (traps or drive)
        self.disk_led_timer = 0           # frames the activity LED stays lit
        self._rom_dir = rom_dir
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
        if self.vic.ba_debt:
            # burn badline/sprite-stolen cycles: time passes, CPU frozen.
            # Sliced to <=16 cycles per step so a raster busy-wait
            # (CMP $D012/BNE — Pitstop II's colour ladder) can never leap
            # over its target line between two reads.
            d = min(self.vic.ba_debt, 16)
            self.vic.ba_debt -= d
            self.cpu.cycles += d
            self.vic.tick(d)
            self.cia1.tick(d)
            self.cia2.tick(d)
            return True
        before = self.cpu.cycles
        cur_nmi = self.cia2.irq_line
        if cur_nmi and not self.cpu._prev_nmi:
            self.cpu.nmi_pending = True
        self.cpu._prev_nmi = cur_nmi
        self.cpu.irq_line = self.cia1.irq_line or self.vic.irq_line
        if self.drive is not None and self.cpu.cycles >= self.drive.idle_until:
            self.drive.sync_to(self.cpu.cycles)
            self.iec.poll()
        ok = self.cpu.step()
        elapsed = self.cpu.cycles - before
        if elapsed > 0:
            self.vic.tick(elapsed)
            self.cia1.tick(elapsed)
            self.cia2.tick(elapsed)
            if (self.drive is not None
                    and self.cpu.cycles >= self.drive.idle_until):
                self.iec.poll()
        return ok

    def clock(self):
        # One PHI2 tick in cycle-accurate mode. Order matters: the VIC runs
        # first (it decides whether the bus is available), the CPU only advances
        # when it has the bus, then the CIAs.
        cur_nmi = self.cia2.irq_line
        if cur_nmi and not self.cpu._prev_nmi:
            self.cpu.nmi_pending = True
        self.cpu._prev_nmi = cur_nmi
        self.cpu.irq_line = self.cia1.irq_line or self.vic.irq_line
        self.vic.clock()
        self.cpu.clock(ba=self.vic.ba)
        self.cia1.clock()
        self.cia2.clock()
        return True

    def swap_disk(self, path):
        """Change the disk at runtime (drag & drop a .d64 onto the window or
        cycle with F6). Re-mounts for the trap loader and — with --drive —
        re-encodes the GCR image and flickers the write-protect sensor so
        loaders detect the change like on real hardware."""
        if self.drive is not None:
            self.drive.flush_writes()    # Aenderungen der alten Disk sichern
        try:
            self.mount_d64(path)
        except Exception as e:
            print(f"Diskwechsel fehlgeschlagen: {e}")
            return
        self.disk_blocks = 0             # FD-Zaehler pro Diskette
        name = self._d64.disk_name().decode("ascii", "replace")
        src_note = " (Laufwerk)" if self.drive is not None else " (Traps)"
        print(f"Diskette gewechselt: {path}  [{name}]{src_note}")

    def enable_drive(self):
        """Attach a true 1541 (milestone M0: the drive computer runs and
        boots its DOS to the idle loop). Requires roms/dos1541.bin."""
        import os
        path = os.path.join(self._rom_dir, "dos1541.bin")
        if os.path.exists(path):
            with open(path, "rb") as f:
                rom = f.read()
            rom_src = "roms/"
        else:
            rom = _get_embedded_rom("dos1541")
            rom_src = "eingebettet"
        if len(rom) != 16384:
            print(f"1541: DOS-ROM hat {len(rom)} Bytes (erwartet 16384)")
            return False
        self.drive = Drive(rom)
        self.iec = IecBus(self.cia2, self.drive.via1)
        # Sync-on-demand (M3): every $DD00 read or write first pulls the
        # drive up to the present C64 cycle, so cycle-counted fastloader
        # protocols see each other's edges with instruction accuracy.
        def _sync_then_read():
            self.drive.idle_until = 0
            self.drive.sync_to(self.cpu.cycles + 3)
            self.iec.poll()
            return self.iec.cia2_port_a_in()
        def _sync_before_write():
            self.drive.idle_until = 0
            self.drive.sync_to(self.cpu.cycles + 3)
            self.iec.poll()
        self.cia2.port_a_in_fn = _sync_then_read
        self.cia2.port_a_write_hook = _sync_before_write
        self.drive.via1.port_b_in = self.iec.via1_port_b_in
        # With a real drive on the bus, the KERNAL IEC shortcuts step aside —
        # device 8 now answers over the wire.
        for addr in self._KERNAL_TRAPS:
            self.cpu.traps.pop(addr, None)
        self._drive_traps_blocked = True
        if self._d64 is not None:
            self.drive.insert_disk(self._d64)
            print(f"1541: DOS-ROM geladen ({rom_src}), IEC-Bus verdrahtet, Diskette eingelegt")
        else:
            print(f"1541: DOS-ROM geladen ({rom_src}), IEC-Bus verdrahtet (keine Diskette)")
        return True

    def run(self, n_cycles):
        if self.cycle_accurate:
            self.vic._bl_defer = True
            for _ in range(n_cycles):
                self.clock()
            return True
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
        self._sid_speed_mask = speed
        name     = data[22:54].split(b"\x00", 1)[0].decode("ascii", "replace")
        author   = data[54:86].split(b"\x00", 1)[0].decode("ascii", "replace")
        released = data[86:118].split(b"\x00", 1)[0].decode("ascii", "replace")
        if version >= 2 and len(data) >= 0x78:
            flags = struct.unpack(">H", data[0x76:0x78])[0]
            sid_model_bits = (flags >> 4) & 0x03
            if sid_model_bits == 0x02:
                self.sid.set_model("8580")
            elif sid_model_bits == 0x01:
                self.sid.set_model("6581")
        payload = data[data_off:]
        if load_addr == 0:
            load_addr = payload[0] | (payload[1] << 8)
            payload = payload[2:]
        # Boot the kernal first so the C64 is in a sensible state
        if self.cpu.cycles < 2_000_000:
            self.run(3_500_000)
        # Environment depends on the format:
        #  - PSID with a play address: WE drive the player. Lean environment,
        #    I/O in, BASIC/KERNAL ROMs banked OUT ($35) — tunes routinely load
        #    their data under the ROM areas and read it back.
        #  - RSID (or play == 0): the tune brings its own interrupt handler
        #    and/or main loop and expects a REAL C64: ROMs banked in ($37),
        #    kernal IRQ chain alive, machine free-running after init.
        is_selfdriving = (data[:4] == b"RSID") or (play_addr == 0)
        self.mem.write_system_byte(Config.ADDR_PROCESSOR_PORT_REG,
                                   0x37 if is_selfdriving else 0x35)
        # Write payload
        self.mem.load_ram(load_addr, payload)
        # Call init with A = song index (0-based), interrupts disabled
        if song_num is None:
            song_num = start_song - 1
        # Multispeed: speed bit for this song = CIA-timer driven play calls
        # (rate = CIA1 timer A latch, programmed by the tune's init). Only
        # meaningful for PSID; RSIDs run their own interrupt environment.
        bit = min(song_num, 31)
        self._sid_cia = (data[:4] == b"PSID"
                         and bool((self._sid_speed_mask >> bit) & 1))
        self._sid_play_countdown = 0
        self.cpu.a = song_num & 0xFF
        self.cpu.x = 0
        self.cpu.y = 0
        self.cpu.set_flag(self.cpu.FI, not is_selfdriving)
        init_returned = self.call_routine(init_addr)
        self._sid_play_addr = play_addr
        # Park the CPU only where that's correct:
        #  - PSID (we call play each frame): always park in a JMP * idle loop,
        #    otherwise the CPU free-runs into zeroed RAM between our calls.
        #  - Self-driving tune whose init RETURNED: park too, but with
        #    interrupts ENABLED so the tune's own IRQ handler keeps playing.
        #  - Self-driving tune whose init did NOT return (it IS the player's
        #    main loop): leave the PC alone — the timeout just means the tune
        #    is running, and yanking the PC out of the loop kills the music.
        load_end = load_addr + len(payload)
        self._sid_idle_addr = 0
        for cand in (0x03C0, 0x02A7, 0xFFF9):
            if cand == 0xFFF9 and is_selfdriving:
                continue                      # ROM banked in there under $37
            if not (load_addr <= cand + 2 and cand <= load_end):
                self._sid_idle_addr = cand
                break
        ia = self._sid_idle_addr
        if ia and (not is_selfdriving or init_returned):
            self.mem.load_ram(ia, bytes((0x4C, ia & 0xFF, (ia >> 8) & 0xFF)))
            self.cpu.pc = ia
            if is_selfdriving:
                self.cpu.set_flag(self.cpu.FI, False)   # tune plays via IRQ
        return {"format": data[:4].decode("ascii"), "version": version,
                "load": load_addr, "init": init_addr, "play": play_addr,
                "songs": songs, "start_song": start_song,
                "name": name, "author": author, "released": released}

    def sid_play_tick(self):
        """If a SID tune is active, call its Play routine once (one frame).
        No-op for CIA-driven multispeed tunes: sid_run() schedules those."""
        addr = getattr(self, "_sid_play_addr", 0)
        if addr and not getattr(self, "_sid_cia", False):
            self.call_routine(addr)
            if self._sid_idle_addr:
                self.cpu.pc = self._sid_idle_addr    # back to the idle loop

    def sid_run(self, n_cycles):
        """Run n_cycles; for CIA-timer (multispeed) PSIDs, interleave play
        calls at the rate given by the CIA1 timer A latch — read live, so
        tunes may retune their speed mid-song. The play routine's own cycles
        count against the budget (at 4x+ they matter). Thanks to the SID's
        timestamped write queue, each call's register writes land sample-
        accurately inside the frame."""
        if (not getattr(self, "_sid_cia", False)
                or not getattr(self, "_sid_play_addr", 0)):
            return self.run(n_cycles)
        budget = n_cycles
        while budget > 0:
            if self._sid_play_countdown <= 0:
                c0 = self.cpu.cycles
                self.call_routine(self._sid_play_addr)
                if self._sid_idle_addr:
                    self.cpu.pc = self._sid_idle_addr
                used = self.cpu.cycles - c0
                per = self.cia1.timer_a_latch
                if not (500 <= per <= 30000):
                    per = 16421              # KERNAL default: ~60 Hz
                self._sid_play_countdown = max(per - used, 1)
                budget -= used
                continue
            step = min(budget, self._sid_play_countdown)
            self.run(step)
            self._sid_play_countdown -= step
            budget -= step

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
        if self.drive is None:
            for addr, name in self._KERNAL_TRAPS.items():
                self.cpu.traps[addr] = getattr(self, name)
        elif not self._is_tape:
            self.drive.insert_disk(self._d64)
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
        if self.drive is None:
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
            self.disk_blocks += (len(data) + 253) // 254
            self.disk_led_timer = 30
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
                    self.disk_blocks += 1
                    self.disk_led_timer = 15
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
            if data is not None:
                self.disk_blocks += (len(data) + 253) // 254
                self.disk_led_timer = 30
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
            self.disk_blocks += (len(file_data) + 253) // 254
            self.disk_led_timer = 30
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
        self.sid._cpu = self.cpu
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


# ---------------------------------------------------------------------------
# Minimal dependency-free PNG I/O (stdlib zlib + numpy only). Used by the VIC
# screenshot test; the emulator's own frames are written as 8-bit truecolour
# PNGs and the VICE reference PNGs are decoded for comparison.
# ---------------------------------------------------------------------------

def _png_read_rgb(path):
    """Decode a non-interlaced PNG to an (H, W, 3) uint8 numpy array. Supports
    colour types 0/2/3/4/6 at bit depth 8, plus sub-byte indexed/greyscale."""
    import numpy as np
    d = open(path, "rb").read()
    if d[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"not a PNG: {path}")
    pos = 8
    W = H = bd = ct = None
    idat = bytearray()
    plte = None
    while pos < len(d):
        ln = int.from_bytes(d[pos:pos + 4], "big")
        typ = d[pos + 4:pos + 8]
        chunk = d[pos + 8:pos + 8 + ln]
        pos += 12 + ln
        if typ == b"IHDR":
            W = int.from_bytes(chunk[0:4], "big")
            H = int.from_bytes(chunk[4:8], "big")
            bd, ct = chunk[8], chunk[9]
            if chunk[12] != 0:
                raise ValueError("interlaced PNG not supported")
        elif typ == b"PLTE":
            plte = np.frombuffer(chunk, np.uint8).reshape(-1, 3)
        elif typ == b"IDAT":
            idat += chunk
        elif typ == b"IEND":
            break
    raw = zlib.decompress(bytes(idat))
    nch = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[ct]
    stride = (W * nch * bd + 7) // 8
    bpp = max(1, (nch * bd) // 8)
    out = np.zeros((H, stride), np.uint8)
    prev = np.zeros(stride, np.int32)
    p = 0
    for y in range(H):
        ft = raw[p]; p += 1
        line = np.frombuffer(raw[p:p + stride], np.uint8).astype(np.int32).copy()
        p += stride
        if ft == 1:
            for i in range(bpp, stride):
                line[i] = (line[i] + line[i - bpp]) & 255
        elif ft == 2:
            line = (line + prev) & 255
        elif ft == 3:
            for i in range(stride):
                a = line[i - bpp] if i >= bpp else 0
                line[i] = (line[i] + ((a + prev[i]) >> 1)) & 255
        elif ft == 4:
            for i in range(stride):
                a = line[i - bpp] if i >= bpp else 0
                b = prev[i]
                c = prev[i - bpp] if i >= bpp else 0
                q = a + b - c
                pa, pb, pc = abs(q - a), abs(q - b), abs(q - c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[i] = (line[i] + pr) & 255
        out[y] = line.astype(np.uint8)
        prev = out[y].astype(np.int32)
    if bd == 8:
        px = out.reshape(H, W, nch)
        if ct in (2, 6):
            return px[:, :, :3].copy()
        if ct == 3:
            return plte[px[:, :, 0]]
        g = px[:, :, 0]
        return np.stack([g, g, g], -1)
    # sub-byte depths (indexed / greyscale), MSB first
    per = 8 // bd
    mask = (1 << bd) - 1
    vals = np.zeros((H, W), np.uint8)
    for y in range(H):
        xi = 0
        for byte in out[y]:
            for k in range(per):
                if xi >= W:
                    break
                vals[y, xi] = (byte >> (8 - bd * (k + 1))) & mask
                xi += 1
    if ct == 3:
        return plte[vals]
    scale = 255 // mask
    g = (vals * scale).astype(np.uint8)
    return np.stack([g, g, g], -1)


def _png_write_rgb(path, arr):
    """Write an (H, W, 3) uint8 array as an 8-bit truecolour PNG."""
    import numpy as np
    a = arr.astype(np.uint8)
    H, W, _ = a.shape

    def _chunk(typ, data):
        body = typ + data
        return (len(data).to_bytes(4, "big") + body
                + (zlib.crc32(body) & 0xFFFFFFFF).to_bytes(4, "big"))

    ihdr = (W.to_bytes(4, "big") + H.to_bytes(4, "big")
            + bytes([8, 2, 0, 0, 0]))
    raw = bytearray()
    for y in range(H):
        raw.append(0)                       # filter type 0 (none)
        raw += a[y].tobytes()
    png = (b"\x89PNG\r\n\x1a\n"
           + _chunk(b"IHDR", ihdr)
           + _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
           + _chunk(b"IEND", b""))
    open(path, "wb").write(png)


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
    # Render right after the visible display area rather than at frame end.
    # Double-buffering games (e.g. The Goonies) redraw the just-shown screen
    # during the vblank that follows, so rendering at frame end would capture
    # that redraw and flicker. Splitting the frame so we render at ~raster 251
    # captures what was actually on screen during the visible area.
    RENDER_RASTER = 251

    def __init__(self, system, scale=2, target_hz=50, headless=False):
        import numpy as np
        self.np = np
        self.system = system
        self.scale = scale
        self.target_hz = target_hz
        self.headless = headless
        self.pygame = None
        if not headless:
            import pygame
            self.pygame = pygame
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
        if not headless:
            self.key_map = _build_key_map(self.pygame)
        self._keys_down = set()    # host pygame keycodes currently pressed
        # The character each held key produced (from the KEYDOWN event's
        # unicode). Punctuation is mapped by CHARACTER rather than key position,
        # so it works regardless of the host keyboard layout (QWERTZ, AZERTY…):
        # you type ':' the way your keyboard makes ':', and the emulator presses
        # the right C64 keys — even though on the C64 the colon is its own key.
        self._key_chars = {}
        SH = (1, 7)                # left shift on the C64 matrix (col, row)
        self._c64_symbols = {
            "!": [SH, (7, 0)], '"': [SH, (7, 3)], "#": [SH, (1, 0)],
            "$": [SH, (1, 3)], "%": [SH, (2, 0)], "&": [SH, (2, 3)],
            "'": [SH, (3, 0)], "(": [SH, (3, 3)], ")": [SH, (4, 0)],
            ":": [(5, 5)], ";": [(6, 2)], ",": [(5, 7)], ".": [(5, 4)],
            "/": [(6, 7)], "?": [SH, (6, 7)], "<": [SH, (5, 7)],
            ">": [SH, (5, 4)], "[": [SH, (5, 5)], "]": [SH, (6, 2)],
            "=": [(6, 5)], "+": [(5, 0)], "-": [(5, 3)],
            "@": [(5, 6)], "*": [(6, 1)], "\u00a3": [(6, 0)],   # £
        }
        # Which control port the numeric-keypad joystick drives: 0 = port 1
        # ($DC01), 1 = port 2 ($DC00). Toggle at runtime with keypad 0.
        # Default is port 2 — the port most C64 games read (Elite, etc.), and
        # the one that does NOT share row lines with the keyboard, so the
        # keypad joystick can't "ghost" into menu keys. A few games use port 1
        # (e.g. Bruce Lee reads $DC01); press keypad 0 to switch for those.
        self._joy_port = 1
        self.disk_list = []
        self._disk_idx = 0
        self.shown_fps = 0.0
        self.warp = False    # True = run as fast as possible (no host frame cap)

        # Audio output — pygame.mixer streaming via Channel.queue()
        self.audio_enabled = False
        self.samples_per_frame = system.sid.SAMPLE_RATE // target_hz
        if not headless:
            try:
                self.pygame.mixer.init(frequency=system.sid.SAMPLE_RATE,
                                       size=-16, channels=1, buffer=4096)
                self.audio_channel = self.pygame.mixer.Channel(0)
                self.audio_enabled = True
                # One frame of silence, used to re-prime the channel after an
                # underrun so playback regains ~2 chunks of lead instead of
                # running chunk-to-mouth (which turns every host hiccup into
                # an audible dropout).
                z = self.np.zeros((self.samples_per_frame, 2), self.np.int16)
                self._silence_sound = self.pygame.sndarray.make_sound(z)
            except self.pygame.error as ex:
                print(f"Audio disabled: {ex}")

    def _key_event(self, host_key, pressed, char=None):
        """
        Update the CIA1 keyboard matrix from a host pygame keystroke.
        UP and LEFT are virtual on the C64 — they're SHIFT + CRSR-DOWN
        and SHIFT + CRSR-RIGHT respectively. We track which host keys are
        physically down and rebuild the matrix each time so the synthesised
        SHIFT doesn't get stripped when the user is also holding real SHIFT.
        `char` is the unicode character the key produced (KEYDOWN only), used
        for layout-independent punctuation mapping.
        """
        if pressed:
            self._keys_down.add(host_key)
            if char and len(char) == 1 and char in self._c64_symbols:
                self._key_chars[host_key] = char
            else:
                self._key_chars.pop(host_key, None)
        else:
            self._keys_down.discard(host_key)
            self._key_chars.pop(host_key, None)
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
            elif key in (p.K_KP5, p.K_KP_ENTER, p.K_RCTRL): joy |= 1 << 4   # fire
        # _joy_port: 0 = port 1 only, 1 = port 2 only, 2 = both ports.
        js = self.system.cia1.joystick_state
        if self._joy_port == 2:
            js[0] = joy
            js[1] = joy
        else:
            js[self._joy_port] = joy
            js[1 - self._joy_port] = 0
        # Keyboard matrix. The PC arrow keys map to the authentic C64 cursor
        # keys: the real machine had only TWO cursor keys — CRSR↕ (0,7) and
        # CRSR⇄ (0,2) — with the up/left directions produced by holding SHIFT.
        #
        # Punctuation is mapped by the CHARACTER the key produced (self.
        # _key_chars), not by key position, so ':' / '"' / etc. work on any
        # host layout. When a symbol key is active, the symbol table already
        # encodes the C64 shift it needs, so we drop the host shift for it.
        active_syms = [self._key_chars[k] for k in self._keys_down
                       if k in self._key_chars]
        suppress_shift = any(self._c64_symbols[c][0] == (1, 7)
                             for c in active_syms) or bool(active_syms)
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
            elif key in self._key_chars:
                for pos in self._c64_symbols[self._key_chars[key]]:
                    mat.add(pos)               # character-mapped punctuation
            elif key in (p.K_LSHIFT, p.K_RSHIFT) and suppress_shift:
                continue                       # shift handled by symbol map
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
        render_bank = self.system.mem.vic_bank()
        cache = {}
        masks = np.empty((25, 40, 8, 8), dtype=np.uint8)
        for r in range(25):
            # Font base = row's OWN bank (captured when the row was fetched) +
            # its char base. Honors mid-frame $DD00 bank switches so a status
            # line in one bank over a playfield in another gets the right font.
            bank = vic.row_mode_bank[r]
            if bank == 0xFF:            # row never fetched -> render-time bank
                bank = render_bank
            cb_sel = (vic.row_mode_d018[r] >> 1) & 0x07
            key = (bank, cb_sel)
            cg = cache.get(key)
            if cg is None:
                cg = self._chargen_for(bank, cb_sel)
                cache[key] = cg
            masks[r] = cg[codes[r]]
        return masks

    def _render_charmode_multicolor(self, rows, masks, color_ram, d021_row,
                                    d022_row, d023_row):
        """
        Render text rows `rows` (a range within 0..24) in multicolor character
        mode (D016 bit 4 set for these rows).

        Per character cell the colour RAM nibble decides the sub-mode:
          * bit 3 = 0  -> standard hi-res, but only the low 3 colour bits are
                          available (8 colours); fg = colour & 7, bg = D021.
          * bit 3 = 1  -> multicolor: horizontal pixel pairs (double width)
                          select one of four colours by their 2-bit value:
                              00 = background      (D021)
                              01 = background#1    (D022)
                              10 = background#2    (D023)
                              11 = character col   (colour RAM & 7)

        `masks` is the full (25,40,8,8) per-row character bitmap (built with
        the correct per-row font); d021_row/d022_row/d023_row are (25,) arrays
        of the background colours active at each row's raster line, so raster
        splits that recolour the backdrop mid-frame render correctly.
        Returns (pixels[h,320,3], bitmap[h,320]) for h = len(rows)*8.
        """
        np = self.np
        pal = self._palette
        r0, r1 = rows.start, rows.stop
        nr = r1 - r0
        masks = masks[r0:r1]
        color_ram = color_ram[r0:r1]
        d021c = d021_row[r0:r1, None]                        # (nr,1)
        d022c = d022_row[r0:r1, None]
        d023c = d023_row[r0:r1, None]

        cell_col = (color_ram & 0x07)                       # (nr,40)
        mc_cell = (color_ram & 0x08) != 0                   # (nr,40) bool

        # --- multicolor interpretation: 2-bit pairs, doubled horizontally ---
        pairs = masks.reshape(nr, 40, 8, 4, 2)
        twobit = (pairs[..., 0] << 1) | pairs[..., 1]       # (nr,40,8,4) values 0..3
        twobit = np.repeat(twobit, 2, axis=3)               # (nr,40,8,8) double-wide

        # colour index per pixel for multicolor cells, via per-cell lookup table
        choices = np.stack([                                # (nr,40,4)
            np.broadcast_to(d021c, (nr, 40)).astype(np.uint8),
            np.broadcast_to(d022c, (nr, 40)).astype(np.uint8),
            np.broadcast_to(d023c, (nr, 40)).astype(np.uint8),
            cell_col.astype(np.uint8),
        ], axis=2)
        choices_b = np.broadcast_to(choices[:, :, None, None, :], (nr, 40, 8, 8, 4))
        colidx_mc = np.take_along_axis(choices_b, twobit[..., None], axis=4)[..., 0]

        # colour index per pixel for hi-res cells (bg where bit clear)
        colidx_hi = np.where(masks.astype(bool),
                             cell_col[:, :, None, None].astype(np.uint8),
                             d021_row[r0:r1, None, None, None].astype(np.uint8))

        mc_b = mc_cell[:, :, None, None]
        colidx = np.where(mc_b, colidx_mc, colidx_hi)       # (nr,40,8,8)

        # foreground mask for sprite priority / collisions
        fg_mc = twobit >= 2
        fg_hi = masks.astype(bool)
        fg = np.where(mc_b, fg_mc, fg_hi)                   # (nr,40,8,8)

        colidx = colidx.transpose(0, 2, 1, 3).reshape(nr * 8, 320)
        bitmap = fg.transpose(0, 2, 1, 3).reshape(nr * 8, 320).astype(np.uint8)
        pixels = pal[colidx].astype(np.uint8)
        return pixels, bitmap

    def _render_charmode_hires(self, rows, masks, color_ram, d021_row):
        """
        Render text rows `rows` in standard hi-res character mode: a set bit
        is the cell's colour-RAM colour, a clear bit is $D021 (per row).
        Returns (pixels[h,320,3], bitmap[h,320]) for h = len(rows)*8.
        """
        np = self.np
        r0, r1 = rows.start, rows.stop
        nr = r1 - r0
        m = masks[r0:r1]
        bitmap = m.transpose(0, 2, 1, 3).reshape(nr * 8, 320)
        fg_colors = np.repeat(np.repeat(color_ram[r0:r1], 8, axis=0), 8, axis=1)
        fg_rgb = self._palette[fg_colors]
        bg_rgb = self._palette[np.repeat(d021_row[r0:r1], 8)][:, None, :]
        pixels = np.where(bitmap[:, :, None], fg_rgb, bg_rgb).astype(np.uint8)
        return pixels, bitmap.astype(np.uint8)

    def _render_bitmap_rows(self, rows, d018, mcm, color_ram, d021_rows):
        """
        Render a contiguous span of character rows in VIC bitmap mode (BMM
        set for these rows). `rows` is a range of char-row indices (0..24)
        that all share the same $D018 bases; `mcm` selects multicolor.
        Returns (pixels[h,320,3], mask[h,320]) for those rows, h = len(rows)*8.

        Hi-res bitmap (mcm=0): each 8x8 cell has two colours from the video
        matrix byte — high nibble = set-pixel colour, low nibble = clear-pixel.
        Multicolor bitmap (mcm=1): 2-bit pixels (double width): 00=$D021,
        01=matrix high nibble, 10=matrix low nibble, 11=colour-RAM nibble.

        $D018: bit 3 selects the 8 KB bitmap base within the VIC bank; bits 4-7
        select the video-matrix (colour) base. Fetches go through the VIC's
        view of memory (read_vic_block), so the chargen-ROM shadow behaves as
        on hardware and matches the collision logic byte-for-byte.
        """
        np = self.np
        pal = self._palette
        mem = self.system.mem
        bmp_rel = ((d018 >> 3) & 1) * 0x2000
        vm_rel  = ((d018 >> 4) & 0x0F) * 0x400
        r0 = rows[0]
        nrows = len(rows)
        ncells = nrows * 40
        raw = np.frombuffer(
            mem.read_vic_block(bmp_rel + r0 * 320, ncells * 8),
            dtype=np.uint8).reshape(nrows, 40, 8)
        vm = np.frombuffer(
            mem.read_vic_block(vm_rel + r0 * 40, ncells),
            dtype=np.uint8).reshape(nrows, 40)
        bits = np.unpackbits(raw.reshape(ncells, 8), axis=1).reshape(nrows, 40, 8, 8)

        if not mcm:                                # hi-res bitmap
            fg = pal[(vm >> 4) & 0x0F]             # (nrows,40,3)
            bg = pal[vm & 0x0F]
            px = np.where(bits[..., None].astype(bool),
                          fg[:, :, None, None, :], bg[:, :, None, None, :])
            mask = bits
        else:                                      # multicolor bitmap
            d021 = d021_rows[:, None]                        # (nrows,1) per-row bg
            pb = bits.reshape(nrows, 40, 8, 4, 2)
            twobit = (pb[..., 0] << 1) | pb[..., 1]           # (nrows,40,8,4)
            twobit = np.repeat(twobit, 2, axis=3)             # (nrows,40,8,8)
            cram = color_ram[rows.start:rows.stop] & 0x0F     # (nrows,40)
            choices = np.stack([
                np.broadcast_to(d021, (nrows, 40)).astype(np.uint8),
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
        # Steady state: previous chunk playing, this one queued (~2 frames of
        # lead). When the channel has drained (startup or a host hiccup ate
        # our lead), re-prime with one silence chunk BEFORE the real audio:
        # that restores the lead so the next small hiccup doesn't cause an
        # audible gap — a drained channel fed chunk-to-mouth turns every
        # scheduling wobble into a dropout.
        if not self.audio_channel.get_busy():
            self.audio_channel.play(self._silence_sound)
            self.audio_channel.queue(sound)
        elif self.audio_channel.get_queue() is None:
            self.audio_channel.queue(sound)
        # else: queue full, drop this frame's audio (we're ahead, e.g. warp)

    def step_frame(self):
        """Advance one full frame worth of cycles, but render right after the
        visible display area (RENDER_RASTER) rather than at frame end, so
        double-buffered games don't flicker. Total cycles run == CYCLES_PER_FRAME."""
        vic = self.system.vic
        lines1 = (self.RENDER_RASTER - vic.raster) % vic.LINES_PER_FRAME
        if lines1 == 0:
            lines1 = vic.LINES_PER_FRAME
        cyc1 = lines1 * vic.CYCLES_PER_LINE
        self.system.sid_run(cyc1)
        if self.audio_enabled:
            self._push_audio()
        self.render_frame()
        self.system.sid_run(self.CYCLES_PER_FRAME - cyc1)

    def _compose_pixels(self):
        """Build the 200x320x3 inner display as a numpy array (no pygame) and
        return (pixels, border_index). Shared by the windowed renderer and the
        head-less render_to_array()."""
        np = self.np
        vic = self.system.vic
        mem = self.system.mem
        dr = vic.display_regs          # latched mid-frame (raster-split safe)
        bg_color   = dr[0x21] & 0x0F
        border     = dr[0x20] & 0x0F

        # --- Background (text mode) ---
        # Honor VIC bank + $D018 video matrix base for screen RAM lookup.
        # Screen + colour RAM come from the per-row snapshots the VIC took as
        # the beam passed each character row (see Vic.tick). This reflects what
        # was actually on each line when it was drawn, so a scroller that copies
        # screen RAM mid-frame renders cleanly instead of tearing. The snapshot
        # already used each row's active $D018 base, so raster splits that change
        # the screen/font base mid-frame (The Hobbit, Elite) still come out right.
        nld = vic.LINES_PER_FRAME
        screen_ram = np.frombuffer(bytes(vic.line_screen),
                                   dtype=np.uint8).reshape(25, 40)
        color_ram = np.frombuffer(bytes(vic.line_color),
                                  dtype=np.uint8).reshape(25, 40) & 0x0F

        # Background colours ($D021/$D022/$D023) active at each character row's
        # raster line, so raster splits that recolour the backdrop mid-frame
        # (e.g. Exploding Fist's sky/ground bands) render each band correctly
        # rather than using one latched value.
        ld21, ld22, ld23 = vic.line_d021, vic.line_d022, vic.line_d023
        d021_row = np.empty(25, dtype=np.uint8)
        d022_row = np.empty(25, dtype=np.uint8)
        d023_row = np.empty(25, dtype=np.uint8)
        for r in range(25):
            raster = (self.FIRST_DISPLAY_LINE + r * 8 + 4) % nld
            d021_row[r] = ld21[raster] & 0x0F
            d022_row[r] = ld22[raster] & 0x0F
            d023_row[r] = ld23[raster] & 0x0F

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

        # --- Unified per-row mode dispatch ---
        # Each text row's graphics mode comes from Vic.row_gfx_mode() — the
        # SAME canonical decision the $D01F collision logic uses. Contiguous
        # rows with equal mode (and, for bitmap, equal $D018 bases) render as
        # one band. This handles split screens (Elite: bitmap 3D view over a
        # text dashboard; MC playfield over a hi-res status line) and, by
        # construction, keeps renderer and collision in agreement.
        modes = [vic.row_gfx_mode(r) for r in range(25)]    # (bmm, mcm, d018)
        pixels = np.empty((200, 320, 3), dtype=np.uint8)
        bitmap = np.empty((200, 320), dtype=np.uint8)
        r = 0
        while r < 25:
            bmm, mcm, d018 = modes[r]
            end = r + 1
            while end < 25:
                b2, m2, d2 = modes[end]
                if b2 != bmm or m2 != mcm:
                    break
                if bmm and d2 != d018:      # bitmap bands need equal bases
                    break
                end += 1
            rows = range(r, end)
            if bmm:
                rp, rm = self._render_bitmap_rows(rows, d018, mcm, color_ram,
                                                  d021_row[r:end])
            elif mcm:
                rp, rm = self._render_charmode_multicolor(
                    rows, masks, color_ram, d021_row, d022_row, d023_row)
            else:
                rp, rm = self._render_charmode_hires(rows, masks, color_ram,
                                                     d021_row)
            pixels[r * 8:end * 8] = rp
            bitmap[r * 8:end * 8] = rm
            r = end
        # --- Per-line display remap (badline / FLD / idle) ---
        # The 25-row grid above is the canonical row content; the display-logic
        # records now say WHICH row line and the beam actually showed on every
        # raster line. In the normal case this is the identity and costs one
        # comparison; with FLD the rows are displaced downward and the gap
        # shows the idle pattern; with DEN off (or outside display state) the
        # whole area is idle. Idle lines display the byte at $3FFF ($39FF in
        # ECM) with black foreground over the line's $D021 — those set bits
        # are real foreground for sprite priority and $D01F collision.
        lt = vic.line_text_row
        lrc = vic.line_rc
        lid = vic.line_idle
        src = np.empty(200, dtype=np.intp)
        idle_lines = []
        for sy in range(200):
            rr = sy + 51
            if lid[rr]:
                idle_lines.append(sy)
                src[sy] = 0
            else:
                src[sy] = lt[rr] * 8 + lrc[rr]
        if idle_lines or not np.array_equal(src, np.arange(200)):
            pixels = pixels[src].copy()
            bitmap = bitmap[src].copy()
            for sy in idle_lines:
                rr = sy + 51
                byte = mem.read_vic(0x39FF if (vic.line_d011[rr] & 0x40)
                                    else 0x3FFF)
                brow = np.tile(np.unpackbits(np.array([byte], np.uint8)), 40)
                bitmap[sy] = brow
                bg = self._palette[vic.line_d021[rr] & 0x0F]
                prow = np.where(brow[:, None].astype(bool),
                                np.zeros(3, np.uint8), bg).astype(np.uint8)
                pixels[sy] = prow
        # Keep the frame's foreground mask for verify_foreground(): the
        # enforcement tool that asserts renderer and collision agree.
        self._last_fg_bitmap = bitmap
        # Mid-line $D021 raster bars on background pixels (colour only —
        # foreground mask and collision are unaffected).
        if vic._d021_splits:
            self._apply_d021_splits_inner(pixels, bitmap)

        # --- Sprites ---
        # bitmap (200, 320) is the foreground mask used for priority + collisions.
        # sprite_occupancy: per-pixel which sprite (bit 0..7) covers each pixel
        sprite_occupancy = np.zeros((200, 320), dtype=np.uint8)
        # Sprites are drawn from the canonical per-line records produced by the
        # sprite display sequencer in Vic.tick(): line_spr_row says which sprite
        # row the beam displayed on every raster line, and the per-line
        # attribute recordings say with which X/pointer/colour/MC/expansion/
        # priority. Multiplexing (Y and pointer rewritten mid-frame to reuse a
        # hardware sprite) falls out of this naturally — the sequencer simply
        # starts a new 0..20 row walk at each Y match — as do mid-sprite
        # attribute splits (colour/expansion/priority changed per raster zone).
        # Consecutive lines with identical attributes render as one numpy block
        # (fancy-indexed by their recorded row numbers, which also encodes
        # Y-expansion doubling), so ordinary games still cost one blit per
        # sprite. Render in REVERSE order so sprite 0 lands on top of sprite 7
        # (lower sprite number = higher hardware priority).
        lrow = vic.line_spr_row
        lx = vic.line_spr_x
        lp = vic.line_spr_ptr
        lmsb = vic.line_spr_msb
        lcol = vic.line_spr_col
        l1c = vic.line_d01c
        l1d = vic.line_d01d
        l1b = vic.line_d01b
        l25 = vic.line_d025
        l26 = vic.line_d026
        lbank = vic.line_spr_bank
        decode_cache = {}
        for s in range(7, -1, -1):
            sy = 0
            while sy < 200:
                r = sy + 51
                if lrow[r * 8 + s] == 0xFF:
                    sy += 1
                    continue
                a0 = (lx[r * 8 + s] | (((lmsb[r] >> s) & 1) << 8),
                      lp[r * 8 + s],
                      lcol[r * 8 + s] & 0x0F,
                      (l1c[r] >> s) & 1,
                      (l1d[r] >> s) & 1,
                      (l1b[r] >> s) & 1,
                      l25[r] & 0x0F,
                      l26[r] & 0x0F,
                      lbank[r])
                rows = [lrow[r * 8 + s]]
                end = sy + 1
                while end < 200:
                    rr = end + 51
                    if lrow[rr * 8 + s] == 0xFF:
                        break
                    an = (lx[rr * 8 + s] | (((lmsb[rr] >> s) & 1) << 8),
                          lp[rr * 8 + s],
                          lcol[rr * 8 + s] & 0x0F,
                          (l1c[rr] >> s) & 1,
                          (l1d[rr] >> s) & 1,
                          (l1b[rr] >> s) & 1,
                          l25[rr] & 0x0F,
                          l26[rr] & 0x0F,
                          lbank[rr])
                    if an != a0:
                        break
                    rows.append(lrow[rr * 8 + s])
                    end += 1
                self._render_sprite_run(s, pixels, bitmap, sprite_occupancy,
                                        sy, rows, a0, decode_cache)
                sy = end
        # Sprite-sprite collision ($D01E) is maintained by the VIC during
        # emulation (Vic._collide_at_raster) from the same per-line records,
        # so the latch is correct whenever the game polls it rather than only
        # when a frame happens to be composed for display.

        # --- Vertical border overlay ---
        # Lines where the vertical border flip-flop is set are covered by the
        # border colour — over graphics AND sprites (the border has priority
        # over everything). With DEN off the flip-flop never opens, which is
        # how blanked loading screens actually look; RSEL=0 covers 4 lines at
        # top and bottom. In the normal 25-row case no line inside the window
        # is bordered, so this costs nothing.
        for sy in range(200):
            rr = sy + 51
            if vic.line_vborder[rr]:
                pixels[sy] = self._palette[vic.line_d020[rr] & 0x0F]

        return pixels, border

    def _d021_row_colors(self, r):
        """(320,3) background colour row for raster r, honouring recorded
        mid-line $D021 splits. Cycle→pixel mapping: x = (cycle-14)*8."""
        np = self.np
        vic = self.system.vic
        base = self._palette[vic.line_d021[r] & 0x0F]
        segs = vic._d021_splits.get(r)
        row = np.empty((320, 3), np.uint8)
        row[:] = base
        if segs:
            for cyc, col in segs:
                x = max(0, min(320, (cyc - 14) * 8))
                row[x:] = self._palette[col]
        return row

    def _apply_d021_splits_inner(self, pixels, bitmap):
        """Recolour flat background pixels of playfield lines that had
        mid-line $D021 writes. Only pixels that are (a) not foreground and
        (b) currently the line's base background colour are touched, so
        glyph/bitmap art and multicolour intermediates stay intact."""
        np = self.np
        vic = self.system.vic
        for r, segs in vic._d021_splits.items():
            sy = r - 51
            if not (0 <= sy < 200) or vic.line_vborder[r]:
                continue
            base = self._palette[vic.line_d021[r] & 0x0F]
            is_bg = (bitmap[sy] == 0) & (pixels[sy] == base).all(axis=1)
            if not is_bg.any():
                continue
            row = self._d021_row_colors(r)
            pixels[sy] = np.where(is_bg[:, None], row, pixels[sy])

    def _compose_canvas(self):
        """Compose the full 384x272 frame: per-line border colours, the inner
        display window, and — where the vertical border flip-flop was tricked
        open (RSEL flip on the compare line) — idle graphics and SPRITES in
        the top/bottom border areas. The side borders stay closed (horizontal
        opening is cycle-exact territory)."""
        np = self.np
        vic = self.system.vic
        mem = self.system.mem
        pixels, border = self._compose_pixels()
        h = self.SCREEN_H + 2 * self.BORDER_Y          # 272
        w = self.SCREEN_W + 2 * self.BORDER_X          # 384
        r_first = 51 - self.BORDER_Y                   # raster of canvas row 0
        canvas = np.empty((h, w, 3), np.uint8)
        # Per-line border colour for every canvas row (raster bars for free).
        l20 = np.frombuffer(bytes(vic.line_d020), dtype=np.uint8)
        canvas[:, :] = self._palette[
            l20[r_first:r_first + h] & 0x0F][:, None, :]
        canvas[self.BORDER_Y:self.BORDER_Y + self.SCREEN_H,
               self.BORDER_X:self.BORDER_X + self.SCREEN_W] = pixels
        # Opened top/bottom border: idle pattern + sprites in the centre.
        lvb = vic.line_vborder
        for r0, r1 in ((r_first, 51), (251, r_first + h)):
            open_rs = [r for r in range(r0, r1) if not lvb[r]]
            if not open_rs:
                continue
            n = r1 - r0
            buf = canvas[r0 - r_first:r1 - r_first,
                         self.BORDER_X:self.BORDER_X + 320]
            fg = np.zeros((n, 320), np.uint8)
            for r in open_rs:
                byte = mem.read_vic(0x39FF if (vic.line_d011[r] & 0x40)
                                    else 0x3FFF)
                bits = np.tile(np.unpackbits(
                    np.array([byte], np.uint8)), 40)
                fg[r - r0] = bits
                bgrow = self._d021_row_colors(r)
                buf[r - r0] = np.where(bits[:, None].astype(bool),
                                       np.zeros(3, np.uint8), bgrow)
            self._border_sprite_pass(buf, fg, r0, r1, set(open_rs))
        return canvas

    def _border_sprite_pass(self, buf, fg, r0, r1, open_set):
        """Render sprites into an opened border region. `buf` is the region's
        centre-320px pixel buffer (rows = rasters r0..r1), `fg` the idle
        foreground mask used for sprite priority. Consumes the same canonical
        per-line sprite records as the main pass."""
        np = self.np
        vic = self.system.vic
        lrow = vic.line_spr_row
        lx = vic.line_spr_x
        lp = vic.line_spr_ptr
        lmsb = vic.line_spr_msb
        lcol = vic.line_spr_col
        l1c = vic.line_d01c
        l1d = vic.line_d01d
        l1b = vic.line_d01b
        l25 = vic.line_d025
        l26 = vic.line_d026
        lbank = vic.line_spr_bank
        occ = np.zeros((r1 - r0, 320), np.uint8)
        cache = {}

        def attrs(rr, s):
            return (lx[rr * 8 + s] | (((lmsb[rr] >> s) & 1) << 8),
                    lp[rr * 8 + s],
                    lcol[rr * 8 + s] & 0x0F,
                    (l1c[rr] >> s) & 1,
                    (l1d[rr] >> s) & 1,
                    (l1b[rr] >> s) & 1,
                    l25[rr] & 0x0F,
                    l26[rr] & 0x0F,
                    lbank[rr])

        for s in range(7, -1, -1):
            r = r0
            while r < r1:
                if r not in open_set or lrow[r * 8 + s] == 0xFF:
                    r += 1
                    continue
                a0 = attrs(r, s)
                rows = [lrow[r * 8 + s]]
                end = r + 1
                while (end < r1 and end in open_set
                        and lrow[end * 8 + s] != 0xFF
                        and attrs(end, s) == a0):
                    rows.append(lrow[end * 8 + s])
                    end += 1
                self._render_sprite_run(s, buf, fg, occ,
                                        r - r0, rows, a0, cache)
                r = end

    def render_to_array(self):
        """Compose a full 384x272x3 uint8 frame (border + display) as a numpy
        array, without any pygame dependency. Used by the VIC screenshot test."""
        return self._compose_canvas()

    def _fd_status(self):
        """Floppy status for the title bar: activity LED + block counter.
        Lit by real 1541 VIA activity when --drive is on, and by the KERNAL
        trap loader otherwise, so the indicator is live in both modes."""
        s = self.system
        if s._d64 is None and s.drive is None:
            return ""
        if s.disk_led_timer > 0:
            s.disk_led_timer -= 1
        led = (s.disk_led_timer > 0
               or (s.drive is not None and (s.drive.led or s.drive.motor)))
        blocks = s.disk_blocks + (s.drive.blocks_read if s.drive else 0)
        return f"   [FD:{'*' if led else '-'} {blocks:04d}]"

    def render_frame(self):
        canvas = self._compose_canvas()
        surf = self.pygame.surfarray.make_surface(canvas.swapaxes(0, 1))
        self.frame_surf.blit(surf, (0, 0))
        if self.scale == 1:
            self.window.blit(self.frame_surf, (0, 0))
        else:
            scaled = self.pygame.transform.scale(self.frame_surf,
                                                 self.window.get_size())
            self.window.blit(scaled, (0, 0))
        self.pygame.display.set_caption(
            f"C64 — Python emulator   [{self.shown_fps:.1f} fps]"
            f"   [Joy: {('Port 1', 'Port 2', 'Both ports')[self._joy_port]}]"
            + self._fd_status())
        self.pygame.display.flip()

    def _render_sprite_run(self, idx, pixels, bg_mask, sprite_occupancy,
                           sy0, rows, attrs, decode_cache):
        """
        Render a run of consecutive screen lines of sprite `idx` that share one
        attribute set. `sy0` is the first screen line (0..199), `rows` the
        recorded sprite row (0..20) displayed on each line — Y-expansion
        doubling and any mid-frame row effects are already encoded in this
        sequence, so the block is built by fancy-indexing the decoded sprite.
        `attrs` = (x, pointer, colour, mc, x_expand, priority, mc0, mc1) as
        recorded for these lines. `decode_cache` memoises decoded sprite shapes
        per (pointer, mc) within the frame.
        Writes the sprite's bit into `sprite_occupancy` everywhere it draws.
        """
        np = self.np
        mem = self.system.mem
        (spr_x, pointer, sprite_color, multicolor, x_expand, prio,
         mc0, mc1, bank) = attrs

        grid = decode_cache.get((pointer, multicolor, bank))
        if grid is None:
            sd = mem.read_vic_bytes_bank(pointer * 64, 63, bank)
            if multicolor:
                # (21,12) 2-bit values 0..3, each MC pixel two wide -> (21,24)
                raw = np.frombuffer(sd, dtype=np.uint8).reshape(21, 3)
                g = np.zeros((21, 12), dtype=np.uint8)
                for p in range(4):
                    g[:, p::4] = (raw >> (6 - 2 * p)) & 0x03
                grid = np.repeat(g, 2, axis=1)
            else:
                bits_flat = np.unpackbits(np.frombuffer(sd, dtype=np.uint8))
                grid = bits_flat[:21 * 24].reshape(21, 24)
            decode_cache[(pointer, multicolor, bank)] = grid

        block = grid[np.asarray(rows, dtype=np.intp)]        # (n, 24)
        if x_expand:
            block = np.repeat(block, 2, axis=1)
        h, w = block.shape

        # Convert VIC X to inner-area (0..319); vertical is already screen rows.
        inner_x = spr_x - 24
        src_x0 = max(0, -inner_x)
        src_x1 = min(w, 320 - inner_x)
        if src_x0 >= src_x1:
            return                                            # fully off-screen
        dst_x0 = max(0, inner_x)
        dst_x1 = dst_x0 + (src_x1 - src_x0)
        dst_y0 = sy0
        dst_y1 = sy0 + h

        sprite_slice = block[:, src_x0:src_x1]
        nonzero = sprite_slice != 0
        if not nonzero.any():
            return

        # Colours: hi-res -> 0=transparent, 1=sprite colour; multicolor ->
        # 0=transparent, 1=$D025, 2=sprite colour, 3=$D026.
        if multicolor:
            color_lookup = np.array([
                [0, 0, 0],                                   # transparent
                C64_PALETTE[mc0],
                C64_PALETTE[sprite_color],
                C64_PALETTE[mc1],
            ], dtype=np.uint8)
            rgb_pixels = color_lookup[sprite_slice]          # (h, w, 3)
        else:
            sprite_rgb = np.array(C64_PALETTE[sprite_color], dtype=np.uint8)
            rgb_pixels = np.broadcast_to(sprite_rgb,
                                         sprite_slice.shape + (3,)).copy()

        # Priority ($D01B, constant within the run): 1 -> behind foreground
        # graphics, so only draw where the background mask is clear.
        bg_slice = bg_mask[dst_y0:dst_y1, dst_x0:dst_x1]
        if prio:
            draw_mask = nonzero & (bg_slice == 0)
        else:
            draw_mask = nonzero

        # Sprite-data collision ($D01F) is maintained by the VIC during
        # emulation (Vic._update_sprite_data_collision); bg_slice is used here
        # only for sprite/foreground priority.

        # Write sprite pixels
        target = pixels[dst_y0:dst_y1, dst_x0:dst_x1]
        target[draw_mask] = rgb_pixels[draw_mask]

        # Record where this sprite drew (for sprite-sprite collision pass)
        occ_slice = sprite_occupancy[dst_y0:dst_y1, dst_x0:dst_x1]
        occ_slice |= (nonzero.astype(np.uint8) << idx)

    def verify_foreground(self, verbose=False):
        """Cross-check the renderer's foreground mask against the VIC's
        per-raster foreground function (used for $D01F collision).

        Both derive from Vic.row_gfx_mode(), so they must agree bit for bit;
        any mismatch means the single-source-of-truth contract is broken and
        a Friday-the-13th-class bug (renderer and collision disagreeing about
        what is 'solid') has crept back in. Returns (bad_lines, bad_pixels);
        (0, 0) == all 64000 pixels agree. Call after a frame was composed."""
        vic = self.system.vic
        bm = getattr(self, "_last_fg_bitmap", None)
        if bm is None:
            print("verify_foreground: no frame composed yet")
            return (-1, -1)
        bad_lines = 0
        bad_pixels = 0
        for sy in range(200):
            want = vic._foreground_bits_at(sy + 51, 0, 40)
            got = 0
            row = bm[sy]
            for x in range(320):
                if row[x]:
                    got |= (1 << (24 + x))
            if got != want:
                bad_lines += 1
                bad_pixels += bin(got ^ want).count("1")
                if verbose and bad_lines <= 5:
                    print(f"  fg mismatch at line {sy}: "
                          f"{bin(got ^ want).count('1')} px differ")
        return (bad_lines, bad_pixels)

    def _log_joystick_state(self, frame):
        """Called once per frame while recording: append a joystick event
        whenever the active port's state changed since the last frame, so the
        transcript captures stick/fire the same way it captures keys."""
        js = self.system.cia1.joystick_state
        cur = (js[0], js[1])
        prev = getattr(self, "_input_log_joy_prev", (0, 0))
        if cur != prev:
            self._input_log.append((frame, "joy", cur[0], cur[1]))
            self._input_log_joy_prev = cur

    def _dump_input_log(self):
        """Print the recorded input transcript. Two views: a human-readable
        timeline and a compact Python list a headless run can replay."""
        log = self._input_log or []
        pg = self.pygame
        keyname = {
            getattr(pg, n): n[2:] for n in dir(pg)
            if n.startswith("K_")
        }
        # Joystick bit names (C64 pin mapping used by joystick_state).
        JOY = [(0x01, "hoch"), (0x02, "runter"), (0x04, "links"),
               (0x08, "rechts"), (0x10, "Feuer")]

        def joy_desc(v):
            if v == 0:
                return "—"
            return "+".join(n for b, n in JOY if v & b)

        print("\n=== F7 Eingabe-Protokoll "
              f"({len(log)} Ereignisse, Frame 0 = Aufnahmestart) ===")
        print("50 Frames = 1 Sekunde (PAL).\n")
        for frame, kind, a, b in log:
            sec = frame / 50.0
            if kind == "keydown":
                nm = keyname.get(a, f"key{a}")
                extra = f" '{b}'" if b and b.isprintable() else ""
                print(f"  F{frame:5d} ({sec:6.2f}s)  Taste ↓ {nm}{extra}")
            elif kind == "keyup":
                nm = keyname.get(a, f"key{a}")
                print(f"  F{frame:5d} ({sec:6.2f}s)  Taste ↑ {nm}")
            elif kind == "joy":
                p1, p2 = a, b
                print(f"  F{frame:5d} ({sec:6.2f}s)  Joystick "
                      f"P1={joy_desc(p1)} P2={joy_desc(p2)}")
        # Compact replay form (frame, kind, a, b) for headless reproduction.
        print("\n--- Kompaktform (für headless-Reproduktion) ---")
        print("INPUT_LOG = [")
        for e in log:
            print(f"    {tuple(e)!r},")
        print("]")
        print("=== Ende Protokoll ===\n")

    def _flicker_diag(self):
        """F10 flicker diagnosis: capture the next 6 rendered frames as
        PNGs plus a per-frame census of all VIC register writes (register,
        raster, cycle, value) into pit_diag_*.png / pit_diag_census.txt in
        the current directory — made for hunting frame-alternating
        artefacts while playing."""
        import numpy as np
        vic = self.system.vic
        frames = []
        census = []
        # align to a frame boundary first so EVERY captured frame carries a
        # complete census (a mid-frame start truncates frame 0's data).
        while vic.raster != 0:
            self.system.sid_run(vic.CYCLES_PER_LINE)
        orig = vic.write
        def hook(off, val):
            o = off & 0x3F
            if o <= 0x2E:
                census.append((len(frames), o, vic.raster,
                               vic._line_cycles, val))
            return orig(off, val)
        vic.write = hook
        try:
            for f in range(12):
                lines1 = ((self.RENDER_RASTER - vic.raster)
                          % vic.LINES_PER_FRAME or vic.LINES_PER_FRAME)
                self.system.sid_run(lines1 * vic.CYCLES_PER_LINE)
                frames.append(np.array(self.render_to_array(), copy=True))
                self.system.sid_run(self.CYCLES_PER_FRAME
                                    - lines1 * vic.CYCLES_PER_LINE)
        finally:
            vic.write = orig
        import os, sys
        base = os.path.dirname(os.path.abspath(sys.argv[0])) or "."
        try:
            from PIL import Image
            for i, fr in enumerate(frames):
                Image.fromarray(fr).save(
                    os.path.join(base, f"pit_diag_{i}.png"))
        except Exception:
            for i, fr in enumerate(frames):
                np.save(os.path.join(base, f"pit_diag_{i}.npy"), fr)
        with open(os.path.join(base, "pit_diag_census.txt"), "w") as f:
            f.write("frame reg raster cyc val\n")
            for e in census:
                f.write(f"{e[0]} D0{e[1]:02X} {e[2]} {e[3]} ${e[4]:02X}\n")
            for i in range(1, len(frames)):
                d = (frames[i] != frames[i-1]).any(axis=2)
                rows = np.where(d.any(axis=1))[0]
                f.write(f"# diff F{i-1}->F{i}: {d.mean()*100:.2f}% "
                        f"Zeilen {rows.min() if len(rows) else '-'}"
                        f"..{rows.max() if len(rows) else '-'}\n")
        print(f"Flicker-Diagnose geschrieben nach: {base}"
              f"{os.sep}pit_diag_0..11.png + pit_diag_census.txt")

    def _sprite_diag_dump(self):
        """F10: print a full sprite + collision snapshot to the console.

        Meant for debugging 'missing enemy' / 'movement blocked by phantom wall'
        style issues: stand at the spot where the bug happens, press F10, and
        copy the output. It shows which sprites are on, where, and whether the
        per-raster sprite collision fired during the last complete frame."""
        vic = self.system.vic
        r = vic.regs
        en = r[0x15]
        msb = r[0x10]
        print("=" * 60)
        print(f"SPRITE DIAG  v{__version__}   collision_enabled={vic.collision_enabled}")
        print(f"$D015 enable = {en:08b}   $D010 X-MSB = {msb:08b}")
        print(f"$D011={r[0x11]:02X} $D016={r[0x16]:02X} $D018={r[0x18]:02X} "
              f"$D01A(irq-en)={vic.irq_enable:02X} bank={self.system.mem.vic_bank()} "
              f"bitmap={(r[0x11]>>5)&1} mcm={(r[0x16]>>4)&1}")
        print(f"$D01C mc={r[0x1C]:08b}  $D01D Xexp={r[0x1D]:08b}  "
              f"$D017 Yexp={r[0x17]:08b}  $D01B prio={r[0x1B]:08b}")
        pbase = (self.system.mem.vic_bank() * 0x4000
                 + ((r[0x18] >> 4) & 0x0F) * 0x400 + 0x3F8)
        for i in range(8):
            on = (en >> i) & 1
            x = r[i * 2] | (((msb >> i) & 1) << 8)
            y = r[i * 2 + 1]
            ptr = self.system.mem.ram[pbase + i]
            flags = []
            if (r[0x1C] >> i) & 1: flags.append("mc")
            if (r[0x1D] >> i) & 1: flags.append("Xexp")
            if (r[0x17] >> i) & 1: flags.append("Yexp")
            if (r[0x1B] >> i) & 1: flags.append("behind")
            print(f"  spr{i} {'ON ' if on else 'off'} "
                  f"X={x:3d} Y={y:3d} ptr=${ptr:02X}(${ptr*0x40:04X}) "
                  f"col=${r[0x27+i]:X} {' '.join(flags)}")
        print(f"collision last full frame:  $D01E(spr-spr)={vic._dbg_sc_last:08b}  "
              f"$D01F(spr-data)={vic._dbg_dc_last:08b}")
        if vic._dbg_dc_rasters_last:
            spans = vic._dbg_dc_rasters_last
            lo = min(t[0] for t in spans); hi = max(t[0] for t in spans)
            bits = 0
            for _, sd in spans: bits |= sd
            print(f"  spr-data coll fired on rasters {lo}..{hi} "
                  f"({len(spans)} lines), sprites={bits:08b}")
        else:
            print("  spr-data coll: none last frame")
        # --- input / joystick state (press F10 while pushing a direction) ---
        c = self.system.cia1
        js0, js1 = c.joystick_state[0], c.joystick_state[1]
        portname = ("Port 1", "Port 2", "Both ports")[self._joy_port]
        try:
            dc00 = c.read(0) & 0xFF
            dc01 = c.read(1) & 0xFF
        except Exception:
            dc00 = dc01 = -1

        def decode(v):
            if v < 0:
                return "?"
            # active-low on the port: 0 = pressed
            names = ["up", "down", "left", "right", "fire"]
            return " ".join(n for b, n in enumerate(names) if not (v >> b) & 1) or "-"
        print(f"input: keypad-joy={portname}  joystick_state[0]={js0:05b} "
              f"[1]={js1:05b}")
        print(f"  $DC00={dc00:08b} (P2 dir/fire -> {decode(dc00)})  "
              f"$DC01={dc01:08b} (P1 dir/fire -> {decode(dc01)})")
        # --- host / audio status (for "no sound" style reports) ---
        ch = getattr(self, "audio_channel", None)
        busy = qd = "n/a"
        if ch is not None:
            try:
                busy = ch.get_busy()
                qd = ch.get_queue() is not None
            except Exception:
                pass
        mix = None
        try:
            mix = self.pygame.mixer.get_init()
        except Exception:
            pass
        sid = self.system.sid
        gates = sum(1 for v in getattr(sid, "voices", [])
                    if getattr(v, "control", 0) & 1)
        print(f"host: warp={self.warp} fps={self.shown_fps:.1f} "
              f"audio_enabled={self.audio_enabled} mixer={mix} "
              f"channel_busy={busy} queued={qd}")
        print(f"SID: $D418(vol)={sid.regs[0x18] & 0x0F if hasattr(sid, 'regs') else '?'} "
              f"gates_on={gates}")
        print("=" * 60)

    def run(self):
        clock = self.pygame.time.Clock()
        last = time.perf_counter()
        frames = 0
        running = True
        self._input_log = None          # F7 input recorder: None = off,
        self._input_log_frame0 = 0       # else a list of (frame, event) tuples
        total_frames = 0                 # monotonic frame counter (timebase)
        while running:
            for event in self.pygame.event.get():
                if event.type == self.pygame.QUIT:
                    running = False
                elif event.type == self.pygame.DROPFILE:
                    path = event.file
                    if path.lower().endswith(".d64"):
                        self.system.swap_disk(path)
                    else:
                        print(f"Kein D64: {path}")
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
                    if event.key == self.pygame.K_F6:
                        # Diskwechsel: durch die auf der Kommandozeile
                        # angegebenen D64s rotieren (F6 ist am C64 keine
                        # eigene Taste — dort ist es Shift+F5, was weiter
                        # funktioniert).
                        if len(self.disk_list) > 1:
                            self._disk_idx = (self._disk_idx + 1) % len(self.disk_list)
                            print(f"F6: Diskette {self._disk_idx + 1}/{len(self.disk_list)}")
                            self.system.swap_disk(self.disk_list[self._disk_idx])
                        elif self.disk_list:
                            print("F6: nur eine Diskette angegeben — weitere per "
                                  "Kommandozeile oder Drag&Drop aufs Fenster")
                        else:
                            print("F6: keine Disketten-Liste — D64s auf der "
                                  "Kommandozeile angeben oder per Drag&Drop wechseln")
                        continue
                    if event.key == self.pygame.K_F8:
                        vic = self.system.vic
                        vic.collision_enabled = not vic.collision_enabled
                        if not vic.collision_enabled:
                            vic.sprite_sprite_coll = 0
                            vic.sprite_data_coll = 0
                        print("Sprite collision: "
                              f"{'ON' if vic.collision_enabled else 'OFF'}")
                        continue
                    if event.key in (self.pygame.K_PAUSE,
                                     self.pygame.K_SCROLLLOCK):
                        # Toggle the input recorder (Pause or ScrollLock —
                        # neither exists on the C64 keyboard, so no clash).
                        # While on, every key and joystick event is logged
                        # with its frame number; on stop a replayable
                        # transcript is printed to the console (frame-stamped,
                        # so a headless run can reproduce the exact sequence).
                        if self._input_log is None:
                            self._input_log = []
                            self._input_log_frame0 = total_frames
                            self._input_log_joy_prev = (
                                self.system.cia1.joystick_state[0],
                                self.system.cia1.joystick_state[1])
                            print("Eingabe-Aufnahme GESTARTET (Pause/ScrollLock "
                                  "erneut = Stop + Protokoll)")
                        else:
                            self._dump_input_log()
                            self._input_log = None
                        continue
                    if event.key == self.pygame.K_F10:
                        self._sprite_diag_dump()
                        self._flicker_diag()
                        continue
                    if event.key in (self.pygame.K_KP0, self.pygame.K_F9):
                        # Cycle the keypad joystick: Port 2 → Port 1 → Both.
                        # "Both" drives both control ports at once, so a game
                        # that only reads port 1 (e.g. Exploding Fist) or port 2
                        # works without having to guess the right port. KP0 or
                        # F9 both do this (F9 in case the numeric keypad is
                        # unavailable / NumLock-dependent).
                        self._joy_port = {1: 0, 0: 2, 2: 1}[self._joy_port]
                        self.system.cia1.joystick_state[0] = 0
                        self.system.cia1.joystick_state[1] = 0
                        label = ("Port 1", "Port 2", "Both ports")[self._joy_port]
                        print(f"Keypad joystick → {label}")
                        continue
                    if self._input_log is not None:
                        rel = total_frames - self._input_log_frame0
                        self._input_log.append(
                            (rel, "keydown", event.key, event.unicode))
                    self._key_event(event.key, True, event.unicode)
                elif event.type == self.pygame.KEYUP:
                    if self._input_log is not None:
                        rel = total_frames - self._input_log_frame0
                        self._input_log.append(
                            (rel, "keyup", event.key, ""))
                    self._key_event(event.key, False)
            # SID-file playback (no-op for PRG / native mode)
            self.system.sid_play_tick()
            self.step_frame()
            frames += 1
            total_frames += 1
            if self._input_log is not None:
                self._log_joystick_state(total_frames - self._input_log_frame0)
            now = time.perf_counter()
            if now - last >= 1.0:
                self.shown_fps = frames / (now - last)
                frames = 0
                last = now
            if not self.warp:
                # tick_busy_loop instead of tick: plain tick() sleeps with the
                # OS timer's coarse granularity (~10-15 ms on some systems),
                # which can overshoot the 20 ms frame budget and silently drag
                # the effective rate below 50 fps — starving the audio queue
                # (heard as intermittent music dropouts that "warp mode fixes").
                # The busy-wait costs a little CPU but paces frames precisely.
                clock.tick_busy_loop(self.target_hz)
        if self.system.drive is not None:
            self.system.drive.flush_writes()
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

    def test_cpu(self, stop_val=-1, pass_pc=0x3463, verbose=False, cycle=False):
        """
        Load and run the Klaus Dormann 6502 functional test.
        Returns True if PC reaches `pass_pc`, False on any infinite-loop trap.
        cycle=True drives the cycle-accurate clock() core instead of step(),
        verifying that core executes the whole documented instruction set.
        """
        load_addr = 0x0400
        self.mem.write_system_byte(Config.ADDR_PROCESSOR_PORT_REG, 0)
        self.mem.load_ram(load_addr, _get_test_program())
        self.cpu.pc = load_addr
        self.cpu.trace = verbose
        self.cpu._micro = None

        def advance():
            if not cycle:
                return self.cpu.step()
            # run one whole instruction's worth of clock() calls
            self.cpu.clock()
            while self.cpu._micro is not None:
                self.cpu.clock()
            return True

        prev_pc = -1
        steps = 0
        while True:
            if self.cpu.pc == pass_pc:
                print(f"TEST PASSED at PC={word2hex(self.cpu.pc)} "
                      f"after {steps} steps, {self.cpu.cycles} cycles"
                      f"{' [cycle-accurate core]' if cycle else ''}.")
                return True
            if self.cpu.pc == prev_pc:
                print(f"Infinite loop (trap) at PC={word2hex(self.cpu.pc)} "
                      f"after {steps} steps, {self.cpu.cycles} cycles.")
                return False
            if 0 <= stop_val < 0x10000 and self.cpu.pc == stop_val:
                print(f"Debug stop at PC={word2hex(self.cpu.pc)}")
            prev_pc = self.cpu.pc
            if not advance():
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
    "dos1541":
        "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"
    ,
    "basic":
        "eNp9eXtcU1e+786DV3hFAU1Pp86agAiKGl/TaG07iIFENwnlYUGPsoGE7ihWcO50PuJppZ2sHA4d"
        "z4R72jvY3trtJitmh6KhojyE6ukRmnhm7Lb1Tqfz6KgVBjrTmd1aj1Xbyf2tYHvu/HMjWVlrr7V+"
        "6/da39/vt33p44Mfl2wq31RcZSsxBYuPP9R/O+jve6uvI5zwhl96PdgaXCJ9J/hC8HJwg7QiuEUq"
        "Gn7qWs0157U3T+UOHwq9HtoWfDWwM4BDhdfGr01ea+8rDqwf+8VY7Zhe8+ypo6fazv386icjn55z"
        "Xt9zffB6xsfpw/805BrsH3px6M9nmKGioYeHDriHD1QOH1w6enDe2UPt5ypmTpZOnXz21Lnt759w"
        "5oQt9guljvfsltorm4ur/91mr6ip7qXtlc22X1Zaii+wlitljup3K2su2SYrLVXVjsqJMkdVzduV"
        "luqaykuVll/CI9lx6cli2xXWUXyhqnjbxDZLpa30w82WyQrH1omKSpu9upe2V0oc9iusrepKCfte"
        "SfmFqrr3HRWWSyWso2qizHLFbvmgunhTsPrd0ktVFSXBaqvlkt1xparaIvf1h05+VGy/4HjvrfGx"
        "qrJLQKl40/s1Ve+VVk5UON6veuK9SvsF1vGOpVYugaHtUnXxpeLqSxUWy3+ylktV1ZX+bcW/KK76"
        "jxJrpZ+1lFb7K21l1mp/uW2zv+xdptrhQOXF9jpUamMt79MGUbbiHbuj+u8HpY4a+4XNlm22krlx"
        "BWjEYr9Cu3HNUSIT8V011d8My21VVTZ7GZojUlw+YWNZS1kxi76hU1O+yUINUI2etFVbHXSb472q"
        "Ont18a/jSrZ/+zyueNpxlKK4te5TeqKm2F5tq/7QAZovZR0f3F9Sbil3VH5YY99sKV2yGVVVF1db"
        "yoHbTcUwqNlUVVJpq7hSadlsK4fZ4srK4g8327bZqmwOO9pUh7ZbKt/9llNbpaXkSnVdhQWBNOXF"
        "1SURUCsVimqPddjfiQtHWSp1VJbXsMXxiRJHeQVr+XVJsX1JNQyARXvNxDfslNbYS6ptjktzzkJd"
        "5+ixN46dPvb2MfnY9WPKsdgxvbhYXCc+IjrE7eJucb94SPSJr4khcVSMiP9HvCF+KjK9Gb2LevN6"
        "f9Kb7tiaziBkqax0VDJgC8Sk68B7N9etSNdBdxP0tzLC6Ax8xlWq6PPy98gWWTeuVmHbuEaFt/xe"
        "o5KTiO33apWS1GVwzw/Jv+ZQsh+v8qw2k+1T9dgYJDumuNBMj5JLtpunjHh7WDO5w0xqoVsbTp6s"
        "82kHtnfXdsp36M/kjsm6i/LnnM79WHgdNo7eMPpWcBfW+gpk7cQan9EqpvRYTz95UX8X5Z8Wb/Mv"
        "N8yY7vJBHlYkygkTa8IqTtS3MJouXWg8vxcbx5f04lz0i5jE4Cz0QQhZ+gRmwGgtPITK+iK8/gvU"
        "HpDcQi9a1OffEFE06O1x6Zn4UOpAvliLWoM44m33HEQ/ZEKKIsa8G3yJ6ABhrx1HeyToeFJRVsC3"
        "WVAN1ONcshwbCYcXk/rOz+oNruV4Oc4jK9wxvALkN5P6qeXBsGZmcrHBZfRpJnMNA8buvIh8Zzp3"
        "ejGIjOoCaA3pZ9RKpwEobXel4lr/Cs8OnyriqUPDvSTbn3P4b6qfxlRklX81Xu5Z4U/tHPlK1V3f"
        "qf9ybjPb4SfL/EXY6Mk1AEtG5SFBGxkwyvciPS5jSGC6jSTXzUS6jV4jzvX9nhMZNP9aNF1Jf41R"
        "z1yt830mLmQf9rMXQy1aTaBd0Hoyxxm1PikaUx6bkb+IIuVhnBw1KtvyMluXRx+XtdIReXHU5NNG"
        "N/oe8rQJjCe109t+MTIDu8x3jgrKrWiHbEpI9bfNRI7cU43cUynfN89uULRRm6zGmebZGvl1nAyL"
        "lT9MJCu/pWtmZCXQPp0aGXlN0N8dOSrIg5SDt458rZo8KMVwO0eWBYoEFa73cgP1yncjEZJzud5n"
        "UDSdcgrJ7oR+mqLrHKgPwTf8gYGTv5aYYPeySPcysszgVuPlpMjN4BXoXwMSIy9Hf4yRh/1mvMaz"
        "liz3r8ArPSbqt+ihoPiAdwG4lXj3FWuPFZznMaznDGQZ2LIdKMTwQc6XCHL0ybPUD7IC6ACjpMHw"
        "X8FR4Ins5XmSnZAjJwLT2ThHUHkygd8SVBQEL4wAf/CdyJG1N7IVdbjIY0O/HJeQ3xb3y6hRTiSZ"
        "thjOjCjzBuplfXBuvbcec/Jp1vtxS6JG/wEY5f28TNO75tlDIY9NiF1UkiOgMP1d0y36a3oTKMm3"
        "pA6sR0RCXb1yQpc7M/QKz0sp6F4vSpQMPa52KznoZqxkg5Wst0p+FDuBDvejrn7SnHJocSNulF4U"
        "jlNnYktOSGPCCBLPgpxRSU6kUnb1o2VjyHyCbLESm1V63grCkXb/wfPqTxQtftTzGNy0drlEUA+0"
        "G2QNuzUYGWjH62mzAU7G7T719MGWZA0l9elx9sRxZeNsh29eNDe8UBccSResI2mClf0hwxIpukH5"
        "FZt8MrpVvgOr43yyQtBMls2q/EVhVScu9mzi0LVYWGWQN1IWAhtmlDTKAlnv34Af8WwEqZ8Xen0a"
        "1u0H/ckLxX/wPwY8Pewnj2K43eQR/0a83rOBS5YYuPYFMAX3iQuwPw9KGtAWOWgl7d+o6bAVlICE"
        "ILBMbZ8imcn6qWyyYSonnNpjdrUHDvqSZsJa6qhoYcC3iNTPqsBruFkGvAb8MYa3gDleiR5WUsW0"
        "InEevXHJJ3ker+fxBh638/ggWKfH8I2OOHFDkch4k+B6JZPkQBJO8iYPtCszcGVuRMBXbiqz6Gg/"
        "Ncy/KAnScVAOaZATgC+FWiusAVWxnx5HR4escKQ2+i9y96RL1vLsX4/P+Wq0SPkLD1DgzfbmhG/P"
        "rsRJJAcbow+Er5BsXb4R/lzZOJsYXTk4JzE7P4dku5JwNnCWA/vZNgm9GMY2zxbpTXpyhpWkW4Ed"
        "finy9csGXj8fPTiGzg0IDHF22yLE1W3jWPks799y/pzMosCZaKL8KEjW4Gn2tKGHQuj66HSbP95L"
        "GwspCTNd6NNRf1vkfKL8B5hDr44FnP4m4mJ/Gxswog4GTGp9c3Yl+9w4+JlzYq1voZzUCZ01vgy/"
        "68IKX7KcTpwTy8NJxOl3sTxg4IAT/WiQVPifwPs8raj9jNQgMLjC8wT67RmYrAAmv2045A2xp/tA"
        "daDYIhAv2ZuFDNcKWCGEvtdHr/w6pSTaq1REAwZlK+jx4egjyi6QPi/d9BH6/Tj650G67pE++X2J"
        "AYgVY4KKZMl6KR3uZl6WPkHSQccW48xIifWYZ3Xhr2wxt0pekEwfeFLQq0PRQrmuwJfYNZXiSwjN"
        "XIzfPFYMUZqfU/KBMyDSzEVlDLQBES2aLt9EUyG2oI9kKRoJFUkPFUmPo7RrhTGOzFPmmbRCTNaS"
        "x/0/oO4ObgfLEkQDuKCUJvRD2COP+h+jN4JDgVPRXFlPXeToUFx4kH3RNVElqCXmsEot/QBlvhHI"
        "krO4v5tHl+BkiLfgTlkcOGcqGj8hPUKBBRQROCUVHY6p0B3KXToaihWqlUR0uo/9MghhT14EuvkY"
        "XJ+9F4ReIsRqEJPlSKDYv0nqKQIUnuct8Wy+72/0nuOtHjZQ4t8cj9AHGBnlzatIQ3nXDs/pWk4z"
        "/QgoaSilO333w3heun4VLEuZ8bYDxSTAiSQIaUnSBpwkFRlwMqXrZiDoosOD6PoQ+o3Edr+Bbo6R"
        "DPS2RG2eBIbWsOV9cQaAH7LVz+I5BpTl6OsTbM4bIEQkJM8X0wHtlBYKeY9DE8E/QPeCsCx09Sfy"
        "79gn3iDAemCeXsMuCYLrlSipwGyS9JXwBruoj3sc0trKYmQrszsg00xnHofWgUorHeU0H62sTmdk"
        "rcBAyjKnDoAUsKQOLPkKZGFaqzsR5/GCCiB7dDxFhZuJzb8FPTWM5LPwcOfYqPnrFJWycDxThdeP"
        "61V4w/h8AKnxeSp8EHCtyz0v9ApFlCL5M+oBef3g1IY8M/i1Jqzhwl+LC+CgQLusnjw42S4yedYu"
        "q6SiYeUnJ0Cp5bDVPDvgWxjVhLOiqqU2laV8otzXABPgvWf7A+VyUfigO8n3Y1c6QO2jZyCgGnUu"
        "Y5D/sEMIPwUxyIrQCd6/Vb8wpGyT60vTu5Z+c5jwIC6XP6DrrL4PR16AMPG8YEVrTpByVuqnDt38"
        "VocQ5LFx2sjj3B4rwA9xWYnTSpqspNFKGqwtRkaI8Upu1AnKO9zv2cpvwfN57Obxbh7v4XELj/fy"
        "+GlLM95HGrgWnQYkSgfGAUlvjqGsAYCcgpPRmJwpBYUToF+IUS/YMn9zLLpC+Sjap9RGQ8pl8PzM"
        "/3akfx5krw9Fg3KWYJAfATAkLlssSJy2GNt9KkpAA1+cig4C2eMn0d0ToGmpsEgqKJKKBOZyO8z+"
        "kBFTQd1CDs+zd/vNxDnLENes4EuWxCmn9PGUi6M+4PS4AhZ/KUlX8oHhVpR90vedq9Wy4XxUzkae"
        "k55dnZChJXp2CnmIf4vdN8jlZejTKRxCauEMdgErdMty2PLgeZu8GLb0iALrGEMfxbxOTxN2AUo3"
        "clerZN35aricQzF241gcVMWzOmsI9HP1Zz40xz9cAvSzfj40p/guiAdDfLDLyv7qJPrsBB8c+eR1"
        "XDPyp9fxNlTNsIf7hVgRTR2pYpyWVAg/LmiT0Vdn46qypC5OtqQG6dTiJEsq5dPXH84iT0OKshvv"
        "huydQTvGQmxDmNppshwgETd4Gz1NpMW/F4XOeFs8e0PmqQYlWVL5tIEGiL/NQmwmclFOCjSbMg2+"
        "tIGWy43KX8VYWC2qZrqWLp6vqCUqHYgRQr4wBZYvaKp8gPGmYQsN/lkD4AzJJwHk0r0ZILovgfpF"
        "KtWC7x6d/a9oXjz1S5f10cVyFtHLMmRiGQkWbOlK6aDrvKXmBP0szTQuQ3D06MnywAovh+tvmKDQ"
        "WakYieVyvZxMSiOX65VnoSCoh+tybUb+XbTYlzC7wzxLON4aXSonSFnCOY6A4aPVcur5qPJXMB7l"
        "LVola89XK7fISr8J13u4eM2w3bPDAHRUEVw7V1LU+usiNOuF8Gzpro+Q0u56CeqD+v/3j9RD4uzn"
        "6K4yj5UjqTp3gqt+7gGQ4XwdDMPEjecHT6Txoh+uFWk2pZOGqM+XIhFhACwkt7OvjpG0hHiGIDA9"
        "VlJqJRYrenOAxxYel/LBUSgqrVBjgtO8plYR12squDsUhJT3wDtun+BxOo8zCg/htMBKYqLZ8MRq"
        "yKBXKevBjesjExZIm0tBXQsgVza44imzi/N9IM4vEjPg/ohZJE2+jV4aIKmCFpT7R/aTN2EEtSro"
        "f7+YQDWgV12MK0GvvnjR20ZSIxFQgJgqMXlpFcm8wa0K8e64frq66xF7ytuG9/uNk6ny71x14Z24"
        "LtjlqvVpIkrl/QJYYqb3+9uUhM7uWvneZN3kfvnWdJ2ZrJqqF9Sg2NWRKQ5+0uRGYBXDKRjoRfgQ"
        "dvLYBaVMhpwY6YLfJNbyJrvOHyH7E9oMig4O7nI5Qz1+o8vlbYPTL+I4+8A8KY1zXgBpbA0sqsVl"
        "Pa46bA2SMs5jhDMKoCzChZIe7xQZgYEiuWdpMOxPbMvf70s1dLkKQj2uwmD43yZ3yh9zgCQauExQ"
        "Z5vJmqlVQbJ2ajX1eAx3S/Sxm8dokiIxyp8g25YFMadIfBC0jK6dgjgPOBCvPF4M04Li9ol4cmgl"
        "Visps84l0+jLIOsYlAg8T6Er/2cY2z0OQAMgQBxWYrcCVsBmHtt57IDkzo7LwKJ25Qi2RgbKrJ36"
        "u34runJ2jhrMtsMkPjh3BNQmc/toTKa3YS6tFhi+285H/v7LwSEAIX8YhxohBgF1PiSYLi9NCL8Y"
        "pDCCGzjR6IWcm+aLVHYhFhnYp6RNJCnaiWT5JiQPKoOnoce1D7cFWn2qGe9+0gp5tlpO7YFMM7DP"
        "34o6zwQWXDXKCeIDtORoeJkhjS+rSNPLaoEBbHV5Wjs96d6FMzMz3gVcaabVFjO71vjXQmVzYbVv"
        "HuDBKl8qrVHxOs/3Q5Cq60mmidoFVJzJy3LgYWL2rsFrwY0dHjtZFVhNy2PpAZHBRm/uxAIlAb1z"
        "WrktJeEqijL04X2USUDjp5WbuNZbJ2lgsjZQd2O1nDSxChAk8QxdR1+WgNaNyfAFb6qlP3W4rkD/"
        "fpdJhoHAUDAwYiOUA7mB3Bt1QLZWGaXn3RwwmtbBEr0JGmVZZI7QBH1Ps+jGmvA/THC+BXB76316"
        "epOJMZCL7V4HqcI1pMrw3yQFhiOOBDsAWU2hdksQ1wzYXfV4O+GgjN9B1gTWUu7RuV5/TYTUdttD"
        "03WkDqzKLj09F30gI6GxCO/jcStIs8/Q5vQlxF9zgHEg/aeVAEQJ9NMzhFoKehcH2eF+uhT8bB/w"
        "vC/Ie6EGDio6a+eAsXtdj/wlb3Ctw+uAwe9zQJwCH62SoYJIjr9dui9rkC+Qsy6slTNvrJFTrQbX"
        "GrwGtqyNU+MuGOS0iYVyMl4wq8ELQUp0bCieRD07yAtMdyPE+ouDqGHockWPTztQEeqhcfTZwfvs"
        "8kH+Wx31AO9zaw2fVUBOkTgEgcdFgbMQsmsIxUeHYE7ZerHLahCZzyrCZ2yxCZcPQmuYXk0ghWt4"
        "ng/xuILHT5Aaaw/AcxeHXhhixVOo9wy980E6VOLSBeEp1Fz33wAMDwScshJwsRAVXxgCv7k9HIC8"
        "x9vm2R8wetspk3mBXO9Bei8Ww/Y8a093Hg2hN8eomHmBNv9+b7zeAGK3h2j6fHQIYsdrEDu6wz+H"
        "eo9q15ONcziSYyXZVlgEZLKB6Wwe51AO/zTUBZSyOeh4bfEwDbj12ZB3C11n2bLYpnzJSfOEcyxk"
        "vz8dJc02SAAsT9Pkjt09jI6M+DbCY+D8q7OBVu820U3cQeUSTRjyfPM9Df6nPbDDDWjp2SY20JTb"
        "0xq9Y3onSFq3qVB4JG+f/kmh4apbUQtusy3m2oZbR7TMLS12jWiYWxrsHFEzt9S4aUTF3FLhxrAG"
        "lY1A9DMEGuUtgSZvY8DpbQq4vE44G3DAnRxF8g0IBA24maO0iMu1F7uI09WCnaTJtQc3kUbXbtzI"
        "fn/ErUpszXflO/Ob8hv1nwPD4Xdo9YgbfBnTDcqm5sbmpmZns6u5lZuTmTRC20iaoG2iyScQhDwU"
        "iLdC2zrdKmdMu2TdtFNOnG6S1dONnJhJo+biQa2ndVDzknZQ/ZJmUPWS2s+/pHInm2aU6dlk0EI4"
        "e4HKp/4v1TP0n/oZzTPa3RH5zwbuecgKGM2hXdv+80BH1qupzo5nzP+24AVz6BHUsU57c+3ztOmg"
        "qUPHqv0Lv0TLxhS1nhbzpGH2kBWQrUH6lTACFYv0W/jJPBt//1QxLP07/JRcla7G53j03Lg0Bd24"
        "AV8cRUOjoLt8vAQX4ELSiupGiYs2Tto00aYR7Rplf3YWVv9kZEtKR9D3gIEUgooLSQGouIAsARUv"
        "Ifmg4vzm/OYlzQXNhc2tPVvkX3H0hgvaASPeCyiAW2izhzZzhcLTEMR206EbagbiVr5rcDX4tKaH"
        "DEX6bDcIAwfeGyb7wKrUGKYEuN63h9nnRuJvOfSQYIU/h3u2D/14GGz3R86DaE6VNibdEUbjz6HM"
        "mH8WxFSegYJGYsDauAGkhcWj4leSyr/7QqOs9++50CTr/C0XnLLWv/eCK3mpL2Xm5UJltX6tpCoI"
        "ZyTuzW/J35O/OzxtuqS/HiR7p1x4L2mZcuIWsmeqCe8hu6ca8e4e1nFW+oF8SRf/4NYCUJiYTSNX"
        "PvjPEvCeAvCdQuxiPxj+VisuKryTNk20aQZ9NNJOg6eVE/+xSHwSQqs2QIvQB8e88U3E1W3sJE7a"
        "NNEm/s6Rdhq6jbCJPI2bxYTT/MvcRfmOt5WDfWLiae5lfm5IGpR7ia2+22jfiPw5ax6BcQppXipB"
        "Fi+pOHAn3Aiu0CR2UrdfCl0XdnobcCtuZt8bLm3mcJ4njkeRkHJhIM/SbHr7RoP8vYG8lI6JRvmB"
        "yEDeRJM8n/445dSIdGiidSBvyqUUkGafGjB21Rict8U8K+Q161NCgLc8Kh/pEhuid/SJACkenguS"
        "5sKO0saERtwIKAEPANCEMAJA87SSZsCUjqWSgBuICycBQ7gRN2EndgU5gRF1L+28qL/ny4wul7Xe"
        "pyCVWCYn0MpiB1SYK6IW2UQHC6HUzIguV3RQbiZHlylaOamZZt++f8zj9BnUQ3axtvHm+rz6iv8g"
        "u8xTO/EuZb4+Bf1tdHqXfEdJQtdHJ6FDnjKpOHbwnDUPct7pnfCUN8+a4FqxunErOCCPoMqLu3iA"
        "wiXZFdVBRu/M40zzwHt1OoNrl84gMG3tsAvvYk3jrz429t2vjz69ZwltChipTehFvxknGwLrcaMX"
        "8kYzso1BssUu6hNUEgL1qaXlR2IMbva0RSRTgF4U7TmJudqhqMMp0rgwjgpGpdt4pzQM3R1jyiL9"
        "fOnUXFetz6BS7JT/QqXaKf8O2YZBv6KK7DS4daaUaGo40R0LSWrzrBrv8u7sgh1Z/jZpRQQO7FIS"
        "JRPt0P+3EDuIy3DggXMUaQ8YzlGoPbDwHMXaAwvO4caZsFb/kUlt+k2XTwsQq3OvhLog4inzt0VC"
        "hYeABvCQOEfW0+Yv67LFCjtC5/MU7fmNcsDfNhJjOqMm5UswnyoiLQvsUlbok+MWCoHsKpVkOcKo"
        "usSV5plZXfiee8MRjarriFolMUe0KiUZiEKPgaGg4iheMnd132WYnv/VEVPGzzMqrxCL/VoBqJ2J"
        "xWL/G6Z1Mfr5g66D0Ww9H4v9kGOYDH0s9nUQ5jb+OfT//VDIgVAJcKO0EjfY4s6waIfsGPLsp/WZ"
        "6Bdjkj1ebsuaHn8S+tvZHiv6ZCT+rGAUfXqO3+LTwcVInAs43POA9oVJbWtrH9v2PxY8d+rBH6/8"
        "y8e4/SHPd5b+U1Ndre65H339x0lAf4M+Hiukc3BwwShpdVf4NCh3jGWu/l+Ixj4p"
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


# =============================================================================
# Wolfgang-Lorenz "C64 Emulator Test Suite" (2.15) runner
# =============================================================================
# The Lorenz suite is a linear chain: every test exhaustively exercises one
# (documented or illegal) 6510 opcode, prints "<NAME> - OK" on success and
# KERNAL-LOADs the next test. On a mismatch it prints "BEFORE/AFTER/RIGHT" with
# the offending values and halts.
#
# We run it exactly like a real C64 + 1541: the test files are served through
# the existing LOAD trap ($FFD5) from an in-memory shim "disk", and the suite
# is kicked off authentically at the READY prompt (LOAD"*",8 : RUN) so that the
# current device ($BA) is 8 and the chain hangs itself along.
#
# Pass detection: test N counts as PASSED once the LOAD for test N+1 arrives
# (a test only loads its successor after its own "- OK"). If no follow-up LOAD
# comes within the per-test cycle budget, the transcript is inspected:
# "BEFORE" present -> FAIL (with the diagnostic), otherwise -> HANG (typical for
# cycle-exact CIA/IRQ/timing tests on an instruction-stepped core).


def _lorenz_petscii(buf):
    """Rough PETSCII->ASCII for the transcript (letters/digits + CR)."""
    out = []
    for b in buf:
        if b == 0x0D:
            out.append("\n")
        elif 0x20 <= b < 0x60:
            out.append(chr(b))
    return "".join(out)


def _lorenz_norm(name_bytes):
    """PETSCII/ASCII filename -> normalised upper-case key."""
    out = bytearray()
    for b in name_bytes:
        if 0xC1 <= b <= 0xDA:      # shifted PETSCII a-z -> A-Z
            b -= 0x80
        if 0x61 <= b <= 0x7A:      # ASCII a-z -> A-Z
            b -= 0x20
        out.append(b)
    return bytes(out).decode("latin1").strip().upper()


class _LorenzShim:
    """Stand-in for a mounted D64: serves the Lorenz test files by name from
    RAM. Implements only the handful of methods the LOAD/OPEN traps call."""

    def __init__(self, tests):
        self.tests = tests            # {UPPER_NAME: prg_bytes}
        self.requested = []           # log of every requested name

    def find_file(self, name):
        key = _lorenz_norm(name)
        if key in ("*", ""):
            key = "START"             # first LOAD"*",8 -> " start"
        self.requested.append(key)
        return (key, 0, 0) if key in self.tests else None

    def read_file(self, track, sector):
        return self.tests[track]      # 'track' carries the name here

    def read_sector(self, track, sector):
        return bytes(256)

    def disk_name(self):
        return b"LORENZ 2.15"

    def list_directory(self):
        return []


def _lorenz_parse_sys(payload, load_addr):
    """Read the SYS target from the BASIC stub (token $9E + ASCII digits)."""
    i = payload.find(0x9E)
    if i < 0:
        return load_addr
    j = i + 1
    digits = ""
    while j < len(payload) and 0x30 <= payload[j] <= 0x39:
        digits += chr(payload[j])
        j += 1
    return int(digits) if digits else load_addr


def _lorenz_force_run(sysm, tests, key):
    """Load test `key` at $0801 and jump to its SYS entry (used by
    --continue-from to skip past a stuck test)."""
    data = tests[key]
    load = data[0] | (data[1] << 8)
    payload = data[2:]
    sysm.mem.load_ram(load, payload)
    end = (load + len(payload)) & 0xFFFF
    for a in (0x2D, 0x2F, 0x31, 0xAE):
        sysm.mem.write_ram_direct(a, end & 0xFF)
        sysm.mem.write_ram_direct(a + 1, (end >> 8) & 0xFF)
    sysm.cpu.pc = _lorenz_parse_sys(payload, load)


def _lorenz_successor(data, own_name, valid):
    """Read the name of the next test a Lorenz test chains to (the file it
    LOADs after printing '<NAME> - OK'), so the runner can tell the user what
    to --continue-from after a hang/fail. Returns a lower-case name or None."""
    own = own_name.strip().upper()
    ok = data.find(b"\x20\x2d\x20\x4f\x4b")          # ' - OK'
    runs = []
    cur = bytearray()
    start = 0
    for i, b in enumerate(data):
        if (0x41 <= b <= 0x5A) or b in (0x28, 0x29):   # A-Z plus '(' ')'
            if not cur:
                start = i
            cur.append(b)
        else:
            if len(cur) >= 2:
                runs.append((start, bytes(cur).decode("latin1")))
            cur = bytearray()
    if len(cur) >= 2:
        runs.append((start, bytes(cur).decode("latin1")))
    cands = [(o, t) for o, t in runs if t != own and t in valid]
    after = [t for o, t in cands if ok >= 0 and o > ok]
    pick = after[0] if after else (cands[-1][1] if cands else None)
    return pick.lower() if pick else None


def _tcol(code, text):
    """Wrap `text` in an ANSI colour code when stdout is a real terminal;
    return it plain otherwise, so `--victest ... > log.txt` produces a clean,
    grep-able file instead of escape-code salad."""
    if sys.stdout.isatty():
        return f"\033[{code}m{text}\033[0m"
    return text


def _run_lorenz_suite(directory="lorenz", budget=120_000_000, max_tests=0,
                      wall_limit=0, continue_from=None, do_list=False,
                      cycle_accurate=False):
    """Run the Lorenz suite from `directory`. Returns True if nothing failed."""
    if not os.path.isdir(directory):
        print(f"Lorenz directory {directory!r} not found. Point --lorenztest "
              f"at the folder holding the extracted test files.")
        return False

    tests = {}
    for fn in os.listdir(directory):
        p = os.path.join(directory, fn)
        if os.path.isfile(p) and fn.lower() != "readme.md":
            tests[fn.strip().upper()] = open(p, "rb").read()

    print(f"Lorenz suite: {len(tests)} files from {directory!r}")
    if do_list:
        for n in sorted(tests):
            print(" ", n.lower())
        return True

    sysm = System(verbose=False, cycle_accurate=cycle_accurate)
    if cycle_accurate:
        print("  [cycle-accurate core — slower; exercises BA/CIA per cycle]")
    shim = _LorenzShim(tests)
    sysm._d64 = shim
    for addr, name in sysm._KERNAL_TRAPS.items():
        sysm.cpu.traps[addr] = getattr(sysm, name)

    transcript = bytearray()
    orig_chrout = sysm._trap_chrout

    def chrout_tap():
        la = sysm._current_output_la
        if la is None or la not in sysm._open_files:
            transcript.append(sysm.cpu.a & 0xFF)
        return orig_chrout()

    sysm.cpu.traps[0xFFD2] = chrout_tap

    results = []
    t0 = time.time()

    # Boot to READY, then authentic LOAD"*",8 : RUN
    sysm.run(3_000_000)
    sysm.type_string('LOAD"*",8\r')
    sysm.run(500_000)
    sysm.type_string("RUN\r")
    if continue_from:
        _lorenz_force_run(sysm, tests, continue_from.upper())
        current = continue_from.upper()
    else:
        current = None
    current_start_cyc = sysm.cpu.cycles
    transcript_mark = 0
    # When resuming mid-chain, the boot LOAD"*",8 above queued a stale START
    # request; skip everything requested before the forced jump so it can't
    # reset `current` back to START and disable hang detection.
    seen_requests = len(shim.requested) if continue_from else 0
    done = False

    def _pass(name):
        results.append((name, "PASS"))
        print(f"  {_tcol(32, 'PASS')}  {name}", flush=True)

    while not done:
        if wall_limit and time.time() - t0 > wall_limit:
            print(f"\n[wall-clock limit {wall_limit}s reached — stopping]")
            break
        sysm.run(400_000)

        while seen_requests < len(shim.requested):
            name = shim.requested[seen_requests]
            seen_requests += 1

            if name == "FINISH":
                if current and current not in ("START", None):
                    _pass(current)
                results.append(("finish", "DONE"))
                print(f"  {_tcol(36, 'DONE')}  suite ran through to 'finish'.", flush=True)
                done = True
                break

            if name == "START":
                current = "START"
                current_start_cyc = sysm.cpu.cycles
                transcript_mark = len(transcript)
                continue

            if current and current != "START":
                _pass(current)

            if name not in shim.tests:
                results.append((name, "MISSING"))
                print(f"  {_tcol(33, '????')}  {name} (file missing)", flush=True)
            current = name
            current_start_cyc = sysm.cpu.cycles
            transcript_mark = len(transcript)

            run_count = sum(1 for _, s in results
                            if s in ("PASS", "FAIL", "HANG"))
            if max_tests and run_count >= max_tests:
                print(f"\n[--max-tests {max_tests} reached]")
                done = True
                break

        if done:
            break

        if current and current != "START" and \
                sysm.cpu.cycles - current_start_cyc > budget:
            tail = _lorenz_petscii(transcript[transcript_mark:])
            if "BEFORE" in tail or "AFTER" in tail:
                detail = " | ".join(l.strip() for l in tail.splitlines()
                                    if l.strip())[-200:]
                results.append((current, "FAIL"))
                print(f"  {_tcol(31, 'FAIL')}  {current}", flush=True)
                print(f"        {detail}")
            else:
                results.append((current, "HANG"))
                print(f"  {_tcol(35, 'HANG')}  {current} "
                      f"(>{budget/1e6:.0f}M cycles, likely cycle-exact test)")
            nxt = _lorenz_successor(shim.tests.get(current, b""), current,
                                    set(shim.tests))
            if nxt:
                print(f"        [chain stopped — resume with "
                      f"--continue-from {nxt}]")
            else:
                print("        [chain stopped — resume with "
                      "--continue-from <next test>]")
            break

    npass = sum(1 for _, s in results if s == "PASS")
    nbad = sum(1 for _, s in results if s in ("FAIL", "HANG"))
    print("\n" + "=" * 60)
    print(f"Result: {npass} passed, {nbad} failed/hung, {time.time()-t0:.1f}s")
    if nbad:
        print("Failed/hung:")
        for n, s in results:
            if s in ("FAIL", "HANG"):
                nxt = _lorenz_successor(shim.tests.get(n, b""), n,
                                        set(shim.tests))
                hint = (f"   → resume with: --continue-from {nxt}"
                        if nxt else "")
                print(f"  {s:5s} {n}{hint}")
    print("=" * 60)
    return nbad == 0


# =============================================================================
# VIC-II screenshot test (VICE testprogs)
# =============================================================================
# Unlike Lorenz, the VIC-II tests are visual: a test PRG draws a screen that is
# compared against a reference image. We render the emulator's frame head-less
# into a numpy array (same 384x272 geometry as the VICE references), save it as
# a PNG, and — if a reference is present — compare them.
#
# The comparison is done at the C64 colour-INDEX level: every pixel of both
# images is mapped to the nearest of the 16 C64 colours and the index maps are
# compared. This is robust against small palette-RGB differences between VICE
# and this emulator (a native VIC image only ever uses the 16 fixed colours).
# A small +/- offset search absorbs minor border-crop differences.


def _run_vic_test(path, frames=20, out_dir="victest_out", threshold=95.0,
                  save_only=False, align=3, fgcheck=False, cycle=False):
    """Run one VIC-II test PRG (or every *.prg under a directory), render a
    frame, save it, and compare against references/<name>.png if present.
    Returns True if nothing scored below the threshold."""
    import glob
    import numpy as np

    # collect test files
    if os.path.isdir(path):
        prgs = sorted(glob.glob(os.path.join(path, "**", "*.prg"),
                                recursive=True))
    elif os.path.isfile(path):
        prgs = [path]
    else:
        print(f"VIC test path {path!r} not found.")
        return False
    if not prgs:
        print(f"No .prg files under {path!r}.")
        return False

    os.makedirs(out_dir, exist_ok=True)
    pal = np.array(C64_PALETTE, dtype=np.int32)

    def to_index(img):
        d = ((img[:, :, None, :].astype(np.int32)
              - pal[None, None, :, :]) ** 2).sum(-1)
        return d.argmin(-1)

    def best_match(mine, ref):
        ai, bi = to_index(mine), to_index(ref)
        if ai.shape != bi.shape:
            return None, None
        H, W = ai.shape
        best, best_off = -1.0, (0, 0)
        for dy in range(-align, align + 1):
            for dx in range(-align, align + 1):
                h, w = H - abs(dy), W - abs(dx)
                a = ai[max(0, dy):max(0, dy) + h, max(0, dx):max(0, dx) + w]
                b = bi[max(0, -dy):max(0, -dy) + h, max(0, -dx):max(0, -dx) + w]
                m = float((a == b).mean())
                if m > best:
                    best, best_off = m, (dy, dx)
        return best * 100.0, best_off

    # one head-less frontend, reused across tests (chargen/palette are ROM-fixed)
    fe = None
    results = []

    for prg in prgs:
        name = os.path.basename(prg)
        sysm = System(verbose=False)
        sysm.run(3_000_000)                     # boot to READY (batch: fast)
        if cycle:
            # switch to the per-PHI2 clock for the measured frames only —
            # boot in batch mode keeps the suite affordable.
            sysm.cycle_accurate = True
            sysm.vic._bl_defer = True
        try:
            load_addr, _len, is_basic = sysm.load_prg(prg)
        except Exception as ex:
            print(f"  {_tcol(33, 'SKIP')}  {name} (load error: {ex})", flush=True)
            continue
        if is_basic:
            sysm.type_string("RUN\r")
        else:
            sysm.type_string(f"SYS{load_addr}\r")

        if fe is None:
            fe = PygameFrontend(sysm, headless=True)
        else:
            fe.system = sysm

        vic = sysm.vic
        arr = None
        fg_result = None
        for fno in range(frames):
            lines1 = (fe.RENDER_RASTER - vic.raster) % vic.LINES_PER_FRAME
            if lines1 == 0:
                lines1 = vic.LINES_PER_FRAME
            cyc1 = lines1 * vic.CYCLES_PER_LINE
            sysm.run(cyc1)
            arr = fe.render_to_array()
            if fgcheck and fno == frames - 1:
                # Verify NOW, while memory and the per-raster recordings are in
                # exactly the state the frame was composed from. Verifying
                # after the frame's remaining cycles would compare against a
                # moved-on machine state and report false mismatches on any test
                # that animates or retriggers raster effects.
                fg_result = fe.verify_foreground()
            sysm.run(fe.CYCLES_PER_FRAME - cyc1)

        shot = os.path.join(out_dir, name + ".png")
        _png_write_rgb(shot, arr)

        if fg_result is not None:
            bl, bp = fg_result
            if bl:
                print(f"  {_tcol(31, 'FGCHECK')} {name}: renderer/collision "
                      f"foreground DISAGREE on {bl} lines ({bp} px)")
            else:
                print(f"  {_tcol(32, 'FGCHECK')} {name}: renderer==collision", flush=True)

        border = vic.regs[0x20] & 0x0F
        ssc = getattr(vic, "sprite_sprite_coll", 0)
        reg = f"$D020={border:X} $D01E={ssc:02X}"

        ref = os.path.join(os.path.dirname(prg), "references", name + ".png")
        if save_only or not os.path.isfile(ref):
            tag = "SAVE" if save_only else "NOREF"
            print(f"  {_tcol(36, tag)} {name}  ({reg})  -> {shot}", flush=True)
            results.append((name, tag, 0.0))
            continue

        pct, off = best_match(arr, _png_read_rgb(ref))
        if pct is None:
            print(f"  {_tcol(33, 'SIZE')} {name}  (Referenz-Format weicht ab, "
                  f"z.B. NTSC)")
            results.append((name, "SIZE", 0.0))
        elif pct >= threshold:
            print(f"  {_tcol(32, 'PASS')} {name}  {pct:5.1f}%  off{off}  ({reg})", flush=True)
            results.append((name, "PASS", pct))
        else:
            print(f"  {_tcol(31, 'DIFF')} {name}  {pct:5.1f}%  off{off}  ({reg})", flush=True)
            results.append((name, "DIFF", pct))

    npass = sum(1 for _, s, _ in results if s == "PASS")
    ndiff = sum(1 for _, s, _ in results if s == "DIFF")
    print("\n" + "=" * 60)
    print(f"VIC test: {len(results)} run, {npass} PASS, {ndiff} DIFF "
          f"(threshold {threshold:.0f}%). Screenshots in {out_dir}/")
    print("=" * 60)
    return ndiff == 0


def _print_help():
    """Print a full overview of command-line usage and options."""
    print(f"""
c64emu {__version__} — Commodore 64 emulator (single file)

USAGE
  python3 c64emu.py [FILE] [OPTIONS]

  With no arguments a pygame window opens and boots to the BASIC prompt.
  A FILE argument is auto-detected by extension and loaded on boot:
    game.prg    load program (auto-RUN if BASIC, else auto-SYS)
    game.d64    mount disk image, auto-load first file & start
    game.t64    mount tape archive, auto-load first file & start
    tune.sid    load PSID and play at 50 Hz

GENERAL OPTIONS
  -h, --help            show this help and exit
  --scale N             window scale factor (default 2)
  --no-run              load FILE but do not auto-RUN / auto-SYS
  --cycle               run FILE on the cycle-accurate core (badline BA-stall\n  --drive              echte 1541-Emulation aktivieren (M0; braucht roms/dos1541.bin)\n  F6 / Drag&Drop       Diskette wechseln (mehrere .d64 auf Kommandozeile = F6-Rotation)\n  --sid8580            8580-Filtermodell statt 6581 (linearere Cutoff-Kurve, mehr Resonanz)
                        + per-cycle CIA; slower than real time, but accurate
                        raster/badline timing). Works for .prg/.d64/.t64 and
                        with --headless too.
  --headless N          boot head-less, run N CPU steps, dump the text
                        screen as ASCII and exit (combine with a FILE to
                        load it first; FILE then runs 1,500,000 extra steps)

TEST MODES
  --cputest [-v]        run the Klaus Dormann 6502 functional test
                          add --cycle to run it on the cycle-accurate core
                        (-v traces every instruction)

  --lorenztest [DIR]    run the Wolfgang-Lorenz test suite from DIR
                        (default 'lorenz'); serves the test files through
                        the LOAD trap like a real 1541 and reports PASS /
                        FAIL / HANG per test. Sub-options:
      --list              list all test names in DIR and exit
      --max-tests N       stop after N tests (0 = all, default)
      --budget N          per-test cycle budget before a test counts as
                          FAIL/HANG (default 120,000,000)
      --wall N            overall wall-clock limit in seconds (0 = none)
      --continue-from T   skip ahead and resume the chain at test T
      --cycle             run on the cycle-accurate core (slower; needed for
                          the timing tests — cputiming/cia*/irq/nmi/trap*)
                          (use after a stuck cycle-exact CIA/IRQ test)

  --victest [PATH]      run the VIC-II screenshot test on PATH (a .prg or a
                        directory of them; default 'vicii'). Renders a frame,
                        saves it as PNG, and compares against the sibling
                        references/<name>.png at the C64 colour-index level.
                        Sub-options:
      --frames N          frames to run before capture (default 20)
      --out DIR           where to save screenshots (default 'victest_out')
      --threshold P       match percent needed for PASS (default 95)
      --align N           +/- pixel offset search for border crop (default 3)
      --save-only         only render+save, do not compare
      --fgcheck           also verify renderer's foreground mask == VIC's
                          per-raster collision foreground (single-source check)

IN-WINDOW KEYS
  F11                   toggle warp (unthrottled) speed
  F12                   soft reset
  arrow keys            authentic C64 cursor keys
  numeric keypad        joystick; KP0 toggles between port 1 and port 2

EXAMPLES
  python3 c64emu.py bruce_lee.d64
  python3 c64emu.py music.sid
  python3 c64emu.py --cputest
  python3 c64emu.py --lorenztest lorenz --max-tests 5
  python3 c64emu.py --lorenztest lorenz --continue-from oraa
  python3 c64emu.py game.prg --headless 2000000
""")


def main():
    args = sys.argv[1:]

    if "--help" in args or "-h" in args:
        _print_help()
        return

    print(f"c64emu {__version__}")

    if "--cputest" in args:
        cyc = "--cycle" in args
        if cyc:
            print("Running Klaus functional test on the CYCLE-ACCURATE core...")
        ok = C64Emu().test_cpu(verbose=("-v" in args), cycle=cyc)
        sys.exit(0 if ok else 1)

    if "--lorenztest" in args:
        i = args.index("--lorenztest")
        tdir = "lorenz"
        if i + 1 < len(args) and not args[i + 1].startswith("-"):
            tdir = args[i + 1]

        def _optval(flag, default, cast=int):
            if flag in args:
                j = args.index(flag)
                if j + 1 < len(args):
                    return cast(args[j + 1])
            return default

        ok = _run_lorenz_suite(
            tdir,
            budget=_optval("--budget", 120_000_000),
            max_tests=_optval("--max-tests", 0),
            wall_limit=_optval("--wall", 0),
            continue_from=_optval("--continue-from", None, str),
            do_list=("--list" in args),
            cycle_accurate=("--cycle" in args),
        )
        sys.exit(0 if ok else 1)

    if "--victest" in args:
        i = args.index("--victest")
        vpath = "vicii"
        if i + 1 < len(args) and not args[i + 1].startswith("-"):
            vpath = args[i + 1]

        def _vopt(flag, default, cast):
            if flag in args:
                j = args.index(flag)
                if j + 1 < len(args):
                    return cast(args[j + 1])
            return default

        ok = _run_vic_test(
            vpath,
            frames=_vopt("--frames", 20, int),
            out_dir=_vopt("--out", "victest_out", str),
            threshold=_vopt("--threshold", 95.0, float),
            save_only=("--save-only" in args),
            fgcheck=("--fgcheck" in args),
            align=_vopt("--align", 3, int),
            cycle=("--cycle" in args),
        )
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
    d64_list = []
    t64_file = None
    for a in args:
        if a.lower().endswith(".prg") and os.path.exists(a):
            prg_file = a
            break
        if a.lower().endswith(".sid") and os.path.exists(a):
            sid_file = a
            break
        if a.lower().endswith(".d64") and os.path.exists(a):
            if d64_file is None:
                d64_file = a
            d64_list.append(a)
            continue          # weitere D64s einsammeln (F6-Rotation)
        if a.lower().endswith(".t64") and os.path.exists(a):
            t64_file = a
            break

    if "--headless" in args:
        i = args.index("--headless")
        n = int(args[i + 1]) if i + 1 < len(args) and args[i + 1].isdigit() else 1_500_000
        sysm = System(cycle_accurate=("--cycle" in args))
        if "--drive" in args:
            sysm.enable_drive()
        if "--sid8580" in args:
            sysm.sid.set_model("8580")
        if prg_file:
            _launch_prg(sysm, prg_file, auto_run=not no_autorun)
            print("Running PRG for 1,500,000 extra cycles...")
            sysm.run(1_500_000)
        elif d64_file:
            _launch_d64(sysm, d64_file, auto_run=not no_autorun)
            print("Running for 1,500,000 extra cycles...")
            sysm.run(1_500_000)
        elif t64_file:
            _launch_t64(sysm, t64_file, auto_run=not no_autorun)
            print("Running for 1,500,000 extra cycles...")
            sysm.run(1_500_000)
        else:
            print(f"Booting for {n} cycles (headless)...")
            sysm.run(n)
        _dump_screen(sysm)
        return

    sysm = System(cycle_accurate=("--cycle" in args))
    if "--drive" in args:
        sysm.enable_drive()
    if "--sid8580" in args:
        sysm.sid.set_model("8580")
    if "--cycle" in args:
        print("Cycle-accurate mode: badline BA-stall + per-cycle CIA. "
              "Runs slower than real time in pure Python.")
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
    front.disk_list = d64_list
    front.run()


if __name__ == "__main__":
    main()
