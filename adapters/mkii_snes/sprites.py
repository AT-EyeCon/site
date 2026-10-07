"""MKII SNES (USA Rev 1) fighter sprite-set codec.

Reverse engineered from the frame builder at $81:8000 / tile fetch at $81:834B.
See docs/MKII_SNES_FEMALE_FIGHTER_SLOT_MAP.md for the format description.
"""
from dataclasses import dataclass, field

SET_BANK_TABLE = 0x84CDCC   # word per set index (even), bank of set header
SET_ADDR_TABLE = 0x84CDEE   # word per set index, address of set header
COMP_JUMP_TABLE = 0x81A451  # zero-byte-suppression handlers (verified mask order)


def off(addr):
    """HiROM CPU address -> file offset."""
    return addr & 0x3FFFFF


def rd16(rom, a):
    o = off(a); return rom[o] | rom[o + 1] << 8


def rd24(rom, a):
    o = off(a); return rom[o] | rom[o + 1] << 8 | rom[o + 2] << 16


@dataclass
class SetHeader:
    index: int
    addr: int
    bank_tbl: int      # [$5A] word per 64 frames: bank of frame data
    group_tbl: int     # [$4E] 4-byte tile-group pointers
    frame_tbl: int     # [$3E] word per frame: address of frame data
    delta_base: int    # [$52]-1 : init x, init y, x deltas, y deltas
    raw: bytes = b''


def set_header(rom, index):
    hb = rd16(rom, SET_BANK_TABLE + index); ha = rd16(rom, SET_ADDR_TABLE + index)
    a = ((hb & 0xFF) << 16) | ha
    r = rom[off(a):off(a) + 16]
    w = lambda i: r[i] | r[i + 1] << 8
    return SetHeader(index, a,
                     bank_tbl=(r[7] << 16) | w(0),
                     group_tbl=(r[4] << 16) | w(2),
                     frame_tbl=(r[7] << 16) | w(5),
                     delta_base=(r[11] << 16) | w(12),
                     raw=bytes(r))


@dataclass
class Piece:
    x: int            # signed, relative to object origin (unflipped)
    y: int
    large: bool       # 16x16 (4 tile words) or 8x8
    tiles: list       # tile words; flips in bits 0-1 of tiles[0]
    data_addr: int = 0  # ROM address of the tile word(s) in the frame stream

    @property
    def hflip(self): return bool(self.tiles[0] & 1)

    @property
    def vflip(self): return bool(self.tiles[0] & 2)


@dataclass
class Frame:
    number: int
    addr: int
    pieces: list = field(default_factory=list)


def frame_addr(rom, hdr, n):
    """n is 1-based frame number (low 9 bits of $4C3C)."""
    bank = rom[off(hdr.bank_tbl) + ((n - 1) >> 6)]  # byte index (LDA [$5A],y with y=(n-1)>>6)
    return (bank << 16) | rd16(rom, hdr.frame_tbl + (n - 1) * 2)


def parse_frame(rom, hdr, n):
    a = frame_addr(rom, hdr, n)
    o = off(a)
    count = rom[o]; nlarge = rom[o + 1]
    p = o + 2
    db = off(hdr.delta_base)
    cx, cy = rom[db], rom[db + 1]
    fr = Frame(n, a)
    for i in range(count):
        b = rom[p]; p += 1
        if b & 0xF0: cx = (cx + rom[db + 1 + (b >> 4)]) & 0xFF
        else: cx = rom[p]; p += 1
        if b & 0x0F: cy = (cy + rom[db + 0x10 + (b & 15)]) & 0xFF
        else: cy = rom[p]; p += 1
        large = i < nlarge
        nt = 4 if large else 1
        tiles = [rom[p + 2 * k] | rom[p + 2 * k + 1] << 8 for k in range(nt)]
        fr.pieces.append(Piece(cx - 256 if cx & 0x80 else cx, cy - 256 if cy & 0x80 else cy, large, tiles, data_addr=0xC00000 | p))
        p += 2 * nt
    fr.end = p
    return fr


def group_ptr(rom, hdr, tw):
    a = hdr.group_tbl + (tw & 0xFC)
    lo = rd16(rom, a); hi = rd16(rom, a + 2)
    return lo, hi


def _comp_masks(rom):
    """Derive, for each of the 256 handler codes, which buffer bytes receive data
    (in the order they are consumed). Derived by symbolic reading of the handler
    code is fragile, so we use the documented convention verified by tests:
    bit k set -> byte (7-k) is literal; literals consumed in ascending byte order."""
    return {c: [7 - k for k in range(7, -1, -1) if c >> k & 1] for c in range(256)}


_MASKS = None


def tile_bytes(rom, hdr, tw):
    """Return the 32 raw 4bpp bytes for a tile word."""
    global _MASKS
    lo, hi = group_ptr(rom, hdr, tw)
    idx = tw >> 8
    if not hi & 0x8000:
        a = ((hi & 0xFF) << 16) | lo
        a += idx * 32
        return bytes(rom[off(a):off(a) + 32])
    if _MASKS is None: _MASKS = _comp_masks(rom)
    stride = (hi >> 8) & 0x3F
    a = ((hi & 0xFF) << 16) | ((lo + stride * idx) & 0xFFFF)
    o = off(a)
    codes = rom[o:o + 4]; q = o + 4
    out = bytearray(32)
    for c in range(4):
        for bi in sorted(_MASKS[codes[c]]):
            out[c * 8 + bi] = rom[q]; q += 1
    return bytes(out)


def decode_4bpp(b):
    px = [[0] * 8 for _ in range(8)]
    for r in range(8):
        p0, p1, p2, p3 = b[2 * r], b[2 * r + 1], b[16 + 2 * r], b[17 + 2 * r]
        for c in range(8):
            s = 7 - c
            px[r][c] = (p0 >> s & 1) | (p1 >> s & 1) << 1 | (p2 >> s & 1) << 2 | (p3 >> s & 1) << 3
    return px


def encode_4bpp(px):
    b = bytearray(32)
    for r in range(8):
        for c in range(8):
            v = px[r][c]; s = 7 - c
            b[2 * r] |= (v & 1) << s; b[2 * r + 1] |= (v >> 1 & 1) << s
            b[16 + 2 * r] |= (v >> 2 & 1) << s; b[17 + 2 * r] |= (v >> 3 & 1) << s
    return bytes(b)


def frame_pixels(rom, hdr, fr):
    """Yield (x, y, colour_index) for every opaque pixel, unflipped object space."""
    for pc in fr.pieces:
        subs = [(0, 0, pc.tiles[0])]
        if pc.large:
            subs = [(0, 0, pc.tiles[0]), (8, 0, pc.tiles[1]), (0, 8, pc.tiles[2]), (8, 8, pc.tiles[3])]
        size = 16 if pc.large else 8
        for sx, sy, tw in subs:
            px = decode_4bpp(tile_bytes(rom, hdr, tw))
            for r in range(8):
                for c in range(8):
                    v = px[r][c]
                    if not v: continue
                    X, Y = sx + c, sy + r
                    if pc.hflip: X = size - 1 - X
                    if pc.vflip: Y = size - 1 - Y
                    yield pc.x + X, pc.y + Y, v
