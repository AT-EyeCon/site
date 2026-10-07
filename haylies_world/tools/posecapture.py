"""Emulator screenshot sheet of every pose x form.

Makes a DEBUG-ONLY copy of a built ROM in which the player-draw routine reads its pose from
free RAM $0F5E instead of $13E0 (bank 00: $E326/$E3A6/$E406), then boots it fresh, enters
Yoshi's House, forces each pose and power-up, and screenshots the real PPU output."""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from emu import Emu, boot_to_playable
from PIL import Image, ImageDraw

def debug_rom(src, dst):
    r = bytearray(open(src, 'rb').read())
    for pc in (0x6327, 0x63A7, 0x6407):
        assert r[pc:pc + 2] == b'\xe0\x13'; r[pc:pc + 2] = b'\x5e\x0f'
    open(dst, 'wb').write(r)

def main(rom, out):
    dbg = os.path.join(os.path.dirname(out), '_debug_pose.sfc'); debug_rom(rom, dbg)
    e = Emu(dbg); assert boot_to_playable(e), 'boot failed'
    e.run(60)
    forms = [('Small', 0), ('Super', 1), ('Cape', 2), ('Fire', 3)]
    S, C = 3, 0x46
    cell = 48 * S
    sheet = Image.new('RGB', (110 + 35 * (48 * S // 2), len(forms) * 2 * (56 * S // 2 + 14)), (255, 255, 255))
    d = ImageDraw.Draw(sheet)
    for fi, (name, pw) in enumerate(forms):
        for p in range(C):
            r = e.ram(); r[0x19] = pw; r[0x0F5E] = p
            e.run(3); r = e.ram(); r[0x0F5E] = p
            e.run(1)
            x, y = r[0x7E], r[0x80]
            im = e.shot().crop((x - 16, y - 18, x + 32, y + 38)).resize((48 * S // 2, 56 * S // 2), Image.NEAREST)
            col, row = p % 35, fi * 2 + p // 35
            X, Y = 110 + col * (48 * S // 2), row * (56 * S // 2 + 14)
            sheet.paste(im, (X, Y + 14)); d.text((X + 2, Y + 1), '%02X' % p, fill=(0, 0, 0))
            if col == 0: d.text((4, Y + 40), name + ' Haylie', fill=(200, 30, 120))
    sheet.save(out); os.remove(dbg)

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
