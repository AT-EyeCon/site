"""Super Mario World player-graphics model: GFX32 layout and pose->tile tables (bank $00)."""
import lz2, snesgfx as g

GFX32_PC = 0x40000          # $08:8000, LC_LZ2 compressed, decompressed to $7E:2000
GFX32_SIZE = 0x5D00
GFX32_MAXLEN = 0x3FC0       # GFX33 starts right after ($08:BFC0)
PAL_PC = dict(mario=0x32C8, luigi=0x32DC, fire_mario=0x32F0, fire_luigi=0x3304)  # 10 colours -> CGRAM $86-$8F
SHARED = [(0, 0, 0), (255, 255, 255), (0, 0, 0), (0x8b, 0x5a, 0x18), (0xde, 0xa4, 0x39), (0xff, 0xde, 0x73)]
POWER_OFS = [0x00, 0x46, 0x83, 0x46]   # $00:DF16 (small, big, cape, fire)

def pc(snes): return snes - 0x8000

def block_addr(t):
    """16x16 player tile byte -> byte offset in decompressed GFX32 (see $00:F636)."""
    return (t & 0xF7) * 0x40 + (0x4000 if t & 8 else 0)

def block_tiles(t):
    """8x8 tile indices (in the 16-wide GFX32 grid) of a 16x16 block: TL,TR,BL,BR."""
    a = block_addr(t) // 32
    return [a, a + 1, a + 16, a + 17]

def table_index(pose, power):
    return pose + (POWER_OFS[power] if pose < 0x3D else 0)

def pose_info(rom, pose, power, facing=1):
    y = table_index(pose, power)
    top = rom[pc(0xE00C) + y]; bot = rom[pc(0xE0CC) + y]; t06 = rom[pc(0xDF1A) + y]
    x = pose
    if pose == 0x29 and power == 0: x = 0x20
    i5 = rom[pc(0xDD32) + (rom[pc(0xDCEC) + x] | facing)]
    tiles = []
    for k in range(4):
        tn = rom[pc(0xDFDA) + t06 + k]
        xo = int.from_bytes(rom[pc(0xDD4E) + i5 + 2 * k:pc(0xDD4E) + i5 + 2 * k + 2], 'little', signed=True)
        yo = int.from_bytes(rom[pc(0xDE32) + i5 + 2 * k:pc(0xDE32) + i5 + 2 * k + 2], 'little', signed=True)
        tiles.append((tn, xo, yo))
    return dict(y=y, top=top, bot=bot, oam=tiles)

def load_gfx32(rom):
    d, n = lz2.decompress(rom, GFX32_PC)
    return bytearray(d)

def block_pixels(gfx, t):
    a, b, c, d = block_tiles(t)
    T = [g.decode_4bpp(gfx, i) for i in (a, b, c, d)]
    return [T[0][y] + T[1][y] for y in range(8)] + [T[2][y] + T[3][y] for y in range(8)]

def put_block(gfx, t, px):
    for k, i in enumerate(block_tiles(t)):
        ox, oy = (k & 1) * 8, (k >> 1) * 8
        gfx[i * 32:i * 32 + 32] = g.encode_4bpp([row[ox:ox + 8] for row in px[oy:oy + 8]])

def compose(rom, gfx, pose, power, extra=None):
    """Return 40x48 index image of a pose (head+body and extra 8x8 tiles from `extra` dict tile->px)."""
    info = pose_info(rom, pose, power)
    W, H, OX, OY = 48, 56, 16, 12
    img = [[0] * W for _ in range(H)]
    def paste(px, x, y):
        for yy, row in enumerate(px):
            for xx, v in enumerate(row):
                if v and 0 <= y + yy < H and 0 <= x + xx < W: img[y + yy][x + xx] = v
    order = []
    for tn, xo, yo in info['oam']:
        if tn & 0x80: continue
        if tn == 0: order.append((block_pixels(gfx, info['top']), xo, yo))
        elif tn == 2: order.append((block_pixels(gfx, info['bot']), xo, yo))
        elif extra is not None and tn in extra: order.append((extra[tn], xo, yo))
    for px, xo, yo in reversed(order):   # OAM: earlier entries are drawn on top
        paste(px, OX + xo, OY + yo)
    return img

def shoe_fix(rows, r_from=0, shoe='7'):
    """Brown (3) pixels with no skin/glove (1, 6, E) in their 8-neighbourhood are shoe leather -> pink.
    Brown touching skin is the skin outline (chin, hands) and is kept."""
    g = [list(r) for r in rows]; out = [r[:] for r in g]
    for y in range(r_from, 16):
        for x in range(16):
            if g[y][x] != '3': continue
            nb = [g[y + dy][x + dx] for dx in (-1, 0, 1) for dy in (-1, 0, 1)
                  if 0 <= x + dx < 16 and 0 <= y + dy < 16 and (dx or dy)]
            if not any(c in '16E' for c in nb): out[y][x] = shoe
    return [''.join(r) for r in out]
