"""Zoomed grid view of base frames + current head anchors, for writing overrides."""
import json, math, sys
from PIL import Image, ImageDraw
import sprites as sp, render as R


def grid(rom, frames, anchors, path, z=4, crop=(24, 30, 104, 130)):
    hdr = sp.set_header(rom, 8); pal = R.read_palette(rom, 0xEF91B3)
    cw, ch = (crop[2] - crop[0]) * z, (crop[3] - crop[1]) * z
    cols = min(5, len(frames)); rows = (len(frames) + cols - 1) // cols
    out = Image.new('RGB', (cols * cw, rows * (ch + 14)), (20, 20, 30))
    d = ImageDraw.Draw(out)
    for i, n in enumerate(frames):
        im = R.frame_index_image(rom, hdr, n)
        rgb = Image.new('RGB', (R.W, R.H), (40, 40, 56))
        for y in range(R.H):
            for x in range(R.W):
                v = im.getpixel((x, y))
                if v: rgb.putpixel((x, y), pal[v])
        tile = rgb.crop(crop).resize((cw, ch), Image.NEAREST)
        ox, oy = (i % cols) * cw, (i // cols) * (ch + 14)
        out.paste(tile, (ox, oy + 14))
        for gx in range(crop[0], crop[2], 8):
            d.line((ox + (gx - crop[0]) * z, oy + 14, ox + (gx - crop[0]) * z, oy + 14 + ch), fill=(70, 70, 90))
            if gx % 16 == 0: d.text((ox + (gx - crop[0]) * z + 1, oy + 14), str(gx), fill=(120, 200, 255))
        for gy in range(crop[1], crop[3], 8):
            d.line((ox, oy + 14 + (gy - crop[1]) * z, ox + cw, oy + 14 + (gy - crop[1]) * z), fill=(70, 70, 90))
            if gy % 16 == 0: d.text((ox + 1, oy + 14 + (gy - crop[1]) * z), str(gy), fill=(120, 255, 120))
        a = anchors.get(str(n))
        lab = '%d' % n
        if a and a[0] is not None:
            cx, cy = ox + (a[0] - crop[0]) * z, oy + 14 + (a[1] - crop[1]) * z
            d.ellipse((cx - 5, cy - 5, cx + 5, cy + 5), outline=(255, 0, 0))
            lab += ' %s a%d f%d %.2f' % (a[5], a[2], a[3], a[4])
        d.text((ox + 2, oy), lab, fill=(255, 255, 0))
    out.save(path)


if __name__ == '__main__':
    rom = open(sys.argv[1], 'rb').read()
    anchors = json.load(open(sys.argv[2]))
    ov = json.load(open(sys.argv[3])) if len(sys.argv) > 5 else {}
    anchors.update({k: v for k, v in ov.items() if not k.startswith('_')})
    grid(rom, [int(x) for x in sys.argv[-2].split(',')], anchors, sys.argv[-1])
