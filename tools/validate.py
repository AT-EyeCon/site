#!/usr/bin/env python3
"""Repeatable emulator validation from fresh power-on (no save states).

python3 tools/validate.py out/Haylie_Brooklyn_MKII_SNES_TEST.sfc [--core build/emu/snes9x/libretro/snes9x_libretro.so]

Runs: boot -> title -> select -> P1 Mileena slot vs P2 Kitana slot fight (walk, crouch,
jump, punch, kick, hits, knockdown, recovery) -> round win banner; mirror matches;
1P vs CPU fight with blood-object watch; BPS round trip + checksum.  Writes contact
sheets and validation.json next to the ROM.
"""
import argparse, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import mk2_smoke as M, snesrom
from snes_emu import Emu

ROOT = os.path.dirname(HERE)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('rom')
    ap.add_argument('--core', default=os.path.join(ROOT, 'build', 'emu', 'snes9x', 'libretro', 'snes9x_libretro.so'))
    ap.add_argument('--clean', default=os.path.join(ROOT, 'rom', 'Mortal Kombat II (USA) (Rev 1).sfc'))
    a = ap.parse_args()
    out = os.path.splitext(a.rom)[0] + '_validation'
    os.makedirs(out, exist_ok=True)
    res = {}
    rom = open(a.rom, 'rb').read()
    res['checksum_ok'] = snesrom.verify_checksum(bytearray(rom))[0]
    bps = os.path.splitext(a.rom)[0].replace('_TEST', '') + '.bps'
    if os.path.exists(bps) and os.path.exists(a.clean):
        res['bps_reproduces_rom'] = snesrom.bps_apply(open(a.clean, 'rb').read(), open(bps, 'rb').read()) == rom

    # 1. main 2P path + win banner
    e, shots = M.run(a.core, a.rom, out)
    def shot(n):
        p = os.path.join(out, n + '.png'); e.screenshot(p); shots.append(p)
    M.win_round(e, shot)
    M.contact(shots, os.path.join(out, 'contact_main.png'))
    res['main_path_frames'] = len(shots)

    # 2. mirror matches
    mshots = []
    for tag, p1, p2 in (('haylie_mirror', ('DOWN', 'DOWN'), ('DOWN', 'DOWN', 'LEFT', 'LEFT', 'LEFT')),
                        ('brooklyn_mirror', ('DOWN', 'RIGHT', 'RIGHT'), ('DOWN', 'LEFT'))):
        e2, _ = M.run(a.core, a.rom, os.path.join(out, tag), p1=p1, p2=p2, fight=False)
        e2.run(480); p = os.path.join(out, tag + '.png'); e2.screenshot(p); mshots.append(p)
    M.contact(mshots, os.path.join(out, 'contact_mirror.png'), cols=2)

    # 3. 1P vs CPU, watch for blood objects (sprite set 0x16)
    e3 = Emu(a.core, a.rom)
    e3.run(700)
    for _ in range(8): e3.press(['START'], 3, release=60)
    e3.run(120); e3.press(['START'], 3, release=120); e3.press(['START'], 3, release=120)
    for b in ('DOWN', 'DOWN'): e3.press([b], 3, release=10)
    e3.press(['A'], 3, release=30); e3.run(600)
    blood_frames, sets = 0, set()
    for f in range(2400):
        e3.run(1)
        if f % 2: continue
        w = e3.memory(2)
        for s in range(2, 11):
            hi = w[0x4C3D + 2 * s] & 0xFE
            if w[0x4C3C + 2 * s] | w[0x4C3D + 2 * s]: sets.add(hi)
    e3.screenshot(os.path.join(out, 'cpu_fight_end.png'))
    res['effect_sets_seen_vs_cpu'] = sorted(hex(x) for x in sets)
    json.dump(res, open(os.path.join(out, 'validation.json'), 'w'), indent=1)
    print(json.dumps(res, indent=1))


if __name__ == '__main__':
    main()
