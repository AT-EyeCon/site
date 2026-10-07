"""Fresh-boot gameplay smoke test: boots ROM (no external save states), enters a level, exercises
movement in each power-up state and saves screenshots."""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from emu import Emu, boot_to_playable
from PIL import Image

def run(rom, outdir, tag):
    os.makedirs(outdir, exist_ok=True)
    from emu import boot_to_level, wait_mode
    t = Emu(rom); t.run(420); t.shot(os.path.join(outdir, 'playtest_%s_title.png' % tag), 2); del t
    e = Emu(rom); ok = boot_to_level(e); e.run(60); e.shot(os.path.join(outdir, 'playtest_%s_intro.png' % tag), 2)
    ok = ok and wait_mode(e, 0x0E); e.run(80); e.shot(os.path.join(outdir, 'playtest_%s_overworld.png' % tag), 2)
    ok = ok and wait_mode(e, 0x14); e.run(120)
    shots = []
    e.shot(os.path.join(outdir, 'playtest_%s_level.png' % tag), 2)
    for pw in range(4):
        e.ram()[0x19] = pw; e.run(4)
        seq = [((), 20), (('LEFT',), 20), (('LEFT', 'Y'), 25), (('B', 'LEFT'), 12), (('LEFT',), 10),
               (('RIGHT',), 12), (('DOWN',), 15), (('UP',), 15)]
        for k, (btn, n) in enumerate(seq):
            e.run(n, btn)
            x = e.ram()[0x7E] ; y = e.ram()[0x80]
            im = e.shot()
            box = (max(0, x - 40), max(0, y - 40), min(256, x + 56), min(224, y + 56))
            shots.append(im.crop(box).resize((96 * 2, 96 * 2), Image.NEAREST))
    W = 192; sheet = Image.new('RGB', (W * 8, W * 4))
    for i, s in enumerate(shots): sheet.paste(s, (i % 8 * W, i // 8 * W))
    sheet.save(os.path.join(outdir, 'playtest_%s.png' % tag))
    print('boot ok' if ok else 'BOOT FAILED', 'mode=%02X' % e.ram()[0x100])
    return ok

if __name__ == '__main__':
    run(sys.argv[1], sys.argv[2], sys.argv[3])
