"""Side-by-side base/character review sheet for chosen frames (dev tool)."""
import json, sys, numpy as np
sys.path.insert(0, '../../tools')
from PIL import Image, ImageDraw
import sprites as sp, render as R, reskin as RS, build

def sheet(frames, char, path, cols=8, crop=(16, 30, 112, 160)):
    rom = open('../../rom/Mortal Kombat II (USA) (Rev 1).sfc', 'rb').read(); h = sp.set_header(rom, 8)
    T = build.templates(rom, h); A = build.head_anchors(rom, h, T, 263, '../../out/.set8_heads_cache.json')
    cfg = RS.load_character('../../characters/' + char); bp = R.read_palette(rom, 0xEF91B3)
    cw, ch = crop[2] - crop[0], crop[3] - crop[1]
    out = Image.new('RGB', (cols * cw * 2, ((len(frames) + cols - 1) // cols) * ch), (40, 40, 56)); d = ImageDraw.Draw(out)
    def toimg(a, pal):
        im = Image.new('RGB', (a.shape[1], a.shape[0]), (40, 40, 56)); px = im.load()
        for y in range(a.shape[0]):
            for x in range(a.shape[1]):
                if a[y, x]: px[x, y] = pal[a[y, x]]
        return im
    for i, n in enumerate(frames):
        base = np.array(R.frame_index_image(rom, h, n)); a = A.get(str(n))
        o = RS.reskin(base, a, T, cfg)
        x, y = (i % cols) * cw * 2, (i // cols) * ch
        out.paste(toimg(base, bp).crop(crop), (x, y)); out.paste(toimg(o, cfg['rgb']).crop(crop), (x + cw, y))
        d.text((x + 2, y + 2), str(n), fill=(255, 255, 0))
    out.save(path)

if __name__ == '__main__':
    sheet([int(v) for v in sys.argv[1].split(',')], sys.argv[2], sys.argv[3])
