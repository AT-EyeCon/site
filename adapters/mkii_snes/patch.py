"""MKII SNES (USA Rev 1) patch primitives: ROM expansion, sprite-set hook, palettes, text."""
import json, os
import sprites as sp
from setbuilder import RomSpace, SetEncoder

HERE = os.path.dirname(os.path.abspath(__file__))
SLOTS = json.load(open(os.path.join(HERE, 'slots.json')))


def asm_hook(routes, orig_set):
    """65816 (M=0, X=0) replacement for `XBA; AND #$00FE` at $85:BF6B.
    routes: list of (char_id, new_set_index). Y = object slot ($84)."""
    c = bytearray()
    c += b'\xeb' + b'\x29\xfe\x00'                       # XBA ; AND #$00FE
    c += b'\xc9' + orig_set.to_bytes(2, 'little')         # CMP #orig
    skip_at = len(c); c += b'\xd0\x00'                    # BNE done
    c += b'\xc0\x04\x00'                                  # CPY #$0004 (only fighter slots 0/2)
    c += b'\xb0' ; ret_orig = len(c); c += b'\x00'        # BCS done_orig
    c += b'\xb9\x10\x4c'                                  # LDA $4C10,y (character id)
    c += b'\x29\xff\x00'                                  # AND #$00FF
    for cid, new in routes:
        c += b'\xc9' + cid.to_bytes(2, 'little')          # CMP #cid
        c += b'\xd0\x04'                                  # BNE +4
        c += b'\xa9' + new.to_bytes(2, 'little')          # LDA #new
        c += b'\x6b'                                      # RTL
    orig_at = len(c)
    c += b'\xa9' + orig_set.to_bytes(2, 'little')         # LDA #orig
    done = len(c); c += b'\x6b'                           # RTL
    c[skip_at + 1] = done - (skip_at + 2)
    c[ret_orig] = orig_at - (ret_orig + 1)
    return bytes(c)


def expand(rom, size=0x400000):
    if len(rom) < size: rom.extend(b'\x00' * (size - len(rom)))
    return RomSpace(rom, 0xF00000)


def install_sets(rom, space, new_sets):
    """new_sets: list of (char_id, header_addr). Relocates the set table and hooks."""
    old_n = SLOTS['set_table_entries']
    idx_tbl = space.alloc(2 * (old_n + len(new_sets)))
    adr_tbl = space.alloc(2 * (old_n + len(new_sets)))
    o = sp.off
    space.write(idx_tbl, rom[o(sp.SET_BANK_TABLE):o(sp.SET_BANK_TABLE) + 2 * old_n])
    space.write(adr_tbl, rom[o(sp.SET_ADDR_TABLE):o(sp.SET_ADDR_TABLE) + 2 * old_n])
    routes = []
    for k, (cid, ha) in enumerate(new_sets):
        i = old_n + k
        space.write(idx_tbl + 2 * i, bytes([ha >> 16, 0]))
        space.write(adr_tbl + 2 * i, bytes([ha & 0xFF, ha >> 8 & 0xFF]))
        routes.append((cid, 2 * i))
    hook = asm_hook(routes, SLOTS['shared_set_index'])
    ha = space.alloc(len(hook)); space.write(ha, hook)
    # JSL hook (replaces XBA ; AND #$00FE)
    site = o(0x85BF6B); assert rom[site:site + 4] == b'\xeb\x29\xfe\x00'
    rom[site:site + 4] = b'\x22' + ha.to_bytes(3, 'little')
    for at, tbl in ((0x85BF78, idx_tbl), (0x85BF7E, adr_tbl)):
        p = o(at); assert rom[p] == 0xBF
        rom[p + 1:p + 4] = tbl.to_bytes(3, 'little')
    return routes


def write_palette(rom, addr, colors):
    """colors: 16 (r,g,b) 0-255 tuples; index 0 kept as stored."""
    p = sp.off(addr)
    for i, (r, g, b) in enumerate(colors):
        if i == 0: continue
        v = (r >> 3) | (g >> 3) << 5 | (b >> 3) << 10
        rom[p + 2 * i:p + 2 * i + 2] = v.to_bytes(2, 'little')


def encode_set(rom, space, images):
    orig = sp.set_header(rom, SLOTS['shared_set_index'])
    enc = SetEncoder(rom, space)
    ha = enc.build(orig, images)
    return ha, enc
