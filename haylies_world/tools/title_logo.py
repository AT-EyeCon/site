"""Rebuild the title-screen layer-3 logo (stripe image at PC 0x2B55D-0x2B6D3, tiles in GFX28/29)."""
import lz2, snesgfx as g, ow

STRIPE_START, STRIPE_END = 0x2B55D, 0x2B6D3
BLANK = 0x38FC
WORLD_COLS = (15, 29)        # 'WORLD' + TM occupy columns 15..28 of rows 9..13
SHIFT = -6                   # re-centre WORLD

def parse(rom):
    p, out = STRIPE_START, []
    while p < STRIPE_END:
        a = rom[p] << 8 | rom[p + 1]; ln = ((rom[p + 2] & 0x3F) << 8 | rom[p + 3]) + 1
        words = [rom[p + 4 + 2 * i] | rom[p + 5 + 2 * i] << 8 for i in range(ln // 2)]
        out.append((a, words)); p += 4 + ln
    assert p == STRIPE_END
    return out

def render_word(art):
    cells = []
    for ch, (pal, col) in zip(art.WORD, art.COLOURS):
        gl = art.GLYPHS[ch]; w = len(gl[0]) * 2 + 4; w = 8 if w <= 8 else 16
        px = [[0] * w for _ in range(24)]
        fill = set()
        for y, r in enumerate(gl):
            for x, c in enumerate(r):
                if c == '#':
                    for dy in (0, 1):
                        for dx in (0, 1): fill.add((1 + 2 * x + dx, 1 + 2 * y + dy))
        for (x, y) in fill:                                  # drop shadow
            for sx, sy in ((1, 1), (2, 2), (1, 2), (2, 1)):
                if 0 <= x + sx < w and y + sy < 24: px[y + sy][x + sx] = 1
        for (x, y) in fill:                                  # outline
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    if 0 <= x + dx < w and 0 <= y + dy < 24 and (x + dx, y + dy) not in fill: px[y + dy][x + dx] = 1
        for (x, y) in fill: px[y][x] = col
        cells.append((px, pal, w // 8))
    return cells

def apply(rom, art):
    stripes = parse(rom)
    # current tilemap of the logo area
    tm = {}
    for a, words in stripes:
        base = a - 0x5000
        for i, w in enumerate(words): tm[(base + i) // 32, (base + i) % 32] = w
    world = {(r, c + SHIFT): w for (r, c), w in tm.items() if r >= 9 and WORLD_COLS[0] <= c < WORLD_COLS[1]}
    keep_tiles = {w & 0x3FF for w in world.values()} | {BLANK & 0x3FF}
    old_tiles = {w & 0x3FF for w in tm.values()}
    free = sorted(t for t in old_tiles - keep_tiles if t >= 0x80)   # GFX28 (<0x80) is shared with HUD/message box
    gfx = {}
    for f in (0x28, 0x29):
        d, n = lz2.decompress(rom, ow.GFX_PTR(rom, f)); gfx[f] = [bytearray(d), n]
    # new word tiles
    cells = render_word(art); total = sum(c[2] for c in cells)
    col0 = (32 - total) // 2; newmap = {}; uniq = {}
    x = col0
    for px, pal, tw in cells:
        for ty in range(3):
            for tx in range(tw):
                tile = [r[tx * 8:tx * 8 + 8] for r in px[ty * 8:ty * 8 + 8]]
                if not any(any(r) for r in tile):
                    newmap[(5 + ty, x + tx)] = BLANK; continue
                key = g.encode_2bpp(tile)
                if key not in uniq:
                    t = free.pop(0); uniq[key] = t
                    f = 0x29 if t >= 0x80 else 0x28
                    gfx[f][0][(t & 0x7F) * 16:(t & 0x7F) * 16 + 16] = key
                newmap[(5 + ty, x + tx)] = 0x2000 | pal << 10 | uniq[key]
        x += tw
    newmap.update(world)
    # emit stripes: one per row, contiguous span
    out = bytearray()
    for r in sorted({r for r, c in newmap}):
        cols = sorted(c for rr, c in newmap if rr == r)
        c0, c1 = cols[0], cols[-1]
        words = [newmap.get((r, c), BLANK) for c in range(c0, c1 + 1)]
        a = 0x5000 + r * 32 + c0; ln = len(words) * 2 - 1
        out += bytes([a >> 8, a & 0xFF, ln >> 8, ln & 0xFF]) + b''.join(w.to_bytes(2, 'little') for w in words)
    room = STRIPE_END - STRIPE_START - len(out)
    assert room >= 0, 'logo stripes too long'
    for r in (3, 4, 8, 14):          # pad with blank writes inside the frame
        if room <= 0: break
        n = min(28, (room - 4) // 2)
        while 0 < room - (4 + 2 * n) < 6: n -= 1
        if n <= 0: break
        a = 0x5000 + r * 32 + 2; ln = n * 2 - 1
        out += bytes([a >> 8, a & 0xFF, ln >> 8, ln & 0xFF]) + BLANK.to_bytes(2, 'little') * n; room -= 4 + 2 * n
    assert room == 0, 'padding left %d' % room
    rom[STRIPE_START:STRIPE_END] = out
    for f, (d, n) in gfx.items():
        c = lz2.compress(d); assert len(c) <= n, 'GFX%02X grew' % f
        off = ow.GFX_PTR(rom, f); rom[off:off + len(c)] = c
    return ['title logo -> %s WORLD (%d new tiles, %d free left)' % (art.WORD, len(uniq), len(free))]
