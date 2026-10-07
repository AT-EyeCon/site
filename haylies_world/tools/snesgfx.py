"""SNES tile/palette helpers."""
from PIL import Image

def bgr15_to_rgb(v):
    return ((v & 31) * 255 // 31, (v >> 5 & 31) * 255 // 31, (v >> 10 & 31) * 255 // 31)

def rgb_to_bgr15(c):
    r, g, b = [round(x * 31 / 255) for x in c[:3]]
    return r | g << 5 | b << 10

def read_pal(rom, off, n):
    return [bgr15_to_rgb(rom[off + 2 * i] | rom[off + 2 * i + 1] << 8) for i in range(n)]

def decode_4bpp(data, t):
    b = data[t * 32:t * 32 + 32]
    px = []
    for y in range(8):
        p0, p1, p2, p3 = b[2 * y], b[2 * y + 1], b[16 + 2 * y], b[17 + 2 * y]
        px.append([((p0 >> (7 - x)) & 1) | ((p1 >> (7 - x)) & 1) << 1 | ((p2 >> (7 - x)) & 1) << 2 | ((p3 >> (7 - x)) & 1) << 3 for x in range(8)])
    return px

def encode_4bpp(px):
    b = bytearray(32)
    for y in range(8):
        for x in range(8):
            v = px[y][x]; m = 0x80 >> x
            if v & 1: b[2 * y] |= m
            if v & 2: b[2 * y + 1] |= m
            if v & 4: b[16 + 2 * y] |= m
            if v & 8: b[17 + 2 * y] |= m
    return bytes(b)

def decode_3bpp(data, t):
    b = data[t * 24:t * 24 + 24]
    return [[((b[2*y] >> (7-x)) & 1) | ((b[2*y+1] >> (7-x)) & 1) << 1 | ((b[16+y] >> (7-x)) & 1) << 2 for x in range(8)] for y in range(8)]

def encode_3bpp(px):
    b = bytearray(24)
    for y in range(8):
        for x in range(8):
            v = px[y][x]; m = 0x80 >> x
            if v & 1: b[2*y] |= m
            if v & 2: b[2*y+1] |= m
            if v & 4: b[16+y] |= m
    return bytes(b)

def decode_2bpp(data, t):
    b = data[t * 16:t * 16 + 16]
    return [[((b[2*y] >> (7-x)) & 1) | ((b[2*y+1] >> (7-x)) & 1) << 1 for x in range(8)] for y in range(8)]

def encode_2bpp(px):
    b = bytearray(16)
    for y in range(8):
        for x in range(8):
            v = px[y][x]; m = 0x80 >> x
            if v & 1: b[2*y] |= m
            if v & 2: b[2*y+1] |= m
    return bytes(b)

def sheet(tiles, pal, cols=16, scale=1, transparent0=False):
    rows = (len(tiles) + cols - 1) // cols
    im = Image.new('RGBA', (cols * 8, rows * 8), (255, 0, 255, 255))
    for i, t in enumerate(tiles):
        for y in range(8):
            for x in range(8):
                v = t[y][x]
                c = pal[v] if not (transparent0 and v == 0) else (0, 0, 0, 0)
                im.putpixel((i % cols * 8 + x, i // cols * 8 + y), tuple(c) + ((255,) if len(c) == 3 else ()))
    return im.resize((im.width * scale, im.height * scale), Image.NEAREST) if scale > 1 else im
