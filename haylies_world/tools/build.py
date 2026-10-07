#!/usr/bin/env python3
"""Haylie's World build: clean SMW (USA) ROM -> Haylies_World_SMW_TEST.sfc

usage: python3 tools/build.py [--phase N] [--char art/characters/haylie.json] [--out path]
"""
import sys, os, json, argparse, hashlib, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import lz2, snesgfx as g, smwplayer as P

CLEAN_SHA1 = '6b47bb75d16514b6a476aa0c73a683a2a4c18765'
HEX = '.123456789ABCDEF'

def parse_block(rows):
    assert len(rows) == 16 and all(len(r) == 16 for r in rows), rows
    return [[HEX.index(c) for c in r] for r in rows]

def load_art(path):
    spec = importlib.util.spec_from_file_location('art', path); m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m); return m

def classify(rom):
    """Blocks used only as big/cape bottom tiles -> 'body' (auto remap)."""
    use = {}
    for pw in range(3):
        for p in range(0x46):
            i = P.pose_info(rom, p, pw)
            use.setdefault(i['top'], set()).add(('T', pw)); use.setdefault(i['bot'], set()).add(('B', pw))
    return {k: ('body' if all(r == 'B' and pw > 0 for r, pw in v) else 'manual') for k, v in use.items()}

def fix_checksum(rom):
    rom[0x7FDC:0x7FE0] = b'\xff\xff\x00\x00'
    s = sum(rom) & 0xFFFF
    rom[0x7FDC:0x7FDE] = (s ^ 0xFFFF).to_bytes(2, 'little'); rom[0x7FDE:0x7FE0] = s.to_bytes(2, 'little')

def write_pal(rom, off, hexes):
    for i, h in enumerate(hexes):
        v = g.rgb_to_bgr15(bytes.fromhex(h)); rom[off + 2 * i:off + 2 * i + 2] = v.to_bytes(2, 'little')

def build(phase, char_path, out):
    clean = open(os.path.join(ROOT, 'clean_smw.sfc'), 'rb').read()
    assert hashlib.sha1(clean).hexdigest() == CLEAN_SHA1, 'clean ROM mismatch'
    rom = bytearray(clean)
    ch = json.load(open(char_path))
    slot = ch['replaces']                       # 'mario' (Haylie) / later 'luigi' (Brooklyn)
    artdir = os.path.join(os.path.dirname(char_path), ch['name'].lower())
    gfx = P.load_gfx32(rom)
    log = []
    # ---- Phase 1+: player palette + body remap + hand-drawn head/small blocks
    write_pal(rom, P.PAL_PC[slot], ch['palettes']['normal'])
    write_pal(rom, P.PAL_PC['fire_' + slot], ch['palettes']['fire'])
    remap = {HEX.index(k): HEX.index(v) for k, v in ch['body_remap'].items()}
    blocks = load_art(os.path.join(artdir, 'blocks.py')).BLOCKS
    cls = classify(rom)
    for t, kind in sorted(cls.items()):
        if t in blocks:
            P.put_block(gfx, t, parse_block(blocks[t]))
        elif kind == 'body':
            px = P.block_pixels(gfx, t)
            rows = [''.join(HEX[remap.get(v, v)] for v in r) for r in px]
            if ch.get('shoes'): rows = P.shoe_fix(rows, 0, ch['shoes'])
            P.put_block(gfx, t, parse_block(rows))
    for t, rows in blocks.items():
        if t not in cls: P.put_block(gfx, t, parse_block(rows))
    # extra raw 8x8 tiles inside GFX32 (cape/balloon pieces etc.) if provided
    art = load_art(os.path.join(artdir, 'blocks.py'))
    for t, rows in getattr(art, 'TILES8', {}).items():
        gfx[t * 32:t * 32 + 32] = g.encode_4bpp([[HEX.index(c) for c in r] for r in rows])
    # player 8x8 pieces that live in GFX00 (SP1): shoe tips, hands, sleeves used by some poses
    import ow
    d0, n0 = lz2.decompress(rom, ow.GFX_PTR(rom, 0)); d0 = bytearray(d0)
    for t, rule in ch.get('sp1_tiles', {}).items():
        t = int(t, 16); px = g.decode_3bpp(d0, t)
        m = {int(k): int(v) for k, v in rule.items()}
        d0[t * 24:t * 24 + 24] = g.encode_3bpp([[m.get(v, v) for v in r] for r in px])
    c0 = lz2.compress(d0); assert len(c0) <= n0, 'GFX00 grew'
    rom[ow.GFX_PTR(rom, 0):ow.GFX_PTR(rom, 0) + len(c0)] = c0
    comp = lz2.compress(gfx)
    assert len(comp) <= P.GFX32_MAXLEN, 'GFX32 too big: %x' % len(comp)
    rom[P.GFX32_PC:P.GFX32_PC + len(comp)] = comp
    log.append('GFX32 %x/%x bytes' % (len(comp), P.GFX32_MAXLEN))
    if phase >= 3:
        import phase3; log += phase3.apply(rom, ch, artdir)
    if phase >= 4:
        import phase4; log += phase4.apply(rom, ch, artdir)
    fix_checksum(rom)
    open(out, 'wb').write(rom)
    return rom, log

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--phase', type=int, default=4)
    ap.add_argument('--char', default=os.path.join(ROOT, 'art/characters/haylie.json'))
    ap.add_argument('--out', default=os.path.join(ROOT, 'build/Haylies_World_SMW_TEST.sfc'))
    a = ap.parse_args()
    rom, log = build(a.phase, a.char, a.out)
    print('\n'.join(log)); print('wrote', a.out, hashlib.sha1(rom).hexdigest())
