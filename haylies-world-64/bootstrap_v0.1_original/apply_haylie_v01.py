#!/usr/bin/env python3
from pathlib import Path
import re, sys

ROOT = Path.cwd()
MODEL = ROOT / 'actors/mario/model.inc.c'
if not MODEL.exists():
    raise SystemExit('ERROR: Run this from the root of a HackerSM64 repository.')

text = MODEL.read_text()
backup = MODEL.with_suffix('.inc.c.haylie_backup')
if not backup.exists():
    backup.write_text(text)

# --- Haylie palette: pink cap/shirt/arms, blue overalls retained, pink shoes ---
# HackerSM64's Mario source uses these red lights for the cap/shirt/arms.
text = text.replace('0xff0000ff', '0xff3f9fff')
text = text.replace('0x7f0000ff', '0x7f1f4fff')

# Change only the normal foot display-list light colors to pink shoes.
for name in ('mario_left_foot', 'mario_right_foot'):
    pat = rf'(const Gfx {name}\[\] = \{{.*?gsSPLightColor\(LIGHT_1, )0x721c0eff(\),.*?gsSPLightColor\(LIGHT_2, )0x390e07ff(\),)'
    text, n = re.subn(pat, rf'\g<1>0xff4fa3ff\g<2>0x7f2751ff\g<3>', text, count=1, flags=re.S)
    if n != 1:
        print(f'WARNING: could not uniquely recolor {name}', file=sys.stderr)

marker = '// HAYLIE_V01_CUSTOM_GEOMETRY\n'
if marker not in text:
    insert_at = text.find('const Gfx mario_face_cap_dl[] = {')
    if insert_at < 0:
        raise SystemExit('ERROR: Could not find mario_face_cap_dl insertion point.')

    custom = r'''// HAYLIE_V01_CUSTOM_GEOMETRY
// Lightweight code-generated identity geometry. This deliberately keeps Mario's
// skeleton and animations so the first Haylie build is mechanically stable.
static const Vtx haylie_glasses_vtx[] = {
    // lens at positive Z, outer 0..3, inner 4..7
    {{{186,128, 78},0,{0,0},{0x7f,0x00,0x00,0xff}}},
    {{{186, 68, 78},0,{0,0},{0x7f,0x00,0x00,0xff}}},
    {{{186, 68, 10},0,{0,0},{0x7f,0x00,0x00,0xff}}},
    {{{186,128, 10},0,{0,0},{0x7f,0x00,0x00,0xff}}},
    {{{187,119, 70},0,{0,0},{0x7f,0x00,0x00,0xff}}},
    {{{187, 77, 70},0,{0,0},{0x7f,0x00,0x00,0xff}}},
    {{{187, 77, 18},0,{0,0},{0x7f,0x00,0x00,0xff}}},
    {{{187,119, 18},0,{0,0},{0x7f,0x00,0x00,0xff}}},
    // lens at negative Z
    {{{186,128,-10},0,{0,0},{0x7f,0x00,0x00,0xff}}},
    {{{186, 68,-10},0,{0,0},{0x7f,0x00,0x00,0xff}}},
    {{{186, 68,-78},0,{0,0},{0x7f,0x00,0x00,0xff}}},
    {{{186,128,-78},0,{0,0},{0x7f,0x00,0x00,0xff}}},
    {{{187,119,-18},0,{0,0},{0x7f,0x00,0x00,0xff}}},
    {{{187, 77,-18},0,{0,0},{0x7f,0x00,0x00,0xff}}},
    {{{187, 77,-70},0,{0,0},{0x7f,0x00,0x00,0xff}}},
    {{{187,119,-70},0,{0,0},{0x7f,0x00,0x00,0xff}}},
    // bridge
    {{{188,104, 18},0,{0,0},{0x7f,0x00,0x00,0xff}}},
    {{{188, 94, 18},0,{0,0},{0x7f,0x00,0x00,0xff}}},
    {{{188, 94,-18},0,{0,0},{0x7f,0x00,0x00,0xff}}},
    {{{188,104,-18},0,{0,0},{0x7f,0x00,0x00,0xff}}},
};

static const Gfx haylie_glasses_dl[] = {
    gsSPLightColor(LIGHT_1, 0xff3f9fff),
    gsSPLightColor(LIGHT_2, 0x7f1f4fff),
    gsSPVertex(haylie_glasses_vtx, 20, 0),
    // positive lens ring
    gsSP2Triangles(0,1,4,0, 1,5,4,0),
    gsSP2Triangles(1,2,6,0, 1,6,5,0),
    gsSP2Triangles(2,3,7,0, 2,7,6,0),
    gsSP2Triangles(3,0,4,0, 3,4,7,0),
    // negative lens ring
    gsSP2Triangles(8,9,12,0, 9,13,12,0),
    gsSP2Triangles(9,10,14,0, 9,14,13,0),
    gsSP2Triangles(10,11,15,0, 10,15,14,0),
    gsSP2Triangles(11,8,12,0, 11,12,15,0),
    // bridge
    gsSP2Triangles(16,17,18,0, 16,18,19,0),
    gsSPEndDisplayList(),
};

static const Vtx haylie_ponytail_vtx[] = {
    {{{ -20, 85,-38},0,{0,0},{0x91,0x20,0x00,0xff}}},
    {{{ -20, 85, 38},0,{0,0},{0x91,0x20,0x00,0xff}}},
    {{{ -20,-25,-38},0,{0,0},{0x91,0x20,0x00,0xff}}},
    {{{ -20,-25, 38},0,{0,0},{0x91,0x20,0x00,0xff}}},
    {{{-155, 45,-17},0,{0,0},{0x91,0x20,0x00,0xff}}},
    {{{-155, 45, 17},0,{0,0},{0x91,0x20,0x00,0xff}}},
    {{{-155,-55,-17},0,{0,0},{0x91,0x20,0x00,0xff}}},
    {{{-155,-55, 17},0,{0,0},{0x91,0x20,0x00,0xff}}},
};

static const Gfx haylie_ponytail_dl[] = {
    gsSPLightColor(LIGHT_1, 0x7a3518ff),
    gsSPLightColor(LIGHT_2, 0x3d1a0cff),
    gsSPVertex(haylie_ponytail_vtx, 8, 0),
    gsSP2Triangles(0,1,5,0, 0,5,4,0),
    gsSP2Triangles(2,6,7,0, 2,7,3,0),
    gsSP2Triangles(0,4,6,0, 0,6,2,0),
    gsSP2Triangles(1,3,7,0, 1,7,5,0),
    gsSP2Triangles(4,5,7,0, 4,7,6,0),
    gsSPEndDisplayList(),
};

'''
    text = text[:insert_at] + custom + text[insert_at:]

# Attach ponytail to both cap-on and cap-off head solids.
text = text.replace(
    'gsSPDisplayList(mario_face_back_hair_cap_on_dl),\n    gsSPEndDisplayList(),',
    'gsSPDisplayList(mario_face_back_hair_cap_on_dl),\n    gsSPDisplayList(haylie_ponytail_dl),\n    gsSPEndDisplayList(),', 1)
text = text.replace(
    'gsSPDisplayList(mario_face_hair_cap_off_dl),\n    gsSPEndDisplayList(),',
    'gsSPDisplayList(mario_face_hair_cap_off_dl),\n    gsSPDisplayList(haylie_ponytail_dl),\n    gsSPEndDisplayList(),', 1)

# Render glasses for every eye state, cap on and cap off.
# Insert immediately after the solid head DL, so current texturing code is not disturbed.
for head_dl in ('mario_face_cap_on_dl', 'mario_face_cap_off_dl'):
    needle = f'gsSPDisplayList({head_dl}),\n    gsSPEndDisplayList(),'
    replacement = f'gsSPDisplayList({head_dl}),\n    gsSPDisplayList(haylie_glasses_dl),\n    gsSPEndDisplayList(),'
    count = text.count(needle)
    if count:
        text = text.replace(needle, replacement)
    else:
        print(f'WARNING: no eye-state endings found for {head_dl}', file=sys.stderr)

MODEL.write_text(text)

# Extracted texture include files are created from the user's baserom.
# Replace the moustache with transparency and the cap M with a white heart.
def rgba16(r,g,b,a=1):
    return ((r>>3)<<11)|((g>>3)<<6)|((b>>3)<<1)|(1 if a else 0)

def write_inc(path, px):
    path = Path(path)
    path.write_text(',\n'.join('0x%04X' % v for v in px) + ',\n')

tex_dir = ROOT / 'actors/mario'
logo = tex_dir / 'mario_logo.rgba16.inc.c'
mustache = tex_dir / 'mario_mustache.rgba16.inc.c'
if logo.exists():
    W=H=32
    pix=[]
    for y in range(H):
        for x in range(W):
            # Parametric heart, scaled to the center of the cap-logo texture.
            X=(x-15.5)/11.0
            Y=(15.5-y)/11.0
            f=(X*X+Y*Y-1)**3 - X*X*Y*Y*Y
            inside=f <= 0 and -1.15 < Y < 1.25
            pix.append(rgba16(255,255,255,1) if inside else rgba16(0,0,0,0))
    write_inc(logo,pix)
else:
    print('WARNING: mario_logo texture not found. Did asset extraction run?', file=sys.stderr)

if mustache.exists():
    write_inc(mustache,[0]*1024)
else:
    print('WARNING: mario_mustache texture not found. Did asset extraction run?', file=sys.stderr)

print('Applied Haylie v0.1 character patch.')
