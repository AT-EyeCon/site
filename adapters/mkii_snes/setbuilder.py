"""Encode index images into a new MKII SNES sprite set and patch it into the ROM.

Each new frame keeps the ORIGINAL frame's piece budget (same number of 16x16 and
8x8 pieces, padded with transparent pieces placed where the originals were) so
VRAM/OAM usage and per-scanline sprite load never exceed what the game already
handles.  Coordinates are always written in absolute form (no delta nibbles).
"""
import sprites as sp
from render import OX, OY, W, H

TILE_GROUP_TILES = 256        # tiles per group (hi byte of tile word)
BLANK = bytes(32)


class RomSpace:
    """Bump allocator inside the expansion area (HiROM banks F0-FF)."""

    def __init__(self, rom, start=0xF00000, end=0x1000000):
        self.rom = rom; self.ptr = start; self.end = end

    def alloc(self, n, align=1, same_bank=True):
        p = (self.ptr + align - 1) // align * align
        if same_bank and (p >> 16) != ((p + n - 1) >> 16):
            p = ((p >> 16) + 1) << 16
        if p + n > self.end:
            raise RuntimeError('expansion space exhausted')
        self.ptr = p + n
        return p

    def write(self, addr, data):
        o = sp.off(addr); self.rom[o:o + len(data)] = data


def _tile_px(img, x0, y0):
    """8x8 index block from a 'P' image (outside canvas = 0)."""
    px = [[0] * 8 for _ in range(8)]
    for r in range(8):
        for c in range(8):
            X, Y = x0 + c, y0 + r
            if 0 <= X < W and 0 <= Y < H:
                px[r][c] = img.getpixel((X, Y))
    return px


def _occupied(px):
    return any(v for row in px for v in row)


def tile_frame(img, nlarge, nsmall):
    """Choose 16x16/8x8 pieces covering img with <= nlarge / nsmall pieces.
    Returns (larges, smalls, lost_pixels) where entries are canvas (x, y)."""
    data = img.tobytes()
    ys = [i // W for i, v in enumerate(data) if v]
    xs = [i % W for i, v in enumerate(data) if v]
    if not xs:
        return [], [], 0
    x0, y0 = min(xs), min(ys)
    best = None
    occ = set(zip(xs, ys))
    for oy in range(0, 16, 2):
        for ox in range(0, 16, 2):
            bx, by = x0 - ox, y0 - oy
            cells = {}
            for (x, y) in occ:
                cx, cy = (x - bx) // 16, (y - by) // 16
                q = ((x - bx) % 16 >= 8) + 2 * ((y - by) % 16 >= 8)
                cells.setdefault((cx, cy), {}).setdefault(q, 0)
                cells[(cx, cy)][q] += 1
            order = sorted(cells, key=lambda k: (-len(cells[k]), -sum(cells[k].values())))
            larges = order[:nlarge]
            larges = [k for k in larges if len(cells[k]) >= 2] if len(order) <= nlarge else larges
            smalls = []
            for k in cells:
                if k in larges: continue
                for q, cnt in cells[k].items():
                    smalls.append((cnt, k, q))
            smalls.sort(reverse=True)
            lost = sum(c for c, _, _ in smalls[nsmall:])
            score = (lost, len(larges) + len(smalls))
            if best is None or score < best[0]:
                best = (score, bx, by, larges, smalls[:nsmall], lost)
    _, bx, by, larges, smalls, lost = best
    L = [(bx + 16 * cx, by + 16 * cy) for cx, cy in larges]
    S = [(bx + 16 * k[0] + 8 * (q & 1), by + 16 * k[1] + 8 * (q >> 1)) for _, k, q in smalls]
    return L, S, lost


class SetEncoder:
    def __init__(self, rom, space):
        self.rom = rom; self.space = space
        self.tiles = {}            # bytes -> (group, idx)
        self.groups = []           # list of [addr, count]
        self.lost = {}

    def tile_word(self, tb):
        if tb in self.tiles:
            g, i = self.tiles[tb]
        else:
            if not self.groups or self.groups[-1][1] >= TILE_GROUP_TILES:
                if len(self.groups) >= 64: raise RuntimeError('tile groups exhausted')
                self.groups.append([self.space.alloc(TILE_GROUP_TILES * 32, align=32), 0])
            g = len(self.groups) - 1; i = self.groups[g][1]
            self.space.write(self.groups[g][0] + i * 32, tb)
            self.groups[g][1] += 1
            self.tiles[tb] = (g, i)
        return (i << 8) | (g << 2)

    def encode_frame(self, n, img, orig):
        nl = sum(p.large for p in orig.pieces); ns = len(orig.pieces) - nl
        L, S, lost = tile_frame(img, nl, ns)
        self.lost[n] = lost
        out = bytearray([nl + ns, nl])
        pad_l = [p for p in orig.pieces if p.large][len(L):]
        pad_s = [p for p in orig.pieces if not p.large][len(S):]
        blank = self.tile_word(BLANK)

        def put(x, y, words):
            out.extend([0, x & 0xFF, y & 0xFF])
            for wd in words: out.extend([wd & 0xFF, wd >> 8])

        for (x, y) in L:
            words = [self.tile_word(sp.encode_4bpp(_tile_px(img, x + dx, y + dy)))
                     for dx, dy in ((0, 0), (8, 0), (0, 8), (8, 8))]
            put(x - OX, y - OY, words)
        for p in pad_l: put(p.x, p.y, [blank] * 4)
        for (x, y) in S:
            put(x - OX, y - OY, [self.tile_word(sp.encode_4bpp(_tile_px(img, x, y)))])
        for p in pad_s: put(p.x, p.y, [blank])
        return bytes(out)

    def build(self, orig_hdr, images, frame_bank_size=0x10000):
        """images: dict frame_number -> 'P' image (all frames 1..N). Returns header addr."""
        nframes = max(images)
        self.tile_word(BLANK)
        # frame data, one bank region per 64 frames
        frame_addrs = {}
        banks = []
        for g in range((nframes + 63) // 64):
            chunk = {}
            for n in range(g * 64 + 1, min(nframes, g * 64 + 64) + 1):
                chunk[n] = self.encode_frame(n, images[n], sp.parse_frame(self.rom, orig_hdr, n))
            total = sum(len(v) for v in chunk.values())
            base = self.space.alloc(total)
            banks.append(base >> 16)
            p = base
            for n, data in chunk.items():
                self.space.write(p, data); frame_addrs[n] = p; p += len(data)
        # group table, frame table and bank table (frame+bank tables share one bank)
        gt = self.space.alloc(4 * 64)
        for gi, (a, _) in enumerate(self.groups):
            self.space.write(gt + 4 * gi, bytes([a & 0xFF, a >> 8 & 0xFF, a >> 16 & 0xFF, 0]))
        ft = self.space.alloc(2 * nframes + len(banks) + 1)
        bt = ft + 2 * nframes
        for n, a in frame_addrs.items():
            self.space.write(ft + 2 * (n - 1), bytes([a & 0xFF, a >> 8 & 0xFF]))
        self.space.write(bt, bytes(banks) + bytes([banks[-1]]))
        hdr = bytearray(orig_hdr.raw)
        hdr[0:2] = bytes([bt & 0xFF, bt >> 8 & 0xFF])
        hdr[2:4] = bytes([gt & 0xFF, gt >> 8 & 0xFF]); hdr[4] = gt >> 16
        hdr[5:7] = bytes([ft & 0xFF, ft >> 8 & 0xFF]); hdr[7] = ft >> 16
        assert ft >> 16 == bt >> 16
        ha = self.space.alloc(16)
        self.space.write(ha, bytes(hdr))
        return ha
