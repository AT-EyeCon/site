"""Phase 4 cosmetics: status-bar player name, title logo."""
import os, importlib.util, lz2, snesgfx as g, ow

def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m); return m

def name_tiles(hud, width=40):
    px = [[0] * width for _ in range(8)]
    n = len(hud.NAME); w = 5; gap = (width - 2 - n * w) // max(1, n - 1)
    x0 = (width - (n * w + (n - 1) * gap)) // 2
    for i, ch in enumerate(hud.NAME):
        for y, row in enumerate(hud.GLYPHS[ch]):
            for x, c in enumerate(row):
                if c == '#': px[y + 1][x0 + i * (w + gap) + x] = 2
    for y in range(8):
        for x in range(width):
            if px[y][x] == 0 and any(0 <= y + dy < 8 and 0 <= x + dx < width and px[y + dy][x + dx] == 2
                                     for dy in (-1, 0, 1) for dx in (-1, 0, 1)):
                px[y][x] = 1
    return [[r[t * 8:t * 8 + 8] for r in px] for t in range(width // 8)]

def apply(rom, ch, artdir):
    log = []
    hud = _load(os.path.join(artdir, 'hud.py'), 'hud')
    off = ow.GFX_PTR(rom, 0x28); d, n = lz2.decompress(rom, off); d = bytearray(d)
    for k, t in enumerate(name_tiles(hud)):
        d[(0x30 + k) * 16:(0x31 + k) * 16] = g.encode_2bpp(t)
    comp = lz2.compress(d); assert len(comp) <= n, 'GFX28 grew'
    rom[off:off + len(comp)] = comp
    log.append('status-bar name -> %s (GFX28 %x/%x)' % (hud.NAME, len(comp), n))
    title = os.path.join(artdir, 'title.py')
    if os.path.exists(title):
        import title_logo; log += title_logo.apply(rom, _load(title, 'title'))
    return log
