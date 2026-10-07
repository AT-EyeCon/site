"""Fresh power-on smoke test for MKII SNES builds (no save states).

Boots, reaches character select, P1 picks the Mileena cell, P2 joins and picks the
Kitana cell, fights a little (walk, crouch, jump, punch, kick, take hits) and
writes screenshots. Usage: mk2_smoke.py CORE ROM OUTDIR
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from snes_emu import Emu


def run(core, rom, out, p1=('DOWN', 'DOWN'), p2=('DOWN', 'LEFT'), fight=True):
    os.makedirs(out, exist_ok=True)
    e = Emu(core, rom)
    shots = []

    def shot(name):
        p = os.path.join(out, name + '.png'); e.screenshot(p); shots.append(p)

    e.run(700); shot('01_boot')
    for _ in range(8): e.press(['START'], 3, release=60)
    e.run(120); shot('02_title')
    e.press(['START'], 3, release=120)
    e.press(['START'], 3, release=120); shot('03_select')
    e.press(['START'], 3, port=1, release=60)
    for b in p1: e.press([b], 3, release=10)
    shot('04_p1_cursor')
    e.press(['A'], 3, release=30)
    for b in p2: e.press([b], 3, port=1, release=10)
    shot('05_p2_cursor')
    e.press(['A'], 3, port=1, release=30)
    e.run(120); shot('06_versus')
    if not fight: return e, shots
    e.run(420); shot('07_fight_start')
    e.hold(['RIGHT']); e.run(40); shot('08_walk_fwd'); e.hold([]); e.run(10)
    e.hold(['LEFT']); e.run(30); shot('09_walk_back'); e.hold([]); e.run(10)
    e.hold(['DOWN']); e.run(20); shot('10_crouch'); e.hold([]); e.run(20)
    e.hold(['UP']); e.run(18); shot('11_jump'); e.hold([]); e.run(60)
    e.hold(['RIGHT']); e.run(60); e.hold([])
    e.hold(['Y']); e.run(6); shot('12_punch'); e.hold([]); e.run(20)
    e.hold(['B']); e.run(8); shot('13_kick'); e.hold([]); e.run(30)
    # P2 attacks P1 (hit reaction / knockdown via sweep)
    e.hold(['Y'], port=1); e.run(8); shot('14_p2_punch'); e.hold([], port=1); e.run(4); shot('15_p1_hit'); e.run(30)
    e.hold(['LEFT', 'B'], port=1); e.run(4); e.hold([], port=1)
    e.hold(['X'], port=1); e.run(10); e.hold([], port=1); e.run(10); shot('16_p1_hit2'); e.run(30)
    e.hold(['DOWN', 'X'], port=1); e.run(12); e.hold([], port=1); shot('17_uppercut'); e.run(25); shot('18_knockdown'); e.run(90); shot('19_recovery')
    return e, shots


def contact(shots, path, cols=5):
    from PIL import Image, ImageDraw
    ims = [Image.open(s) for s in shots]
    rows = (len(ims) + cols - 1) // cols
    m = Image.new('RGB', (256 * cols, 236 * rows))
    d = ImageDraw.Draw(m)
    for i, (im, s) in enumerate(zip(ims, shots)):
        m.paste(im, ((i % cols) * 256, (i // cols) * 236 + 12))
        d.text(((i % cols) * 256 + 2, (i // cols) * 236), os.path.basename(s)[:-4], fill=(255, 255, 0))
    m.save(path)


if __name__ == '__main__':
    e, shots = run(sys.argv[1], sys.argv[2], sys.argv[3])
    contact(shots, os.path.join(sys.argv[3], 'contact.png'))
