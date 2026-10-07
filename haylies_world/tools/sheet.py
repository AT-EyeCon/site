"""Build the Haylie sprite-sheet preview from a built ROM."""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import smwplayer as P, preview, ow, snesgfx as g
from PIL import Image, ImageDraw

def main(rom_path, out, shots=()):
    rom = open(rom_path, 'rb').read()
    skip = {0x11, 0x12, 0x13, 0x2A, 0x2B, 0x2C, 0x2D, 0x2E, 0x2F, 0x30, 0x31, 0x40, 0x41}
    poses = [p for p in range(0x46) if p not in skip]
    parts = []
    for title, pw, slot in [('SMALL HAYLIE', 0, 'mario'), ('SUPER HAYLIE', 1, 'mario'), ('CAPE HAYLIE (body frames)', 2, 'mario'),
                            ('FIRE HAYLIE', 1, 'fire_mario')]:
        f = os.path.join(os.path.dirname(out), '_tmp.png')
        preview.poses_sheet(rom, pw, f, 3, slot=slot, poses=poses, cols=19); parts.append((title, Image.open(f).copy()))
    # overworld frames
    d, n = ow.lz2.decompress(rom, ow.GFX_PTR(rom, 0x10))
    pal = [(200, 220, 255)] + g.read_pal(rom, ow.OW_PAL_PC, 7)
    owim = Image.new('RGB', (len(ow.PLAYER_BLOCKS) * 60, 60), (255, 255, 255))
    for i, t in enumerate(ow.PLAYER_BLOCKS):
        owim.paste(preview.img(ow.block(d, t), pal, 3), (i * 60 + 6, 6))
    parts.append(('OVERWORLD HAYLIE', owim))
    for s in shots: parts.append((os.path.basename(s), Image.open(s)))
    W = max(p.width for _, p in parts); H = sum(p.height + 24 for _, p in parts)
    sh = Image.new('RGB', (W, H), (255, 255, 255)); dr = ImageDraw.Draw(sh); y = 0
    for t, p in parts:
        dr.text((6, y + 6), t, fill=(200, 30, 120)); sh.paste(p, (0, y + 22)); y += p.height + 24
    sh.save(out)

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3:])
