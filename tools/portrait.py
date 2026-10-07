"""Parametric portrait renderer (original art, no game assets).

Draws a head-and-shoulders fighter portrait from a character's `portrait` spec at
4x resolution, then downsamples.  Used for select / versus screen cells.
"""
import math, random
from PIL import Image, ImageDraw, ImageFilter


def _c(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


def render(spec, w=32, h=52, ss=4):
    W, H = w * ss, h * ss
    bg0, bg1 = _c(spec['bg'][0]), _c(spec['bg'][1])
    im = Image.new('RGB', (W, H))
    d = ImageDraw.Draw(im)
    for y in range(H):
        t = y / H
        d.line((0, y, W, y), fill=tuple(int(bg0[i] * (1 - t) + bg1[i] * t) for i in range(3)))
    skin, skin_d, skin_l = _c(spec['skin'][0]), _c(spec['skin'][1]), _c(spec['skin'][2])
    hair, hair_d, hair_l = _c(spec['hair'][0]), _c(spec['hair'][1]), _c(spec['hair'][2])
    gi, gi_d, gi_l = _c(spec['gi'][0]), _c(spec['gi'][1]), _c(spec['gi'][2])
    cx = W // 2
    s = spec.get('head_scale', 1.0)
    fw, fh = int(W * 0.34 * s), int(H * 0.25 * s)          # face half-width / half-height
    fy = int(H * spec.get('face_y', 0.42))
    rnd = random.Random(spec.get('seed', 1))

    # shoulders / gi
    d.ellipse((cx - W * 0.62, H * 0.78, cx + W * 0.62, H * 1.45), fill=gi)
    d.polygon([(cx - W * 0.62, H), (cx - W * 0.2, H * 0.80), (cx - W * 0.05, H)], fill=gi_d)
    d.polygon([(cx + W * 0.62, H), (cx + W * 0.2, H * 0.80), (cx + W * 0.05, H)], fill=gi_l)
    # neck
    d.rectangle((cx - fw * 0.42, fy + fh * 0.6, cx + fw * 0.42, H * 0.84), fill=skin_d)
    # lapels: V opening
    under = _c(spec['undershirt']) if spec.get('undershirt') else skin_d
    d.polygon([(cx - W * 0.17, H * 0.80), (cx + W * 0.17, H * 0.80), (cx, H * 0.97)], fill=under)
    d.line((cx - W * 0.2, H * 0.79, cx, H * 0.99), fill=gi_l, width=ss * 2)
    d.line((cx + W * 0.2, H * 0.79, cx, H * 0.99), fill=gi_d, width=ss * 2)

    style = spec['hair_style']
    if style == 'curly':
        # big curly volume behind the face
        for _ in range(140):
            a = rnd.uniform(0, 2 * math.pi); r = rnd.uniform(0.55, 1.0)
            x = cx + math.cos(a) * fw * 1.55 * r
            y = fy - fh * 0.15 + math.sin(a) * fh * 1.35 * r
            rr = rnd.uniform(ss * 2.2, ss * 3.6)
            d.ellipse((x - rr, y - rr, x + rr, y + rr), fill=rnd.choice([hair, hair_d, hair_l, hair]))
    else:
        # hair pulled back: cap shape + ponytail to one side
        d.ellipse((cx - fw * 1.15, fy - fh * 1.25, cx + fw * 1.15, fy + fh * 0.6), fill=hair_d)
        d.ellipse((cx + fw * 0.7, fy - fh * 0.4, cx + fw * 1.45, fy + fh * 1.5), fill=hair_d)
    # face
    d.ellipse((cx - fw, fy - fh, cx + fw, fy + fh), fill=skin)
    d.ellipse((cx - fw * 1.0, fy - fh * 0.1, cx - fw * 0.7, fy + fh * 0.8), fill=skin_d)
    d.ellipse((cx + fw * 0.1, fy - fh * 0.6, cx + fw * 0.6, fy - fh * 0.2), fill=skin_l)
    if style == 'curly':
        # curly fringe over the forehead
        for _ in range(45):
            x = cx + rnd.uniform(-fw * 1.05, fw * 1.05); y = fy - fh * rnd.uniform(0.75, 1.15)
            rr = rnd.uniform(ss * 2, ss * 3.2)
            d.ellipse((x - rr, y - rr, x + rr, y + rr), fill=rnd.choice([hair, hair_l, hair_d]))
    else:
        # smooth hair over the top, parted, pulled back
        d.chord((cx - fw * 1.08, fy - fh * 1.22, cx + fw * 1.08, fy - fh * 0.25), 180, 360, fill=hair)
        d.chord((cx - fw * 0.9, fy - fh * 1.15, cx + fw * 0.4, fy - fh * 0.45), 190, 330, fill=hair_l)
        d.line((cx - fw * 0.15, fy - fh * 1.15, cx + fw * 0.05, fy - fh * 0.6), fill=hair_d, width=ss)
    # eyes
    ey = fy - fh * 0.05
    for sx in (-1, 1):
        ex = cx + sx * fw * 0.42
        d.ellipse((ex - ss * 2.2, ey - ss * 1.6, ex + ss * 2.2, ey + ss * 1.6), fill=(250, 250, 250))
        d.ellipse((ex - ss * 1.3, ey - ss * 1.4, ex + ss * 1.3, ey + ss * 1.4), fill=_c(spec.get('eye', '#402818')))
        d.line((ex - ss * 2.6, ey - ss * 3.2, ex + ss * 2.2, ey - ss * 3.6), fill=hair_d, width=ss)
    if spec.get('glasses'):
        gc = _c(spec['glasses'])
        for sx in (-1, 1):
            ex = cx + sx * fw * 0.42
            d.rounded_rectangle((ex - ss * 4.2, ey - ss * 3, ex + ss * 4.2, ey + ss * 3), radius=ss * 2,
                                outline=gc, width=int(ss * 1.4))
        d.line((cx - ss * 1.2, ey - ss * 0.5, cx + ss * 1.2, ey - ss * 0.5), fill=gc, width=ss)
    # nose / mouth / cheeks
    d.line((cx + ss * 0.5, fy + fh * 0.12, cx + ss * 1.5, fy + fh * 0.32), fill=skin_d, width=ss)
    if spec.get('smile'):
        d.chord((cx - fw * 0.38, fy + fh * 0.38, cx + fw * 0.38, fy + fh * 0.72), 0, 180, fill=(150, 40, 60))
        d.chord((cx - fw * 0.3, fy + fh * 0.4, cx + fw * 0.3, fy + fh * 0.55), 0, 180, fill=(250, 245, 240))
    else:
        d.line((cx - fw * 0.25, fy + fh * 0.55, cx + fw * 0.25, fy + fh * 0.52), fill=(160, 70, 70), width=ss)
    if spec.get('cheeks'):
        for sx in (-1, 1):
            x = cx + sx * fw * 0.6
            d.ellipse((x - ss * 2.5, fy + fh * 0.2, x + ss * 2.5, fy + fh * 0.45), fill=_c(spec['cheeks']))
    im = im.filter(ImageFilter.SMOOTH)
    return im.resize((w, h), Image.LANCZOS)


def quantize(img, palette, indices):
    """Map RGB image onto the given palette entries (list of (r,g,b)); returns index array."""
    import numpy as np
    a = np.asarray(img.convert('RGB'), np.int32)
    P = np.array([palette[i] for i in indices], np.int32)
    # perceptual-ish weighting
    wgt = np.array([3, 4, 2])
    dist = (((a[:, :, None, :] - P[None, None, :, :]) ** 2) * wgt).sum(-1)
    return np.array(indices)[dist.argmin(-1)]
