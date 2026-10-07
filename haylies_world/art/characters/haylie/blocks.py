"""Haylie hand-edited player blocks (16x16, final palette indices, Mario-orientation = facing LEFT).

Each entry starts from the clean ROM's block, optionally body-remapped, then rows are replaced.
Index legend: . clear 1 white 2 black 3 brown(hair/skin outline) 6 skin E skin shade 7 hot pink (glasses)
              8/D/9 cap dark/main/light   A/B/C navy/denim/light-blue shirt   F buttons
"""
import os, sys, json
_here = os.path.dirname(os.path.abspath(__file__))
_root = os.path.abspath(os.path.join(_here, '../../..'))
sys.path.insert(0, os.path.join(_root, 'tools'))
import smwplayer as P
_rom = open(os.path.join(_root, 'clean_smw.sfc'), 'rb').read()
_gfx = P.load_gfx32(_rom)
_ch = json.load(open(os.path.join(_here, '..', 'haylie.json')))
HEX = '.123456789ABCDEF'
_remap = {HEX.index(k): HEX.index(v) for k, v in _ch['body_remap'].items()}

def base(t, remap_from=16):
    px = P.block_pixels(_gfx, t)
    return [''.join(HEX[_remap.get(v, v) if y >= remap_from else v] for v in r) for y, r in enumerate(px)]

def blk(t, remap_from=16, src=None, **rows):
    out = base(src if src is not None else t, remap_from)
    if remap_from < 16: out = P.shoe_fix(out, remap_from, _ch.get('shoes', '3'))
    for k, v in rows.items():
        y = int(k[1:]); assert len(v) == 16, (hex(t), k, v); out[y] = v
    return out

BLOCKS = {}
TILES8 = {}

# ---- big Haylie: standard 3/4 head (stand / walk / run / most poses)
BLOCKS[0x70] = blk(0x70,
    r4='...89191988.....',
    r5='...8D111D998....',
    r6='.2888D1DDDD98...',
    r7='.2888833333D98..',
    r8='..2777777733DD8.',
    r9='..2711711733DD8.',
    r10='...7127217E37732',
    r11='..37127217E33332',
    r12='.367777777E33332',
    r13='..3E666666E32332',
    r14='..3E688666E3.232',
    r15='...3E6666EE3..2.')

# ---- template stamping: re-use the hand-drawn 0x70 face on every block that contains the same
#      Mario 3/4 face (shifted). Only pixels identical to Mario's template are replaced, so
#      overlapping hands / caps in a given block are preserved.
_ORIG70 = base(0x70)
_NEW70 = BLOCKS[0x70]

def _find(rows, pats, wild='?'):
    hits = []
    for y in range(16 - len(pats) + 1):
        for x in range(16 - len(pats[0]) + 1):
            if all(all(c == wild or rows[y + j][x + i] == c for i, c in enumerate(p)) for j, p in enumerate(pats)):
                hits.append((x, y))
    return hits

def stamp_face(rows, r0=6, keep=()):
    """Stamp the Haylie 3/4 face where Mario's eyes ('11?11','12621','12621') are found."""
    rows = [list(r) for r in rows]
    for ax, ay in _find([''.join(r) for r in rows], ['11?11', '12621', '12621']):
        ax, ay = ax, ay + 1                     # anchor = left eye white in row 10 of template
        for r in range(r0, 16):
            for c in range(16):
                tx, ty = ax + c - 4, ay + r - 10
                if 0 <= tx < 16 and 0 <= ty < 16 and (tx, ty) not in keep:
                    if rows[ty][tx] == _ORIG70[r][c] and _ORIG70[r][c] != _NEW70[r][c]:
                        rows[ty][tx] = _NEW70[r][c]
    return [''.join(r) for r in rows]

def stamp_cap(rows):
    rows = [list(r) for r in rows]
    for x, y in _find([''.join(r) for r in rows], ['959', 'D154D']):
        rows[y][x] = '1'; rows[y][x + 1] = '9'; rows[y][x + 2] = '1'
        rows[y + 1][x - 1:x + 4] = list('D111D')
        if y + 2 < 16 and rows[y + 2][x + 1] in '2D89': rows[y + 2][x + 1] = '1'
    return [''.join(r) for r in rows]

def auto(t, remap_from=16, **rows):
    return stamp_face(stamp_cap(blk(t, remap_from, **rows)))

# ---- big Haylie: front-facing head (0x84) + template stamping for other front heads
BLOCKS[0x84] = blk(0x84,
    r4='....88199188....',
    r5='...8D911119D8...',
    r6='..8DDDD11DDDD8..',
    r7='..882333333288..',
    r8='..837777777738..',
    r9='..837117711738..',
    r10='.E3E71277217E3E.',
    r11='E33671277217633E',
    r12='E33677777777633E',
    r13='.E366E6666E663E.',
    r14='..366866668663..',
    r15='...36E8888E63...')
_ORIG84 = base(0x84); _NEW84 = BLOCKS[0x84]

def stamp_front(rows, r0=4):
    rows = [list(r) for r in rows]
    for ax, ay in _find([''.join(r) for r in rows], ['11EE11', '126621', '126621']):
        for r in range(r0, 16):
            for c in range(16):
                tx, ty = ax + c - 5, ay + r - 9
                if 0 <= tx < 16 and 0 <= ty < 16 and rows[ty][tx] == _ORIG84[r][c] and _ORIG84[r][c] != _NEW84[r][c]:
                    rows[ty][tx] = _NEW84[r][c]
    return [''.join(r) for r in rows]

# ---- big Haylie: profile looking up (0x0A/0x03 "look up")
BLOCKS[0xA0] = blk(0xA0,
    r5='....28888198....',
    r6='...2888833998...',
    r7='...23333333998..',
    r8='..3332777773D8..',
    r9='.36663712177D98.',
    r10='.36666712173298.',
    r11='.3EEEE777773398.',
    r12='.3686E66662E2D8.',
    r13='..3E666666233D8.')

def back_hair(rows, r_from, tie=None):
    """Back-of-head views: black hair below the cap -> brown with black outline; optional pink hair tie."""
    g = [list(r) for r in rows]
    for y in range(r_from, 16):
        for x in range(16):
            if g[y][x] == '2':
                nb = [g[yy][xx] if 0 <= yy < 16 and 0 <= xx < 16 else ('2' if yy == 16 else '.') for xx, yy in ((x-1,y),(x+1,y),(x,y-1),(x,y+1))]
                if '.' not in nb and nb.count('2') >= 2: g[y][x] = '3'
    if tie:
        for x, y in tie: g[y][x] = '7'
    return [''.join(r) for r in g]

for _t, _r, _tie in [(0x90, 11, [(7, 13), (8, 13)]), (0xB0, 11, [(7, 13), (8, 13)]), (0x72, 11, [(7, 13), (8, 13)]),
                     (0x0F, 11, [(8, 13), (9, 13)]), (0xE3, 16, None), (0x4C, 11, [(8, 13), (9, 13)]),
                     (0x4B, 9, None)]:
    BLOCKS[_t] = back_hair(stamp_cap(base(_t)), _r, _tie)

def shift(rows, dx, dy=0):
    out = [['.'] * 16 for _ in range(16)]
    for y in range(16):
        for x in range(16):
            if 0 <= x + dx < 16 and 0 <= y + dy < 16: out[y + dy][x + dx] = rows[y][x]
    return [''.join(r) for r in out]

def hair_rows(rows, r_from, r_to):
    g = [list(r) for r in rows]; src = [r[:] for r in g]
    for y in range(r_from, r_to + 1):
        for x in range(16):
            if src[y][x] == '2':
                nb = [src[yy][xx] if 0 <= yy < 16 and 0 <= xx < 16 else ('2' if yy == 16 else '.') for xx, yy in ((x-1,y),(x+1,y),(x,y-1),(x,y+1))]
                if '.' not in nb and nb.count('2') >= 2: g[y][x] = '3'
    return [''.join(r) for r in g]

# duck-with-item (pose 1D): head split across E2 (cap) / F2 (face) -> shifted copies of 0x70
_h70 = shift(BLOCKS[0x70], -1)
BLOCKS[0xE2] = blk(0xE2, **{'r%d' % (y + 7): _h70[y] for y in range(3, 9)})
BLOCKS[0xF2] = blk(0xF2, remap_from=6, **{'r%d' % (y - 9): _h70[y] for y in range(9, 15)})
BLOCKS[0xF2][5] = '.3E688666E3322A.'

BLOCKS[0x48] = blk(0x48, r5='...8191988......', r6='...811199D8.....', r7='...8919999D8....',
    r8='.28888DD9998....', r9='23777773399D8...', r10='..711733339DD8..', r11='..7217E3363DDD8.',
    r12='367777E33362DD8.', r13='3E66E6E33362DD8.', r14='3E686663E6E288..', r15='.3E666EEEEE322..')
BLOCKS[0x58] = blk(0x58, remap_from=1, r0='.3EE66666EE32...')
BLOCKS[0xD4] = blk(0xD4, r4='....8191D88.....', r5='....81119DD8....', r6='..288818999D8...',
    r7='.23333333899D8..', r8='...77777338998..', r9='...717117338338.', r10='...727217383113.',
    r11='.36777777E311113', r12='.366666E63311113', r13='.3E8866666E88113'[:16], r14='..3EEEEE68999818',
    r15='...333368999DD8.')
BLOCKS[0xA5] = blk(0xA5, r6='.2888999DDDD8...', r7='233338999DDDD8..', r8='.233333899DDDD8.',
    r9='...77773399DDD8.', r10='...7E7333669DDD8', r11='3666777363E999D8', r12='366666E363E8DDD8',
    r13='3EE866666E38DDD8', r14='.3EEE66E3333888.', r15='..336EEE333332..')
BLOCKS[0x61] = blk(0x61, r4='...81DDD88......', r5='...81199DD8.....', r6='.2888DD999D8....',
    r7='2333333D999D8...', r8='..377773D999D8..', r9='...711733D999D8.', r10='...7217333669D8.',
    r11='3667777E363E99D8', r12='366666E6363E8DD8', r13='3E88666666EE38D8', r14='.3EEEE66E333328.',
    r15='..3336EEE33332..')
BLOCKS[0xC0] = blk(0xC0, remap_from=1, r0='.3336EE333332...')
BLOCKS[0x5F] = blk(0x5F, r8='...8919988......', r9='...811199D8.....', r10='.288881899D8....',
    r11='2333333333D8....', r12='22337777773D8...', r13='.31137117E33D88.', r14='311113777E336E..')
BLOCKS[0x5E] = blk(0x5E, r5='....8191338.....', r6='....81131138....', r7='..28813111138...',
    r8='.233333111138...', r9='.27777311112D8..', r10='..7117731132D88.', r11='...71272333336E.',
    r12='..3677399993363E', r15='..3EEE39999332..')
BLOCKS[0x06] = blk(0x06, remap_from=8, r2='..28119899998...', r3='288888D9333898..', r4='23333333111288..',
    r5='36677721111128A.', r7='.3E88E8866682CCA')
BLOCKS[0x1C] = blk(0x1C, r9='....88199188....', r10='...8991111998...', r11='..899DD11DD998..',
    r12='..892333333298..', r13='..827777777728..')
BLOCKS[0x1D] = blk(0x1D, remap_from=7, r1='..279E2EE2E972..', r4='.3E6E6EEEE6E6E33', r5='..36668888666313')
BLOCKS[0x0B] = blk(0x0B, r12='...8891991988...', r13='..899D1111D998..', r14='.899DDD11DDD998.',
    r15='.89D23333332D98.')
BLOCKS[0x1A] = blk(0x1A, remap_from=6, r0='.8D7712772177D8.', r1='.33E77777777E33.',
    r4='3666E688886E6663', r5='3E66EE6666EE66E3')
BLOCKS[0x85] = blk(0x85, r2='....88199188....', r3='...8991111998...', r4='..8DDDD11DDDD8..',
    r5='..823333333328..', r6='.8D3711771173D8.', r7='.83372177217338.', r8='E83E77777777E38E',
    r9='E3E6666666666E3E', r10='E3666EEEEEE6663E', r11='3166688888866613', r12='3666682222866663',
    r13='3666668888666663')
BLOCKS[0x95] = blk(0x95, remap_from=0)
BLOCKS[0xC7] = hair_rows(stamp_face(stamp_cap(base(0xC7))), 3, 8)
BLOCKS[0x17] = hair_rows(stamp_cap(base(0x17)), 1, 12)
BLOCKS[0xB3] = stamp_front(stamp_cap(base(0xB3)))

# ---- small Haylie: whole body in one 16x16 block; cap tip in the block above
BLOCKS[0x71] = blk(0x71, remap_from=7,
    r0='.237777773DDD8..',
    r1='...71272173368..',
    r2='..37777777363332',
    r3='.366666663333332',
    r4='.3E88EE666E33332',
    r5='..3EEEEE6EE3.32.',
    r6='....333EEE332...')
_ORIG71 = base(0x71); _NEW71 = BLOCKS[0x71]

def remap_rows(rows, r_from):
    rows = [r if y < r_from else ''.join(HEX[_remap.get(HEX.index(c), HEX.index(c))] for c in r) for y, r in enumerate(rows)]
    return P.shoe_fix(rows, min(r_from, 15), _ch.get('shoes', '3'))

def stamp_small(rows, keep_body=False):
    rows = [list(r) for r in rows]; face_end = None
    for ax, ay in _find([''.join(r) for r in rows], ['E2E2E', '62626']):
        face_end = ay + 6
        for r in range(0, 7):
            for c in range(16):
                tx, ty = ax + c - 4, ay + r - 1
                if 0 <= tx < 16 and 0 <= ty < 16 and rows[ty][tx] == _ORIG71[r][c] and _ORIG71[r][c] != _NEW71[r][c]:
                    rows[ty][tx] = _NEW71[r][c]
    rows = [''.join(r) for r in rows]
    if face_end is not None and not keep_body: rows = remap_rows(rows, face_end)
    return rows, face_end

def small_cap(rows):
    g = [list(r) for r in rows]
    for x, y in _find(rows, ['959', '154']):
        g[y][x:x + 3] = list('191'); g[y + 1][x:x + 3] = list('111')
        if y + 2 < 16:
            for xx in range(16):
                if g[y + 2][xx] == '2' and xx > 0 and g[y + 2][xx - 1] in '28': g[y + 2][xx] = '8'
            g[y + 2][x + 1] = '1'
    return [''.join(r) for r in g]

# ---- default: every player block not hand-drawn above gets the automatic cap/face stamp
_AUTO = [0x08, 0x0C, 0x0E, 0x54, 0x5D, 0x64, 0x74, 0x80, 0x93, 0x63, 0x82, 0x85]
for _t in _AUTO:
    BLOCKS.setdefault(_t, stamp_front(auto(_t)))

# small Haylie: every remaining small-form block gets cap + face stamps (body rows remapped)
import build as _B
_cls = _B.classify(_rom)
_small = sorted({P.pose_info(_rom, p, 0)[k] for p in range(0x3D) for k in ('top', 'bot')})
SMALL_REPORT = {}
for _t in _small:
    if _t in BLOCKS: continue
    _r = small_cap(stamp_cap(base(_t)))
    _r2, _fe = stamp_small(_r)
    SMALL_REPORT[_t] = _fe
    if _r2 != base(_t): BLOCKS[_t] = _r2

# ---- small Haylie: hand-drawn variants that the template can't reach
def _sm(t, rf, **rows):
    r = small_cap(stamp_cap(base(t)))
    for k, v in rows.items():
        assert len(v) == 16, (hex(t), k, v); r[int(k[1:])] = v
    return remap_rows(r, rf)

BLOCKS[0x3C] = _sm(0x3C, 7, r0='....77777733DD8.', r1='...7127217336D8.', r2='..3777777736368.',
    r3='.366666663333E2.', r4='.3E88EE66626E2..', r5='313EEEEE6E33113.', r6='3113333EEE311113')
_front = dict(r0='..8933333333D8..', r1='..337127721733..', r2='.36377777777363.', r3='.3E3666666663E3.',
    r4='..336EEEEEE633..', r5='...3E688886E3...', r6='....3EEEEEE3....')
BLOCKS[0xE5] = _sm(0xE5, 7, **_front)
BLOCKS[0xF5] = _sm(0xF5, 7, r0='..8933333333D8..', r1='..837127721738..', r2='..637777777736..',
    r3='.63366666666336.', r4='.E336EEEEEE6313.', r5='..33E68888631113', r6='.3133EEEEEE31113')
BLOCKS[0x39] = _sm(0x39, 7, r0='..893333333333..', r1='.89937127721783.', r2='.896377777777613',
    r3='.863366666663363', r4='.863E6EEEEEE6363', r5='..3EEE688886EE8.', r6='.31333EEEEEE398.')
_b38 = BLOCKS[0x38]; _b38[4] = '..3E8866899332..'; _b38[5] = '...3EEEE89D88...'
BLOCKS[0xF1] = _sm(0xF1, 5, r0='.33371271273D8..', r1='3311377777736D8.', r2='311113688663ED8.')
BLOCKS[0xF0] = _sm(0xF0, 5, r0='....72772736DD8.', r1='.33377777736DD8.', r2='36666663363EDD8.',
    r3='333EE86666E8DD8.', r4='3113EEE66E8288..')
BLOCKS[0xF6] = _sm(0xF6, 6, r0='.837127721732212', r1='.637777777731222', r2='6336666666331212',
    r3='E336EEEEE668222.', r4='.E3E688886E89D8.', r5='...3EEEEEE39DD8.')
BLOCKS[0xE6] = _sm(0xE6, 6, r0='.837127721732212', r1='.337777777731222', r2='3636666666331212',
    r3='3E36EEEEE668222.', r4='.33E688886E89D8.', r5='3DD3EEEEEE39D8..')
BLOCKS[0x3D] = _sm(0x3D, 7, r0='....777777333D8.', r1='...7127217336DD8', r2='..377777773636D8',
    r3='.366666663333ED8', r4='.3E88EE66626E28.', r5='..3EEEEE338E22D8', r6='...33333113321D8')
for _t in (0x19, 0x18):
    BLOCKS[_t] = _sm(_t, 7, r0='.2333333722739D8', r1='.2366666677739D8', r2='..366666666E39D8',
        r3='..366888666339D8')
for _t in (0xC6, 0xD0, 0x69):
    BLOCKS[_t] = remap_rows(back_hair(small_cap(stamp_cap(base(_t))), 3, [(7, 5), (8, 5)]), 7)
BLOCKS[0x3A] = remap_rows(back_hair(small_cap(stamp_cap(base(0x3A))), 3), 7)
BLOCKS[0x4E] = remap_rows(hair_rows(small_cap(stamp_cap(base(0x4E))), 7, 10), 9)
for _t in (0x09, 0x28, 0x29, 0x2A, 0x2B, 0x2C, 0x2D, 0x2E, 0x2F, 0x5A, 0x5C, 0xB6, 0xC4, 0xD5, 0xD6, 0xD7, 0xE0):
    BLOCKS[_t] = hair_rows(BLOCKS.get(_t, small_cap(stamp_cap(base(_t)))), 0, 15)

# shared-pose bodies (poses >= 0x3D are used by every power-up) -> normal body remap
for _t in (0x07, 0x10, 0xA3, 0xE1):
    BLOCKS[_t] = blk(_t, remap_from=0)
# remaining back-of-head views
for _t in (0x5B, 0x6A, 0x6B, 0xF7):
    BLOCKS[_t] = remap_rows(back_hair(small_cap(stamp_cap(base(_t))), 0), 7)
BLOCKS[0xE3] = back_hair(base(0xE3), 10)
for _t in (0x0F, 0x4B, 0x4C, 0x72, 0x90, 0xB0, 0x1B):
    BLOCKS[_t] = hair_rows(BLOCKS.get(_t, base(_t)), 0, 15)

# scorched poses (0x30/0x31): soot-dark Haylie - heart cap, pink glasses around the eyes, no moustache
def _scorched(rows, eye_rows, lower_from):
    g = [list(r) for r in small_cap(stamp_cap(rows))]
    for y in eye_rows:
        for x in range(16):
            if g[y][x] == '1':
                for xx in (x - 1, x + 1):
                    if 0 <= xx < 16 and g[y][xx] in '23': g[y][xx] = '7'
    return hair_rows([''.join(r) for r in g], lower_from, 15)
BLOCKS[0x49] = _scorched(base(0x49), range(9, 13), 13)
BLOCKS[0x4A] = _scorched(base(0x4A), range(9, 13), 13)
BLOCKS[0x6C] = remap_rows(_scorched(base(0x6C), range(0, 4), 4), 8)
BLOCKS[0x4D] = remap_rows(_scorched(base(0x4D), range(0, 4), 4), 8)
BLOCKS[0x5C] = small_cap(stamp_cap(base(0x5C)))
BLOCKS[0x59] = remap_rows(base(0x59), 0)
