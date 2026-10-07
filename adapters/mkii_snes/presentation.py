"""Phase 4 presentation for a fighter slot: HUD nameplate (and anything that reuses it).

The HUD nameplate is a 2bpp bitmap (8px tall, N tiles) copied per character by
$83:CD34 from a decompressed name blob.  We hook that lookup so the slot's
character id copies an uncompressed bitmap from expansion ROM instead.
Glyphs are an original shaded block font (not extracted from the game).
"""
import numpy as np

# 7-row glyphs, '#' = ink.  Shading is applied procedurally (1 highlight, 2 body, 3 shadow).
FONT = {
    'A': ['.####.', '##..##', '##..##', '######', '##..##', '##..##', '##..##'],
    'B': ['#####.', '##..##', '##..##', '#####.', '##..##', '##..##', '#####.'],
    'C': ['.####.', '##..##', '##....', '##....', '##....', '##..##', '.####.'],
    'D': ['#####.', '##..##', '##..##', '##..##', '##..##', '##..##', '#####.'],
    'E': ['######', '##....', '##....', '#####.', '##....', '##....', '######'],
    'F': ['######', '##....', '##....', '#####.', '##....', '##....', '##....'],
    'G': ['.####.', '##..##', '##....', '##.###', '##..##', '##..##', '.#####'],
    'H': ['##..##', '##..##', '##..##', '######', '##..##', '##..##', '##..##'],
    'I': ['##', '##', '##', '##', '##', '##', '##'],
    'J': ['....##', '....##', '....##', '....##', '##..##', '##..##', '.####.'],
    'K': ['##..##', '##.##.', '####..', '###...', '####..', '##.##.', '##..##'],
    'L': ['##....', '##....', '##....', '##....', '##....', '##....', '######'],
    'M': ['##...##', '###.###', '#######', '##.#.##', '##...##', '##...##', '##...##'],
    'N': ['##..##', '###.##', '######', '##.###', '##..##', '##..##', '##..##'],
    'O': ['.####.', '##..##', '##..##', '##..##', '##..##', '##..##', '.####.'],
    'P': ['#####.', '##..##', '##..##', '#####.', '##....', '##....', '##....'],
    'R': ['#####.', '##..##', '##..##', '#####.', '##.##.', '##..##', '##..##'],
    'S': ['.####.', '##..##', '##....', '.####.', '....##', '##..##', '.####.'],
    'T': ['######', '..##..', '..##..', '..##..', '..##..', '..##..', '..##..'],
    'U': ['##..##', '##..##', '##..##', '##..##', '##..##', '##..##', '.####.'],
    'V': ['##..##', '##..##', '##..##', '##..##', '##..##', '.####.', '..##..'],
    'W': ['##...##', '##...##', '##...##', '##.#.##', '#######', '###.###', '##...##'],
    'Y': ['##..##', '##..##', '.####.', '..##..', '..##..', '..##..', '..##..'],
    'Z': ['######', '....##', '...##.', '..##..', '.##...', '##....', '######'],
}

# (site, direct-page pointer used by the copy loop that follows)
#   site code = LDA $83D704|D726,x ; TAY ; LDA $83D748,x   (9 bytes, X = char id * 2)
NAMEPLATE_SITES = [(0x83CD34, 0xBE), (0x83CD94, 0xBE), (0x83D5F3, 0xB6), (0x83D671, 0xB6)]


def render_name(text, gap=1):
    cols = []
    for ch in text:
        if ch == ' ':
            cols.append(np.zeros((7, 3), np.uint8)); continue
        g = np.array([[1 if c == '#' else 0 for c in row] for row in FONT[ch]], np.uint8)
        cols.append(g); cols.append(np.zeros((7, gap), np.uint8))
    ink = np.concatenate(cols, 1)
    ink = np.vstack([ink, np.zeros((1, ink.shape[1]), np.uint8)])
    px = np.zeros_like(ink)
    H, W = ink.shape
    for y in range(H):
        for x in range(W):
            if not ink[y, x]: continue
            up = y > 0 and ink[y - 1, x]
            down = y + 1 < H and ink[y + 1, x]
            right = x + 1 < W and ink[y, x + 1]
            px[y, x] = 1 if not up else (3 if not down or not right else 2)
    w = (W + 7) // 8 * 8
    return np.pad(px, ((0, 0), (0, w - W)))


def encode_2bpp(px):
    n = px.shape[1] // 8; out = bytearray(16 * n)
    for t in range(n):
        for r in range(8):
            for c in range(8):
                v = int(px[r, t * 8 + c]); s = 7 - c
                out[16 * t + 2 * r] |= (v & 1) << s; out[16 * t + 2 * r + 1] |= (v >> 1 & 1) << s
    return bytes(out)


WIN_TABLE = 0x83D7B8          # 17 x 16-bit pointers to "<NAME> WINS" strings in bank $83
WIN_ENTRIES = 17
# (LDA $83D7B8,x site, LDX #$0083 site) pairs feeding the text renderer $85:B79F
WIN_SITES = [(0x83D126, 0x83D13F), (0x83D1DE, 0x83D1F5), (0x83D213, 0x83D22A), (0x85A4B5, 0x85A4C9)]


class Presentation:
    """Collects per-character nameplates, then installs one shared hook."""

    def __init__(self):
        self.plates = []        # (char_id, addr, ntiles)
        self.wins = {}          # char_id -> text

    def add(self, rom, space, cfg, slot):
        px = render_name(cfg['display_name'])
        data = encode_2bpp(px)
        a = space.alloc(len(data)); space.write(a, data)
        self.plates.append((slot['char_id'], a, px.shape[1] // 8))
        self.wins[slot['char_id']] = cfg['display_name'] + ' WINS'

    def install(self, rom, space):
        if not self.plates: return
        o = lambda a: a & 0x3FFFFF
        self._install_wins(rom, space, o)
        for site, dp in NAMEPLATE_SITES:
            orig = bytes(rom[o(site):o(site) + 9])
            assert orig[0] == 0xBF and orig[4] == 0xA8 and orig[5:] == bytes.fromhex('bf48d783'), hex(site)
            c = bytearray()
            for cid, a, n in self.plates:
                c += b'\xe0' + (cid * 2).to_bytes(2, 'little')        # CPX #id*2
                c += b'\xd0\x11'                                       # BNE next
                c += b'\xa9' + (a & 0xFFFF).to_bytes(2, 'little')      # LDA #addr
                c += bytes([0x85, dp])                                 # STA dp
                c += b'\xa9' + (a >> 16).to_bytes(2, 'little')         # LDA #bank
                c += bytes([0x85, dp + 2])                             # STA dp+2
                c += b'\xa0\x00\x00'                                   # LDY #0
                c += b'\xa9' + n.to_bytes(2, 'little')                 # LDA #ntiles
                c += b'\x6b'                                           # RTL
            c += orig + b'\x6b'                                        # original lookup ; RTL
            h = space.alloc(len(c)); space.write(h, bytes(c))
            rom[o(site):o(site) + 9] = b'\x22' + h.to_bytes(3, 'little') + b'\xea' * 5


def _install_wins_impl(self, rom, space, o):
    strings = []
    for i in range(WIN_ENTRIES):
        p = 0x830000 | (rom[o(WIN_TABLE) + 2 * i] | rom[o(WIN_TABLE) + 2 * i + 1] << 8)
        q = o(p); e = rom.index(0, q)
        strings.append(bytes(rom[q:e]))
    for cid, text in self.wins.items():
        strings[cid] = text.encode('ascii')
    blob_len = 2 * WIN_ENTRIES + sum(len(x) + 1 for x in strings)
    base = space.alloc(blob_len)
    bank = base >> 16
    tbl, p = bytearray(), base + 2 * WIN_ENTRIES
    data = bytearray()
    for st in strings:
        tbl += (p & 0xFFFF).to_bytes(2, 'little'); data += st + b'\x00'; p += len(st) + 1
    space.write(base, bytes(tbl + data))
    for lda, ldx in WIN_SITES:
        assert rom[o(lda):o(lda) + 4] == bytes.fromhex('bfb8d783'), hex(lda)
        assert rom[o(ldx):o(ldx) + 3] == bytes.fromhex('a28300'), hex(ldx)
        rom[o(lda) + 1:o(lda) + 4] = base.to_bytes(3, 'little')
        rom[o(ldx) + 1:o(ldx) + 3] = bank.to_bytes(2, 'little')


Presentation._install_wins = _install_wins_impl


def apply(rom, space, cfg, slot, pres=None):
    if pres is not None: pres.add(rom, space, cfg, slot)


# ---------------------------------------------------------------- select portraits
import json as _json, os as _os, sys as _sys
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..', '..', 'tools'))
import portrait as _PT

_SEL = _json.load(open(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), 'data', 'select_screen.json')))


def _select_palette(rom):
    o = int(_SEL['palette'], 16) & 0x3FFFFF
    return [((c & 31) << 3, (c >> 5 & 31) << 3, (c >> 10 & 31) << 3)
            for c in (rom[o + 2 * i] | rom[o + 2 * i + 1] << 8 for i in range(224))]


def portrait_patch(rom, cfg, slot_name):
    """List of (7F addr, and_mask, or_value) for one select-screen cell."""
    cell = _SEL['cells'][slot_name]
    x0, y0, x1, y1 = cell['window']
    pal = _select_palette(rom)
    a, b = _SEL['palette_indices']
    img = _PT.render(cfg['portrait']['spec'], w=x1 - x0, h=y1 - y0)
    q = _PT.quantize(img, pal, list(range(a, b)))
    recs = {}
    for py in range(y0, y1):
        for px in range(x0, x1):
            t = cell['tiles']['%d,%d' % (px // 8, py // 8)]
            r, c = py % 8, px % 8
            v = int(q[py - y0, px - x0]); bit = 7 - c
            for pl in range(8):
                addr = t * 64 + (pl // 2) * 16 + 2 * r + (pl & 1)
                am, ov = recs.get(addr, (0xFF, 0))
                am &= ~(1 << bit) & 0xFF
                ov |= ((v >> pl) & 1) << bit
                recs[addr] = (am, ov)
    return [(k, am, ov) for k, (am, ov) in sorted(recs.items())]


def install_select_portraits(rom, space, patches):
    if not patches: return
    o = lambda a: a & 0x3FFFFF
    tbl = bytearray()
    for addr, am, ov in patches: tbl += addr.to_bytes(2, 'little') + bytes([am, ov])
    t = space.alloc(len(tbl)); space.write(t, bytes(tbl))
    src = int(_SEL['source'], 16)
    L = lambda a: a.to_bytes(3, 'little')
    c = bytearray()
    c += b'\xa5\x6c\x29\xff\x00'                         # LDA $6C ; AND #$00FF
    c += b'\xc9' + (src >> 16).to_bytes(2, 'little')     # CMP #bank
    c += b'\xd0\x05'                                     # BNE plain
    c += b'\xa5\x6a'                                     # LDA $6A
    c += b'\xc9' + (src & 0xFFFF).to_bytes(2, 'little')  # CMP #addr
    plain_br = len(c); c += b'\xf0\x04'                  # BEQ go (skip JML)
    c += b'\x5c\xfc\xb9\x85'                             # plain: JML $85B9FC
    c += b'\x22\xfc\xb9\x85'                             # go: JSL $85B9FC
    c += b'\x08\xc2\x30\x48\xda\x5a\x8b'                 # PHP ; REP #$30 ; PHA ; PHX ; PHY ; PHB
    c += b'\xe2\x20\xa9\x7f\x48\xab\xc2\x20'             # SEP #$20 ; LDA #$7F ; PHA ; PLB ; REP #$20
    c += b'\xa2\x00\x00'                                 # LDX #0
    loop = len(c)
    c += b'\xbf' + L(t)                                  # LDA tbl,x (addr)
    c += b'\xa8'                                         # TAY
    c += b'\xe2\x20'                                     # SEP #$20
    c += b'\xb9\x00\x00'                                 # LDA $0000,y
    c += b'\x3f' + L(t + 2)                              # AND tbl+2,x
    c += b'\x1f' + L(t + 3)                              # ORA tbl+3,x
    c += b'\x99\x00\x00'                                 # STA $0000,y
    c += b'\xc2\x20'                                     # REP #$20
    c += b'\xe8\xe8\xe8\xe8'                             # INX x4
    c += b'\xe0' + len(tbl).to_bytes(2, 'little')        # CPX #len
    c += b'\xd0' + bytes([(loop - (len(c) + 2)) & 0xFF]) # BNE loop
    c += b'\xab\x7a\xfa\x68\x28\x6b'                     # PLB ; PLY ; PLX ; PLA ; PLP ; RTL
    h = space.alloc(len(c))
    bne1, jml = 8, plain_br + 2          # first BNE (bank mismatch) -> JML
    assert c[bne1] == 0xD0
    c[bne1 + 1] = jml - (bne1 + 2)
    space.write(h, bytes(c))
    site = o(int(_SEL['hook_site'], 16))
    assert rom[site:site + 4] == b'\x22\xfc\xb9\x85'
    rom[site + 1:site + 4] = h.to_bytes(3, 'little')


# ---------------------------------------------------------------- versus portraits
VS_TILE_TABLE = 0x82DCD9     # 4-byte (addr16, bank16) per char id -> compressed 71x48-byte tile set
VS_PAL_TABLE = 0x82DD09      # 4-byte per char id -> 64-colour palette (128 bytes)
VS_W, VS_H, VS_TILES = 56, 80, 71


def lz_literal_stream(data):
    """All-literal stream for the $85:B9FC decompressor (mode 1).
    Output is produced back-to-front, so chunks are emitted from the end."""
    out = bytearray(len(data).to_bytes(2, 'little') + b'\x01')
    end = len(data)
    while end > 0:
        n = min(64, end)
        out += bytes([0x40 | (n - 1)]) + data[end - n:end]
        end -= n
    out += b'\x00'
    return bytes(out)


def vs_portrait(cfg):
    from PIL import Image
    img = _PT.render(cfg['portrait']['spec'], w=VS_W, h=VS_H)
    q = img.quantize(colors=64, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    pal = q.getpalette()[:64 * 3]
    pal += [0] * (192 - len(pal))
    px = list(q.getdata())
    tiles = bytearray()
    for t in range(VS_TILES):
        tx, ty = t % 7, t // 7
        b = bytearray(48)
        for r in range(8):
            for c in range(8):
                y, x = ty * 8 + r, tx * 8 + c
                v = px[y * VS_W + x] if y < VS_H else 0
                s = 7 - c
                for pl in range(6):
                    b[(pl // 2) * 16 + 2 * r + (pl & 1)] |= ((v >> pl) & 1) << s
        tiles += b
    palb = bytearray()
    for i in range(64):
        r, g, bl = pal[3 * i:3 * i + 3]
        palb += ((r >> 3) | (g >> 3) << 5 | (bl >> 3) << 10).to_bytes(2, 'little')
    return bytes(palb), bytes(tiles)


def install_vs_portrait(rom, space, cfg, char_id):
    o = lambda a: a & 0x3FFFFF
    palb, tiles = vs_portrait(cfg)
    stream = lz_literal_stream(tiles)
    pa = space.alloc(len(palb)); space.write(pa, palb)
    sa = space.alloc(len(stream)); space.write(sa, stream)
    for tbl, a in ((VS_TILE_TABLE, sa), (VS_PAL_TABLE, pa)):
        e = o(tbl) + 4 * char_id
        rom[e:e + 4] = bytes([a & 0xFF, a >> 8 & 0xFF, a >> 16, 0])
