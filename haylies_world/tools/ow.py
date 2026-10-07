"""Overworld player graphics (GFX10, 3bpp LZ2) and palette."""
import lz2, snesgfx as g
GFX_PTR = lambda rom, i: (rom[0x39F6 + i] & 0x7F) * 0x8000 + ((rom[0x39C4 + i] << 8 | rom[0x3992 + i]) & 0x7FFF)
OW_PAL_PC = 0x3598          # 7 colours (index 1-7) of OW sprite palette row used by Mario (attr pal 2)
PLAYER_BLOCKS = [6, 8, 10, 12, 14, 32, 36, 70, 100, 102]   # 16x16 blocks (top-left 8x8 tile index, 16-wide grid)

def load(rom, i=0x10):
    d, n = lz2.decompress(rom, GFX_PTR(rom, i)); return bytearray(d), n

def block(d, t):
    T = [g.decode_3bpp(d, i) for i in (t, t + 1, t + 16, t + 17)]
    return [T[0][y] + T[1][y] for y in range(8)] + [T[2][y] + T[3][y] for y in range(8)]

def put(d, t, px):
    for k, i in enumerate((t, t + 1, t + 16, t + 17)):
        ox, oy = (k & 1) * 8, (k >> 1) * 8
        d[i * 24:i * 24 + 24] = g.encode_3bpp([r[ox:ox + 8] for r in px[oy:oy + 8]])
