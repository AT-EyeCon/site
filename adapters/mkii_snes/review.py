"""Contact sheet with head markers, for reviewing head anchors."""
import json, math
from PIL import Image, ImageDraw
import sprites as sp, render as R


def head_sheet(rom, hdr, pal, heads, frames, path, cols=16, scale=1):
    ims = [R.frame_index_image(rom, hdr, n) for n in frames]
    s = R.sheet(ims, frames, pal, cols=cols)
    d = ImageDraw.Draw(s)
    for i, n in enumerate(frames):
        hd = heads.get(str(n)) or heads.get(n)
        if not hd: continue
        x0, y0 = (i % cols) * R.W, (i // cols) * (R.H + 10) + 10
        cx, cy, ang = hd[0] + x0, hd[1] + y0, hd[2]
        d.ellipse((cx - 7, cy - 7, cx + 7, cy + 7), outline=(0, 255, 0))
        dx, dy = math.sin(math.radians(ang)) * -10, math.cos(math.radians(ang)) * -10
        d.line((cx, cy, cx + dx, cy + dy), fill=(255, 0, 0))
        d.text((x0 + 60, y0 - 10), '%.2f' % hd[4], fill=(0, 255, 255))
    if scale != 1: s = s.resize((int(s.size[0] * scale), int(s.size[1] * scale)))
    s.save(path)
