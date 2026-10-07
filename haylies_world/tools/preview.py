"""Render previews from a built ROM: unique blocks and pose sheets with the character palette."""
import sys, os, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import smwplayer as P, snesgfx as g
from PIL import Image, ImageDraw

def palette(rom, slot='mario', bg=(200, 220, 255)):
    pal = P.SHARED + g.read_pal(rom, P.PAL_PC[slot], 10); pal[0] = bg; return pal

def img(px, pal, s):
    im = Image.new('RGB', (len(px[0]), len(px)))
    for y, r in enumerate(px):
        for x, c in enumerate(r): im.putpixel((x, y), pal[c])
    return im.resize((im.width * s, im.height * s), Image.NEAREST)

def blocks_sheet(rom, keys, out, s=5, cols=12, slot='mario'):
    gfx = P.load_gfx32(rom); pal = palette(rom, slot)
    W, H = 16 * s + 6, 16 * s + 14
    sh = Image.new('RGB', (cols * W, ((len(keys) + cols - 1) // cols) * H), (255, 255, 255)); d = ImageDraw.Draw(sh)
    for n, k in enumerate(keys):
        X, Y = n % cols * W, n // cols * H
        sh.paste(img(P.block_pixels(gfx, k), pal, s), (X, Y + 12)); d.text((X, Y), '%02X' % k, fill=(0, 0, 0))
    sh.save(out)

def poses_sheet(rom, power, out, s=3, slot='mario', extra=None, poses=range(0x46), cols=12):
    gfx = P.load_gfx32(rom); pal = palette(rom, slot)
    poses = list(poses); W, H = 48 * s, 56 * s + 14
    sh = Image.new('RGB', (cols * W, ((len(poses) + cols - 1) // cols) * H), (255, 255, 255)); d = ImageDraw.Draw(sh)
    for n, p in enumerate(poses):
        X, Y = n % cols * W, n // cols * H
        sh.paste(img(P.compose(rom, gfx, p, power, extra), pal, s), (X, Y + 14)); d.text((X + 3, Y), '%02X' % p, fill=(0, 0, 0))
    sh.save(out)
