"""Phase 3: overworld player sprite + palette (HUD portrait / life icon come from GFX32 already)."""
import os, importlib.util, lz2, snesgfx as g, ow
HEX = '.1234567'

def apply(rom, ch, artdir):
    spec = importlib.util.spec_from_file_location('owart', os.path.join(artdir, 'overworld.py'))
    art = importlib.util.module_from_spec(spec); spec.loader.exec_module(art)
    d, n = ow.load(rom); changed = 0
    for t in ow.PLAYER_BLOCKS:
        px = ow.block(d, t)
        rows = [''.join(HEX[v] for v in r) for r in px]
        new = [art.ROWS.get(r, r) for r in rows]
        changed += sum(a != b for a, b in zip(rows, new))
        ow.put(d, t, [[HEX.index(c) for c in r] for r in new])
    comp = lz2.compress(d)
    assert len(comp) <= n, 'GFX10 grew %x > %x' % (len(comp), n)
    off = ow.GFX_PTR(rom, 0x10); rom[off:off + len(comp)] = comp
    for i, h in enumerate(art.OW_PALETTE):
        v = g.rgb_to_bgr15(bytes.fromhex(h)); rom[ow.OW_PAL_PC + 2 * i:ow.OW_PAL_PC + 2 * i + 2] = v.to_bytes(2, 'little')
    return ['OW sprite rows changed: %d, GFX10 %x/%x bytes' % (changed, len(comp), n)]
