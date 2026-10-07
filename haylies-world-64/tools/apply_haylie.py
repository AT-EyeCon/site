#!/usr/bin/env python3
"""Haylie's World 64 character patch for HackerSM64.

Run from the root of a HackerSM64 checkout *after* asset extraction
(`make` or `python3 extract_assets.py us`). Idempotent: it always rebuilds
from the pristine files kept in `.haylie_orig/`.

What it does (keeps Mario's skeleton + animations untouched):
  * palette: pink cap/shirt, pink shoes, royal-blue overalls, fair skin, brown hair
  * head: shrinks Mario's big nose, removes the moustache (replaced by a smile
    + blush texture), brown hair locks instead of sideburns
  * new eye textures (big brown eyes with lashes), white heart cap logo
  * new geometry: pink rounded glasses w/ temples, brown ponytail + pink scrunchie
    (added to cap-on, cap-off, low-poly and metal/vanish heads)
  * loose cap actor (blown off / stolen cap) recolored + heart logo
"""
import math, re, shutil, sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw
except ImportError:
    sys.exit('ERROR: Pillow is required (pip install pillow)')

ROOT = Path.cwd()
MARIO = ROOT / 'actors/mario'
CAP = ROOT / 'actors/mario_cap'
ORIG = ROOT / '.haylie_orig'
HUD_HEAD = ROOT / 'textures/segment2/segment2.05A00.rgba16.png'
FILES = [MARIO / 'model.inc.c', CAP / 'model.inc.c', HUD_HEAD] + [
    MARIO / f'{n}.rgba16.png' for n in (
        'mario_logo', 'mario_mustache', 'mario_sideburn', 'mario_eyes_center',
        'mario_eyes_half_closed', 'mario_eyes_closed')] + [CAP / 'mario_cap_logo.rgba16.png']

for f in FILES:
    if not f.exists():
        sys.exit(f'ERROR: {f} missing. Run from HackerSM64 root after asset extraction.')
    keep = ORIG / f.relative_to(ROOT)
    if not keep.exists():
        keep.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, keep)
    shutil.copy2(keep, f)  # always start from pristine

# ---------------------------------------------------------------- palette
def lc(rgb):  # light + ambient (half) pair
    r, g, b = rgb
    return f'0x{r:02x}{g:02x}{b:02x}ff', f'0x{r//2:02x}{g//2:02x}{b//2:02x}ff'

PINK = (0xf2, 0x4f, 0xa2)       # cap / shirt / sleeves
SHOE = (0xff, 0x62, 0xb0)       # shoes (a touch lighter than the cap)
BLUE = (0x26, 0x50, 0xe8)       # overalls
SKIN = (0xff, 0xd2, 0xae)       # face
HAIR = (0x8a, 0x55, 0x2c)       # hair
GLASS = (0xff, 0x45, 0xa8)      # glasses frame
SCRUNCH = (0xff, 0x8c, 0xc8)    # ponytail scrunchie
BIB = (0xff, 0xa8, 0xd4)        # heart on the overalls bib
MOUTH = (0x8c, 0x22, 0x3c)      # open smile
TONGUE = (0xff, 0x7a, 0x96)

COLOR_MAP = {
    ('0xff0000ff', '0x7f0000ff'): lc(PINK),
    ('0x721c0eff', '0x390e07ff'): lc(SHOE),
    ('0xffff', '0x7fff'): lc(BLUE),
    ('0xfec179ff', '0x7f603cff'): lc(SKIN),
    ('0x730600ff', '0x390300ff'): lc(HAIR),
}

def recolor(text):
    for (o1, o2), (n1, n2) in COLOR_MAP.items():
        text = text.replace(f'gsSPLightColor(LIGHT_1, {o1})', f'gsSPLightColor(LIGHT_1, {n1})')
        text = text.replace(f'gsSPLightColor(LIGHT_2, {o2})', f'gsSPLightColor(LIGHT_2, {n2})')
    return text

# ---------------------------------------------------------------- vertex edits
VTX_RE = re.compile(r'(\{\{\{\s*)(-?\d+),\s*(-?\d+),\s*(-?\d+)(\s*\})')

def edit_vtx_arrays(text, name_pred, fn):
    def arr(m):
        if not name_pred(m.group(1)):
            return m.group(0)
        def one(v):
            p = tuple(int(v.group(i)) for i in (2, 3, 4)); q = tuple(fn(*p))
            return v.group(0) if q == p else '%s%6d, %6d, %6d%s' % (v.group(1), *q, v.group(5))
        body = VTX_RE.sub(one, m.group(2))
        return m.group(0).replace(m.group(2), body)
    return re.sub(r'static const Vtx (\w+)\[\] = \{(.*?)\n\};', arr, text, flags=re.S)

def shrink_nose(x, y, z):
    # Head-bone space: X up, Y forward, Z sideways. Mario's nose pokes out to Y~180.
    if y <= 104 or abs(z) > 70 or x > 140:
        return x, y, z
    t = min(1.0, (y - 104) / 76.0)
    y2 = 104 + (y - 104) * 0.24
    x2 = x + (106 - x) * 0.45 * t      # pull toward a small button-nose centre
    z2 = z * (1 - 0.60 * t)
    return x2, y2, z2

def is_head_array(name):
    return (any(k in name for k in ('face', 'eyes', 'mustache', 'sideburn', 'm_logo', 'hair'))
            and 'hand' not in name and 'unused' not in name)

def slim_jaw(x, y, z):
    # Mario's heavy jowls -> rounder, smaller chin. Smooth falloff below the eyes.
    f = max(0.0, min(1.0, (95 - x) / 95.0))
    f = f * f * (3 - 2 * f)
    z2 = z * (1 - 0.20 * f)
    y2 = y * (1 - 0.14 * f) if y > 0 else y
    x2 = x + 14 * f
    return x2, y2, z2

def reshape_head(x, y, z):
    x, y, z = shrink_nose(x, y, z)
    x, y, z = slim_jaw(x, y, z)
    return round(x), round(y), round(z)

# ---------------------------------------------------------------- mesh helpers
class Mesh:
    def __init__(self):
        self.v = []; self.t = []
    def add(self, p, n):
        l = math.sqrt(sum(c * c for c in n)) or 1
        self.v.append((tuple(round(c) for c in p), tuple(max(-127, min(127, round(c / l * 127))) for c in n)))
        return len(self.v) - 1
    def tri(self, a, b, c):
        self.t.append((a, b, c))
    def quad_flat(self, a, b, c, d):
        n = cross(sub(b, a), sub(d, a))
        i = [self.add(p, n) for p in (a, b, c, d)]
        self.tri(i[0], i[1], i[2]); self.tri(i[0], i[2], i[3])

def sub(a, b): return tuple(x - y for x, y in zip(a, b))
def add(a, b): return tuple(x + y for x, y in zip(a, b))
def mul(a, s): return tuple(x * s for x in a)
def cross(a, b): return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])
def norm(a):
    l = math.sqrt(sum(c * c for c in a)) or 1
    return tuple(c / l for c in a)

def emit(name, mesh, batch=30):
    """Emit Vtx arrays + a geometry-only display list, chunked for the 32-entry vertex cache."""
    out = []; dl = [f'const Gfx {name}_dl[] = {{']
    tris = list(mesh.t); k = 0
    while tris:
        used = {}; chunk = []
        rest = []
        for t in tris:
            need = [i for i in t if i not in used]
            if len(used) + len(need) <= batch:
                for i in need: used[i] = len(used)
                chunk.append(t)
            else:
                rest.append(t)
        tris = rest
        vname = f'{name}_vtx_{k}'; k += 1
        order = sorted(used, key=used.get)
        out.append(f'static const Vtx {vname}[] = {{')
        for i in order:
            (x, y, z), (nx, ny, nz) = mesh.v[i]
            out.append('    {{{%6d, %6d, %6d}, 0, {0, 0}, {0x%02x, 0x%02x, 0x%02x, 0xff}}},' % (x, y, z, nx & 255, ny & 255, nz & 255))
        out.append('};\n')
        dl.append(f'    gsSPVertex({vname}, {len(order)}, 0),')
        for j in range(0, len(chunk), 2):
            a = [used[i] for i in chunk[j]]
            if j + 1 < len(chunk):
                b = [used[i] for i in chunk[j + 1]]
                dl.append('    gsSP2Triangles(%2d, %2d, %2d, 0x0, %2d, %2d, %2d, 0x0),' % (*a, *b))
            else:
                dl.append('    gsSP1Triangle(%2d, %2d, %2d, 0x0),' % tuple(a))
    dl.append('    gsSPEndDisplayList(),\n};\n')
    return '\n'.join(out) + '\n' + '\n'.join(dl)

# ---------------------------------------------------------------- glasses
def face_y(x, z):
    """Approximate front surface of the (nose-shrunk) face in head space."""
    az = abs(z)
    base = 103 - 0.0009 * (x - 135) ** 2
    if az < 45: return base - 0.25 * az
    if az < 90: return base - 11 - (az - 45) * 0.95
    return base - 54 - (az - 90) * 1.9

def rounded_rect(cx, cz, hx, hz, r, n_corner=3):
    pts = []
    for (sx, sz, a0) in ((1, 1, 0), (-1, 1, 90), (-1, -1, 180), (1, -1, 270)):
        ccx = cx + sx * (hx - r); ccz = cz + sz * (hz - r)
        for i in range(n_corner + 1):
            a = math.radians(a0 + 90 * i / n_corner)
            pts.append((ccx + r * math.cos(a), ccz + r * math.sin(a)))
    return pts

def glasses_mesh():
    m = Mesh()
    OFF = 13; DEPTH = 6; W = 7
    for side in (1, -1):
        cx, cz = 132, side * 33
        outer = rounded_rect(cx, cz, 26, 28, 15)
        inner = rounded_rect(cx, cz, 26 - W, 28 - W, 11)
        n = len(outer)
        def P(pt, front):
            x, z = pt; y = face_y(x, z) + OFF + (DEPTH if front else 0)
            return (x, y, z)
        for i in range(n):
            j = (i + 1) % n
            o0, o1, i0, i1 = outer[i], outer[j], inner[i], inner[j]
            q = [P(o0, 1), P(o1, 1), P(i1, 1), P(i0, 1)]
            m.quad_flat(*(q if side > 0 else q[::-1]) if False else q)  # front face
            m.quad_flat(P(o1, 1), P(o0, 1), P(o0, 0), P(o1, 0))      # outer wall
            m.quad_flat(P(i0, 1), P(i1, 1), P(i1, 0), P(i0, 0))      # inner wall
    # bridge
    y = face_y(140, 0) + OFF
    m.quad_flat((144, y + DEPTH, -7), (144, y + DEPTH, 7), (137, y + DEPTH, 7), (137, y + DEPTH, -7))
    m.quad_flat((144, y + DEPTH, 7), (144, y + DEPTH, -7), (144, y, -7), (144, y, 7))
    m.quad_flat((137, y, 7), (137, y, -7), (137, y + DEPTH, -7), (137, y + DEPTH, 7))
    # temple arms: outer lens edge back over the ear
    for side in (1, -1):
        z0 = side * 59
        p = [(142, face_y(142, z0) + OFF + 2, z0), (140, 36, side * 118), (134, -30, side * 130), (122, -66, side * 124)]
        for a, b in zip(p, p[1:]):
            up = (6, 0, 0); out = (0, 0, side * 5)
            a0, a1 = add(a, up), sub(a, up); b0, b1 = add(b, up), sub(b, up)
            m.quad_flat(add(a0, out), add(b0, out), add(b1, out), add(a1, out))  # outer
            m.quad_flat(a0, b0, add(b0, out), add(a0, out))                      # top
    fix_winding(m)
    return m

def fix_winding(m, outward_from=(110, 0, 0)):
    """Make every triangle face away from the head centre (front-face culling safe)."""
    for k, (a, b, c) in enumerate(m.t):
        pa, pb, pc = (m.v[i][0] for i in (a, b, c))
        n = cross(sub(pb, pa), sub(pc, pa))
        ctr = mul(add(add(pa, pb), pc), 1 / 3)
        if sum(x * y for x, y in zip(n, sub(ctr, outward_from))) < 0:
            m.t[k] = (a, c, b)

# ---------------------------------------------------------------- ponytail
def ponytail_mesh():
    m = Mesh(); sc = Mesh()
    # spine (x up, y forward) in the head's mid-plane, from under the cap's back opening
    spine = [(124, -112), (118, -160), (98, -200), (64, -224), (26, -230), (-8, -218), (-30, -196)]
    radii = [30, 40, 45, 42, 34, 21, 6]
    SIDES = 8
    rings = []
    for i, ((x, y), r) in enumerate(zip(spine, radii)):
        a = spine[max(0, i - 1)]; b = spine[min(len(spine) - 1, i + 1)]
        tx, ty = b[0] - a[0], b[1] - a[1]; L = math.hypot(tx, ty)
        nx, ny = -ty / L, tx / L       # in-plane normal
        ring = []
        for s in range(SIDES):
            ang = 2 * math.pi * s / SIDES
            ca, sa = math.cos(ang), math.sin(ang)
            off = (nx * ca * r, ny * ca * r, sa * r * 1.15)
            p = (x + off[0], y + off[1], off[2])
            ring.append(m.add(p, off))
        rings.append(ring)
    for r0, r1 in zip(rings, rings[1:]):
        for s in range(SIDES):
            a, b, c, d = r0[s], r0[(s + 1) % SIDES], r1[(s + 1) % SIDES], r1[s]
            m.tri(a, b, c); m.tri(a, c, d)
    # cap the root
    for s in range(1, SIDES - 1):
        m.tri(rings[0][0], rings[0][s + 1], rings[0][s])
    # orient using spine (outward from local axis)
    for k, (a, b, c) in enumerate(m.t):
        pa, pb, pc = (m.v[i][0] for i in (a, b, c))
        n = cross(sub(pb, pa), sub(pc, pa))
        ctr = mul(add(add(pa, pb), pc), 1 / 3)
        # nearest spine point
        sp = min(spine, key=lambda q: (q[0] - ctr[0]) ** 2 + (q[1] - ctr[1]) ** 2)
        if sum(x * y for x, y in zip(n, sub(ctr, (sp[0], sp[1], 0)))) < 0:
            m.t[k] = (a, c, b)
    # scrunchie: fat short ring around the root
    (x0, y0), (x1, y1) = spine[0], spine[1]
    cx, cy = x0 + (x1 - x0) * 0.35, y0 + (y1 - y0) * 0.35
    tx, ty = x1 - x0, y1 - y0; L = math.hypot(tx, ty); tx, ty = tx / L, ty / L
    nx, ny = -ty, tx
    R = 41; H = 9; SS = 10
    rings = []
    for h in (-H, 0, H):
        rr = R if h == 0 else R - 6
        ring = []
        for s in range(SS):
            ang = 2 * math.pi * s / SS
            ca, sa = math.cos(ang), math.sin(ang)
            off = (nx * ca * rr, ny * ca * rr, sa * rr * 1.1)
            p = (cx + tx * h + off[0], cy + ty * h + off[1], off[2])
            ring.append(sc.add(p, add(off, (tx * h * 2, ty * h * 2, 0))))
        rings.append(ring)
    for r0, r1 in zip(rings, rings[1:]):
        for s in range(SS):
            a, b, c, d = r0[s], r0[(s + 1) % SS], r1[(s + 1) % SS], r1[s]
            sc.tri(a, b, c); sc.tri(a, c, d)
    for k, (a, b, c) in enumerate(sc.t):
        pa, pb, pc = (sc.v[i][0] for i in (a, b, c))
        n = cross(sub(pb, pa), sub(pc, pa))
        ctr = mul(add(add(pa, pb), pc), 1 / 3)
        axis_pt = (cx + tx * ((ctr[0]-cx)*tx + (ctr[1]-cy)*ty), cy + ty * ((ctr[0]-cx)*tx + (ctr[1]-cy)*ty), 0)
        if sum(x * y for x, y in zip(n, sub(ctr, axis_pt))) < 0:
            sc.t[k] = (a, c, b)
    return m, sc

def bib_heart_mesh():
    # torso-bone space: X up, Y forward, Z sideways; bib front is at Y~88 around X~10.
    m = Mesh(); N = 28; S = 1.6
    cx, cz = 12, 0
    def surf(x): return 89 - max(0, x - 9) * 0.2 + 3
    ctr = m.add((cx, surf(cx), cz), (10, 120, 0))
    ring = []
    for i in range(N):
        t = 2 * math.pi * i / N
        hx = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        hz = 16 * math.sin(t) ** 3
        x, z = cx + hx * S * 0.8, cz + hz * S * 0.8
        ring.append(m.add((x, surf(x), z), (10, 120, 0)))
    for i in range(N):
        m.tri(ctr, ring[i], ring[(i + 1) % N])
    fix_winding(m, outward_from=(cx, 0, 0))
    return m

# Front surface (Y) of the reshaped lower face, sampled from the patched mesh.
_MOUTH_X = [40, 46, 52, 58, 64]
_MOUTH_Z = [0, 8, 16, 24, 32]
_MOUTH_Y = [[90, 90, 90, 90, 88], [94, 94, 94, 93, 92], [102, 97, 97, 96, 95],
            [108, 106, 105, 99, 98], [113, 111, 110, 108, 100]]

def mouth_surface(x, z):
    def interp(xs, v):
        v = max(xs[0], min(xs[-1], v))
        for i in range(len(xs) - 1):
            if v <= xs[i + 1]:
                return i, (v - xs[i]) / (xs[i + 1] - xs[i])
        return len(xs) - 2, 1.0
    i, fx = interp(_MOUTH_X, x); j, fz = interp(_MOUTH_Z, abs(z))
    y00, y01 = _MOUTH_Y[i][j], _MOUTH_Y[i][j + 1]
    y10, y11 = _MOUTH_Y[i + 1][j], _MOUTH_Y[i + 1][j + 1]
    return (y00 * (1 - fz) + y01 * fz) * (1 - fx) + (y10 * (1 - fz) + y11 * fz) * fx

def mouth_mesh():
    # open "D" smile; dark mouth + tongue as separate meshes so they can be lit separately
    mouth = Mesh(); tongue = Mesh(); W = 24; N = 12
    def strip(m, top, bot, lift, zs):
        cols = []
        for z in zs:
            xt, xb = top(z), bot(z)
            cols.append((m.add((xt, mouth_surface(xt, z) + lift, z), (20, 120, 0)),
                         m.add((xb, mouth_surface(xb, z) + lift, z), (20, 120, 0))))
        for (a, b), (c, d) in zip(cols, cols[1:]):
            m.tri(a, b, d); m.tri(a, d, c)
        fix_winding(m, outward_from=(50, 0, 0))
    zs = [-W + 2 * W * i / N for i in range(N + 1)]
    top = lambda z: 53 + 0.014 * z * z
    bot = lambda z: 53 - 11 * max(0.0, 1 - (z / W) ** 2) + 0.014 * z * z
    strip(mouth, top, bot, 3, zs)
    tz = [-11 + 22 * i / 6 for i in range(7)]
    strip(tongue, lambda z: 47 - 0.5 * max(0.0, 1 - (z / 11) ** 2) + 0.016 * z * z,
          lambda z: 53 - 11 * max(0.0, 1 - (z / W) ** 2) + 0.014 * z * z + 1.2, 4, tz)
    return mouth, tongue

def light(rgb):
    a, b = lc(rgb)
    return f'    gsSPLightColor(LIGHT_1, {a}),\n    gsSPLightColor(LIGHT_2, {b}),\n'

def parts_source():
    g = glasses_mesh(); p, s = ponytail_mesh()
    src = ['// Generated by haylies-world-64/tools/apply_haylie.py - Haylie head extras.\n',
           emit('haylie_glasses', g), emit('haylie_ponytail', p), emit('haylie_scrunchie', s),
           emit('haylie_bib_heart_mesh', bib_heart_mesh())]
    mo, to = mouth_mesh()
    src += [emit('haylie_mouth', mo), emit('haylie_tongue', to)]
    src.append('const Gfx haylie_bib_heart_dl[] = {\n' + light(BIB) +
               '    gsSPDisplayList(haylie_bib_heart_mesh_dl),\n    gsSPEndDisplayList(),\n};\n')
    src.append('// Geometry only: used by the Metal Cap heads (env-mapped, no light changes).\n'
               'const Gfx haylie_head_extras_metal_dl[] = {\n'
               '    gsSPDisplayList(haylie_glasses_dl),\n'
               '    gsSPDisplayList(haylie_ponytail_dl),\n'
               '    gsSPDisplayList(haylie_scrunchie_dl),\n'
               '    gsSPDisplayList(haylie_mouth_dl),\n'
               '    gsSPEndDisplayList(),\n};\n')
    src.append('// Lit version: called at the end of every normal head (shade-only combiner).\n'
               'const Gfx haylie_head_extras_dl[] = {\n' + light(GLASS) +
               '    gsSPDisplayList(haylie_glasses_dl),\n' + light(HAIR) +
               '    gsSPDisplayList(haylie_ponytail_dl),\n' + light(SCRUNCH) +
               '    gsSPDisplayList(haylie_scrunchie_dl),\n' + light(MOUTH) +
               '    gsSPDisplayList(haylie_mouth_dl),\n' + light(TONGUE) +
               '    gsSPDisplayList(haylie_tongue_dl),\n'
               '    gsSPEndDisplayList(),\n};\n')
    return '\n'.join(src)

# ---------------------------------------------------------------- textures (32x32 RGBA16)
SS = 8  # supersampling

def canvas():
    return Image.new('RGBA', (32 * SS, 32 * SS), (0, 0, 0, 0))

def finish(im, path):
    im = im.resize((32, 32), Image.LANCZOS)
    px = im.load()
    for y in range(32):
        for x in range(32):
            r, g, b, a = px[x, y]
            px[x, y] = (r, g, b, 255) if a >= 128 else (0, 0, 0, 0)  # RGBA16 has 1-bit alpha
    im.save(path)

def E(d, box, **kw):
    d.ellipse([c * SS for c in box], **kw)

def heart(d, cx, cy, s, fill):
    pts = []
    for i in range(200):
        t = 2 * math.pi * i / 200
        x = 16 * math.sin(t) ** 3
        y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        pts.append(((cx + x * s / 16) * SS, (cy - y * s / 16) * SS))
    d.polygon(pts, fill=fill)

def tex_logo(path, cx=15.5, cy=14.0, s=10.5):
    im = canvas(); d = ImageDraw.Draw(im)
    heart(d, cx, cy, s, (255, 255, 255, 255))
    finish(im, path)

def tex_logo_opaque(path, cx=15.5, cy=15.5, s=10.5):
    im = Image.new('RGBA', (32 * SS, 32 * SS), PINK + (255,)); d = ImageDraw.Draw(im)
    heart(d, cx, cy, s, (255, 255, 255, 255))
    finish(im, path)

IRIS = (110, 62, 28, 255); IRIS_D = (62, 32, 14, 255); LASH = (40, 22, 18, 255); BROW = (112, 70, 38, 255)
EYE_C = ((5.4, 18.0), (24.6, 18.0))   # u,v of each eye centre (matches the eye mesh UVs)

def eye_open(d, cx, cy, mirror):
    E(d, (cx - 5.2, cy - 6.8, cx + 5.2, cy + 6.8), fill=(255, 255, 255, 255))
    E(d, (cx - 4.4, cy - 4.8, cx + 4.4, cy + 6.2), fill=IRIS_D)
    E(d, (cx - 3.6, cy - 3.9, cx + 3.6, cy + 5.3), fill=IRIS)
    E(d, (cx - 1.9, cy - 1.5, cx + 1.9, cy + 2.9), fill=(20, 10, 6, 255))
    E(d, (cx - 2.4 * mirror - 1.3, cy - 3.4, cx - 2.4 * mirror + 1.3, cy - 0.8), fill=(255, 255, 255, 255))
    E(d, (cx + 1.8 * mirror - 0.7, cy + 2.4, cx + 1.8 * mirror + 0.7, cy + 3.8), fill=(255, 255, 255, 255))
    lashes(d, cx, cy - 6.4, mirror)

def lashes(d, cx, cy, mirror, w=5.8):
    d.arc([(cx - w) * SS, (cy - 1.2) * SS, (cx + w) * SS, (cy + 6) * SS], 190, 350, fill=LASH, width=int(1.6 * SS))
    ox = cx + mirror * (w - 0.3)
    d.line([(ox * SS, (cy + 1.4) * SS), ((ox + mirror * 1.9) * SS, (cy - 0.6) * SS)], fill=LASH, width=int(1.3 * SS))

def brows(d):
    for (cx, _), mirror in zip(EYE_C, (-1, 1)):
        d.arc([(cx - 4.8) * SS, 3.4 * SS, (cx + 4.8) * SS, 8.4 * SS], 200, 340, fill=BROW, width=int(1.3 * SS))

def tex_eyes(path, state):
    im = canvas(); d = ImageDraw.Draw(im)
    brows(d)
    for (cx, cy), mirror in zip(EYE_C, (-1, 1)):
        if state == 'open':
            eye_open(d, cx, cy, mirror)
        elif state == 'half':
            eye_open(d, cx, cy, mirror)
            # eyelid: erase top half back to skin (transparent shows lit skin)
            d.rectangle([(cx - 6) * SS, (cy - 7.5) * SS, (cx + 6) * SS, (cy - 0.5) * SS], fill=(0, 0, 0, 0))
            d.line([((cx - 4.8) * SS, (cy - 0.5) * SS), ((cx + 4.8) * SS, (cy - 0.5) * SS)], fill=LASH, width=int(1.6 * SS))
            ox = cx + mirror * 4.6
            d.line([(ox * SS, (cy - 0.5) * SS), ((ox + mirror * 1.8) * SS, (cy - 2.2) * SS)], fill=LASH, width=int(1.2 * SS))
        else:  # closed: happy curve
            d.arc([(cx - 4.8) * SS, (cy - 2.5) * SS, (cx + 4.8) * SS, (cy + 3.5) * SS], 20, 160, fill=LASH, width=int(1.6 * SS))
            ox = cx + mirror * 4.4
            d.line([(ox * SS, (cy + 1.4) * SS), ((ox + mirror * 1.8) * SS, (cy - 0.2) * SS)], fill=LASH, width=int(1.2 * SS))
    finish(im, path)

def tex_mouth(path):
    # mustache UVs are mirrored about u=0 (face centre), v grows downward (chin).
    im = canvas(); d = ImageDraw.Draw(im)
    E(d, (19, 12, 30, 21), fill=(255, 150, 160, 255))       # blush
    # smile: from centre (u~0,v~19) curving up to the corner (u~11,v~14)
    finish(im, path)

def tex_hair_lock(path):
    # sideburn UV: covers the strip in front of each ear; fill with brown hair strands.
    im = canvas(); d = ImageDraw.Draw(im)
    base = HAIR + (255,); dark = (0x5e, 0x37, 0x1a, 255); hi = (0xb0, 0x78, 0x48, 255)
    d.polygon([(0, 0), (30 * SS, 0), (32 * SS, 10 * SS), (26 * SS, 24 * SS), (14 * SS, 32 * SS), (2 * SS, 30 * SS), (0, 16 * SS)], fill=base)
    for i in range(4):
        x = 6 + i * 6.5
        d.line([(x * SS, 0), ((x - 5) * SS, 28 * SS)], fill=dark, width=int(0.7 * SS))
    finish(im, path)

def tex_hud_head(path):
    # 16x16 lives icon: Haylie's head (pink heart cap, glasses, brown ponytail)
    K = 16; Z = 12
    im = Image.new('RGBA', (K * Z, K * Z), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    def e(b, c): d.ellipse([v * Z for v in b], fill=c)
    def r(b, c): d.rectangle([v * Z for v in b], fill=c)
    hair = HAIR + (255,); pink = PINK + (255,); skin = SKIN + (255,); dk = (40, 22, 18, 255)
    e((0.2, 6.0, 5.6, 13.6), hair)                 # ponytail (left)
    e((2.6, 3.4, 14.4, 15.6), hair)                # hair behind face
    e((3.8, 5.2, 13.8, 15.4), skin)                # face
    e((2.4, 0.4, 14.6, 9.0), pink)                 # cap dome
    r((2.4, 5.6, 15.8, 7.4), pink)                 # brim
    pts = []
    for i in range(60):
        t = 2 * math.pi * i / 60
        x = 16 * math.sin(t) ** 3; y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        pts.append(((8.6 + x * 2.4 / 16) * Z, (3.7 - y * 2.4 / 16) * Z))
    d.polygon(pts, fill=(255, 255, 255, 255))
    gl = GLASS + (255,)
    for cx in (6.9, 11.1):
        d.rectangle([(cx - 1.9) * Z, 8.2 * Z, (cx + 1.9) * Z, 11.4 * Z], outline=gl, width=int(0.8 * Z))
        r((cx - 0.5, 9.2, cx + 0.5, 10.6), dk)
    r((8.6, 9.2, 9.4, 9.8), gl)
    e((7.6, 12.6, 10.4, 13.9), (140, 34, 60, 255))  # smile
    im = im.resize((K, K), Image.BOX)
    px = im.load()
    for y in range(K):
        for x in range(K):
            c = px[x, y]
            px[x, y] = c[:3] + (255,) if c[3] >= 128 else (0, 0, 0, 0)
    im.save(path)

# ---------------------------------------------------------------- apply
def patch_mario_model():
    f = MARIO / 'model.inc.c'; text = f.read_text()
    text = recolor(text)
    text = edit_vtx_arrays(text, is_head_array, reshape_head)
    # logo DLs: draw over pink (transparent texels show the shade colour)
    for dl in ('mario_m_logo_dl', 'mario_low_poly_mario_m_logo_dl'):
        text, n = re.subn(rf'(const Gfx {dl}\[\] = \{{\n)', r'\1' + light(PINK).replace('\\', '\\\\'), text)
        assert n == 1, dl
    # include generated parts ahead of the first head DL
    anchor = text.index('const Gfx mario_butt_dl[]')
    anchor = text.rfind('\n//', 0, anchor) + 1
    text = text[:anchor] + '#include "actors/mario/haylie_parts.inc.c"\n\n' + text[anchor:]
    # every normal head (high + low poly, cap on + off, all eye states) ends with face DL
    n_total = 0
    for face in ('mario_face_cap_on_dl', 'mario_face_cap_off_dl',
                 'mario_low_poly_face_cap_on_dl', 'mario_low_poly_face_cap_off_dl'):
        needle = f'    gsSPDisplayList({face}),\n    gsSPEndDisplayList(),'
        n = text.count(needle); n_total += n
        text = text.replace(needle, f'    gsSPDisplayList({face}),\n    gsSPDisplayList(haylie_head_extras_dl),\n    gsSPEndDisplayList(),')
    assert n_total >= 24, f'expected >=24 head DLs, patched {n_total}'
    # metal heads
    for dl, last in (('mario_metal_cap_on_shared_dl', 'mario_face_back_hair_cap_on_dl'),
                     ('mario_metal_cap_off_shared_dl', 'mario_face_hair_cap_off_dl')):
        pat = rf'(const Gfx {dl}\[\] = \{{.*?gsSPDisplayList\({last}\),\n)(    gsSPEndDisplayList\(\),)'
        text, n = re.subn(pat, r'\1    gsSPDisplayList(haylie_head_extras_metal_dl),\n\2', text, count=1, flags=re.S)
        assert n == 1, dl
    # heart on the bib (normal + medium poly torso, and metal torso geometry)
    for dl, shirt in (('mario_torso_dl', 'mario_tshirt_shared_dl'),
                      ('mario_medium_poly_torso_dl', 'mario_medium_poly_tshirt_shared_dl')):
        pat = rf'(const Gfx {dl}\[\] = \{{.*?gsSPDisplayList\({shirt}\),\n)'
        text, n = re.subn(pat, r'\1    gsSPDisplayList(haylie_bib_heart_dl),\n', text, count=1, flags=re.S)
        assert n == 1, dl
    text, n = re.subn(r'(const Gfx mario_metal_torso_shared_dl\[\] = \{.*?gsSPDisplayList\(mario_tshirt_shared_dl\),\n)',
                      r'\1    gsSPDisplayList(haylie_bib_heart_mesh_dl),\n', text, count=1, flags=re.S)
    assert n == 1, 'metal torso'
    f.write_text(text)
    (MARIO / 'haylie_parts.inc.c').write_text(parts_source())
    return n_total

def patch_cap_actor():
    f = CAP / 'model.inc.c'; text = recolor(f.read_text()); f.write_text(text)
    tex_logo_opaque(CAP / 'mario_cap_logo.rgba16.png')

def main():
    n = patch_mario_model()
    patch_cap_actor()
    tex_logo(MARIO / 'mario_logo.rgba16.png')
    tex_eyes(MARIO / 'mario_eyes_center.rgba16.png', 'open')
    tex_eyes(MARIO / 'mario_eyes_half_closed.rgba16.png', 'half')
    tex_eyes(MARIO / 'mario_eyes_closed.rgba16.png', 'closed')
    tex_mouth(MARIO / 'mario_mustache.rgba16.png')
    tex_hair_lock(MARIO / 'mario_sideburn.rgba16.png')
    tex_hud_head(HUD_HEAD)
    print(f'Haylie patch applied: {n} head display lists extended, textures regenerated.')

if __name__ == '__main__':
    main()
