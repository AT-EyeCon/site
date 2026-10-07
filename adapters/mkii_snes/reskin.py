"""Turn a base pose of the shared Kitana/Mileena sprite set into a character frame.

Inputs are the base pose's colour-index image (shared palette), the detected head
anchor and the character's config + head sprites.  Output is an index image in
the CHARACTER's own 16-colour palette.  No original ROM pixels are stored in
character folders; base poses are read from the user's ROM at build time.
"""
import json, os
import numpy as np
from PIL import Image
from scipy import ndimage
import headfind as HF
from render import W, H, OX, OY

# luminance of the shared base palette (Mileena), indices 0-15
BASE_LUM = [0, 33, 50, 6, 75, 99, 39, 172, 56, 128, 220, 121, 106, 77, 152, 88]
GI = [2, 3, 4, 5, 6]          # character palette gi shades dark->light


def load_heads(path, key):
    views, cur = {}, None
    for line in open(path):
        line = line.rstrip('\n')
        if not line or line.startswith('#'): continue
        if line.startswith('['): cur = line.strip('[]'); views[cur] = []; continue
        views[cur].append([key.get(ch, 0) for ch in line])
    return {k: np.array(v, np.uint8) for k, v in views.items()}


def load_character(char_dir):
    cfg = json.load(open(os.path.join(char_dir, 'character.json')))
    cfg['heads'] = load_heads(os.path.join(char_dir, 'art', 'heads.txt'), cfg['head_key'])
    cfg['rgb'] = [tuple(int(c[i:i + 2], 16) for i in (1, 3, 5)) for c in cfg['palette']['colors']]
    return cfg


def _xform(a, angle, flip):
    im = Image.fromarray(a)
    if flip: im = im.transpose(Image.FLIP_LEFT_RIGHT)
    return np.array(im.rotate(angle, resample=Image.NEAREST, expand=True, fillcolor=0))


def _paste(dst, src, cx, cy, only_opaque=True):
    h, w = src.shape
    y0, x0 = cy - h // 2, cx - w // 2
    for y in range(h):
        for x in range(w):
            v = src[y, x]
            if v and 0 <= y0 + y < H and 0 <= x0 + x < W: dst[y0 + y, x0 + x] = v


def _gi(lum):
    return GI[min(4, max(0, int((lum - 20) / 42)))]


def reskin(base, anchor, templates, cfg, scale_override=None):
    """base: HxW uint8 shared-palette indices. anchor: [cx,cy,angle,flip,score,view] or None."""
    cls = HF.CLASS[base]
    out = np.zeros_like(base)
    erase = np.zeros(base.shape, bool)
    view = None
    if anchor:
        cx, cy, ang, flip, _, view = anchor
        t = templates[view]
        m = _xform(((t > 0).astype(np.uint8)), ang, flip) > 0
        m = ndimage.binary_dilation(m, iterations=1)
        hh, ww = m.shape
        y0, x0 = cy - hh // 2, cx - ww // 2
        for y in range(hh):
            for x in range(ww):
                if m[y, x] and 0 <= y0 + y < H and 0 <= x0 + x < W: erase[y0 + y, x0 + x] = True
        erase &= base > 0
    # hair: dark pixels connected to the erased head, within reach of it
    dark = (cls == 3) & ~erase
    hair = np.zeros(base.shape, bool)
    if anchor:
        lab, _ = ndimage.label(dark | erase, structure=np.ones((3, 3)))
        ids = set(np.unique(lab[erase])) - {0}
        yy, xx = np.mgrid[0:H, 0:W]
        near = (xx - anchor[0]) ** 2 + (yy - anchor[1]) ** 2 <= 28 ** 2
        hair = np.isin(lab, list(ids)) & dark & near
    # belt: interior dark blobs (not hair, not outline) bordered by costume
    costume = cls == 1
    opaque = base > 0
    interior = ndimage.binary_erosion(opaque, structure=np.ones((3, 3)))
    cand = dark & ~hair & interior
    lab, nb = ndimage.label(cand, structure=np.ones((3, 3)))
    belt = np.zeros(base.shape, bool)
    stripe = np.zeros(base.shape, bool)
    near_cost = ndimage.binary_dilation(costume, iterations=1)
    for i in range(1, nb + 1):
        comp = lab == i
        if comp.sum() < 5: continue
        if (comp & near_cost).sum() < 0.4 * comp.sum(): continue
        ys, xs = np.nonzero(comp)
        if (np.ptp(xs) + 1) < 1.5 * (np.ptp(ys) + 1): continue   # belts run across the body
        belt |= comp
        mid = int(round(ys.mean()))
        stripe |= comp & (np.arange(H)[:, None] == mid)
    lum = np.array(BASE_LUM)[base]
    body = (base > 0) & ~erase
    out[body & (cls != 3)] = np.vectorize(_gi)(lum[body & (cls != 3)]) if (body & (cls != 3)).any() else 0
    d = body & (cls == 3)
    out[d] = np.where(np.isin(base[d], (1, 3)), 1, GI[0])
    if cfg['hair']['keep_base_ponytail']:
        out[hair] = np.where(lum[hair] > 60, 11, 10)
    else:
        out[hair] = 0
    belt_px = belt & body
    if cfg['belt'].get('stripe'):
        out[belt_px] = np.where(stripe[belt_px], 15, np.where(lum[belt_px] > 40, 14, 13))
        out[belt_px & ~stripe] = 13
    else:
        out[belt_px] = 13
        edge = belt_px & ~ndimage.binary_erosion(belt_px, structure=np.ones((3, 1)))
        out[edge & (np.arange(H)[:, None] > 0) & ~stripe] = 14
    # black undershirt wedge just below the head
    if anchor and cfg['outfit'].get('undershirt') and view != 'back':
        ang = np.radians(anchor[2])
        dx, dy = -np.sin(ang), np.cos(ang)
        for t in range(7, 12):
            half = max(0, (11 - t) // 2)
            for s in range(-half, half + 1):
                x = int(round(anchor[0] + dx * t + dy * s)); y = int(round(anchor[1] + dy * t - dx * s))
                if 0 <= x < W and 0 <= y < H and out[y, x] in GI: out[y, x] = 15
    # looser gi: widen fabric silhouette by one pixel horizontally
    loose = cfg['outfit'].get('loose_px', 1)
    for _ in range(loose):
        fabric = np.isin(out, GI)
        ring = ndimage.binary_dilation(fabric, structure=np.ones((1, 3), bool)) & (out == 0) & ~erase
        out[ring] = GI[1]
    # proportions: scale body about the object origin
    sc = scale_override or cfg['proportions']['body_scale']
    if sc != 1.0:
        im = Image.fromarray(out)
        nw, nh = int(round(W * sc)), int(round(H * sc))
        small = np.array(im.resize((nw, nh), Image.NEAREST))
        out = np.zeros_like(out)
        ox, oy = int(round(OX - OX * sc)), int(round(OY - OY * sc))
        out[oy:oy + nh, ox:ox + nw] = small[:H - oy, :W - ox]
    if anchor:
        hcx = int(round(OX + (anchor[0] - OX) * sc)); hcy = int(round(OY + (anchor[1] - OY) * sc))
        head = _xform(cfg['heads'][view], anchor[2], anchor[3])
        _paste(out, head, hcx, hcy)
    return out
