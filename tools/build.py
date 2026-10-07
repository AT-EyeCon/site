#!/usr/bin/env python3
"""Reproducible build: python3 tools/build.py haylie|brooklyn|all [--rom PATH]

Verifies the clean MKII SNES (USA Rev 1) ROM, generates character frames from the
slot's base poses + character art, re-encodes them as new sprite sets in ROM
expansion space, applies palettes/text, fixes the checksum, and writes:
  out/<name>.sfc, out/<name>.bps, sprite sheets and previews.
The source ROM is only ever read.
"""
import argparse, json, os, sys, time
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
sys.path.insert(0, os.path.join(ROOT, 'adapters', 'mkii_snes'))
import numpy as np
from PIL import Image
import snesrom, setbuilder as SB, sprites as sp, render as R, reskin as RS, headfind as HF, patch as P, presentation as PR

ADAPTER = os.path.join(ROOT, 'adapters', 'mkii_snes')
DATA = os.path.join(ADAPTER, 'data')
CHARS = {'haylie': 'mileena', 'brooklyn': 'kitana'}


def load_rom(path):
    data = open(path, 'rb').read()
    h = snesrom.hashes(data)
    if h['sha1'] != P.SLOTS['source_sha1'] or h['size'] != P.SLOTS['source_size']:
        sys.exit('Refusing ROM: expected Mortal Kombat II (USA) (Rev 1) unheadered, SHA-1 %s; got %s (%d bytes)'
                 % (P.SLOTS['source_sha1'], h['sha1'], h['size']))
    return data


def templates(rom, hdr):
    cfg = json.load(open(os.path.join(DATA, 'set8_head_templates.json')))
    T = {}
    for name, t in cfg.items():
        cm = HF.class_map(R.frame_index_image(rom, hdr, t['frame']))
        T[name] = cm[t['y']:t['y'] + 17, t['x']:t['x'] + 17]
    return T


def head_anchors(rom, hdr, T, n_frames, cache):
    if os.path.exists(cache):
        A = json.load(open(cache))
    else:
        A = {}
        for n in range(1, n_frames + 1):
            cm = HF.class_map(R.frame_index_image(rom, hdr, n))
            a = HF.find_head(cm, T)
            if a[5] == 'back':
                # a real back view is (almost) all hair; otherwise the face is visible -> use face templates
                y, x = a[1], a[0]
                win = cm[max(0, y - 6):y + 7, max(0, x - 5):x + 6]
                if (win > 0).sum() and (win == 3).sum() / (win > 0).sum() < 0.7:
                    a = HF.find_head(cm, {k: v for k, v in T.items() if k != 'back'})
            A[str(n)] = a
        json.dump(A, open(cache, 'w'))
    ov = os.path.join(DATA, 'set8_head_overrides.json')
    if os.path.exists(ov):
        for k, v in json.load(open(ov)).items():
            if k.startswith('_'): continue
            A[k] = v
    return A


def character_frames(rom, hdr, cfg, anchors, T, frames_cfg):
    out = {}
    n_frames = frames_cfg['frame_count']
    subs = frames_cfg['family_safe']
    for n in range(1, n_frames + 1):
        src = subs.get(str(n), n)
        if src == 0:
            out[n] = Image.new('P', (R.W, R.H), 0); continue
        base = np.array(R.frame_index_image(rom, hdr, src))
        a = anchors.get(str(src))
        if a and a[0] is None: a = None
        img = RS.reskin(base, a, T, cfg)
        out[n] = Image.fromarray(img.astype(np.uint8), 'P')
    return out


def write_sheet(images, cfg, path, cols=16):
    frames = sorted(images)
    s = R.sheet([images[n] for n in frames], frames, cfg['rgb'], cols=cols)
    s.save(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('target', help='haylie | brooklyn | all | <character id>')
    ap.add_argument('--rom', default=os.environ.get('MK2_ROM', os.path.join(ROOT, 'rom', 'Mortal Kombat II (USA) (Rev 1).sfc')))
    ap.add_argument('--out', default=os.path.join(ROOT, 'out'))
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    t0 = time.time()
    clean = load_rom(args.rom)
    rom = bytearray(clean)
    hdr = sp.set_header(rom, P.SLOTS['shared_set_index'])
    T = templates(rom, hdr)
    frames_cfg = json.load(open(os.path.join(DATA, 'set8_frames.json')))
    anchors = head_anchors(rom, hdr, T, frames_cfg['frame_count'], os.path.join(args.out, '.set8_heads_cache.json'))
    names = ['haylie', 'brooklyn'] if args.target == 'all' else [args.target]
    if not os.path.exists(os.path.join(ROOT, 'characters', names[0], 'character.json')): sys.exit('unknown character ' + names[0])
    space = P.expand(rom)
    new_sets, report = [], {}
    pres = PR.Presentation()
    sel_patches = []
    for name in names:
        cfg = RS.load_character(os.path.join(ROOT, 'characters', name))
        slot = P.SLOTS['fighters'][cfg['fighter_slot']]
        imgs = character_frames(clean, hdr, cfg, anchors, T, frames_cfg)
        ha, enc = P.encode_set(rom, space, imgs)
        new_sets.append((slot['char_id'], ha))
        P.write_palette(rom, int(slot['palette'], 16), cfg['rgb'])
        mp = slot.get('mirror_palette')
        if mp and cfg['palette'].get('mirror_colors') and not slot.get('mirror_palette_shared_with'):
            P.write_palette(rom, int(mp, 16), [tuple(int(h[i:i + 2], 16) for i in (1, 3, 5)) for h in cfg['palette']['mirror_colors']])
        PR.apply(rom, space, cfg, slot, pres)
        sel_patches += PR.portrait_patch(clean, cfg, cfg['fighter_slot'])
        PR.install_vs_portrait(rom, space, cfg, slot['char_id'])
        write_sheet(imgs, cfg, os.path.join(args.out, '%s_MKII_SNES_sprite_sheet.png' % cfg['display_name'].title()))
        report[name] = {'set_header': hex(ha), 'tiles': len(enc.tiles), 'lost_px': sum(enc.lost.values())}
    icon_cfgs = {RS.load_character(os.path.join(ROOT, 'characters', n))['fighter_slot']: RS.load_character(os.path.join(ROOT, 'characters', n)) for n in names}
    ihdr, iimgs, ipals = PR.icon_set_images(clean, icon_cfgs)
    icon_set = SB.SetEncoder(rom, space).build(ihdr, iimgs)
    PR.install_icon_palettes(rom, space, ipals)
    blood = P.SLOTS['blood_set_index']
    blank = SB.build_blank_set(rom, space, sp.set_header(clean, blood))
    P.install_sets(rom, space, new_sets, replace={blood: blank, PR.ICON_SET: icon_set})
    pres.install(rom, space)
    PR.install_select_portraits(rom, space, sel_patches)
    snesrom.fix_checksum(rom)
    base = 'Haylie_Brooklyn_MKII_SNES' if args.target == 'all' else args.target.title() + '_MKII_SNES'
    sfc = os.path.join(args.out, base + ('_TEST.sfc' if args.target == 'all' else '.sfc'))
    open(sfc, 'wb').write(rom)
    bps = snesrom.bps_create(clean, bytes(rom))
    open(os.path.join(args.out, base + '.bps'), 'wb').write(bps)
    assert snesrom.bps_apply(clean, bps) == bytes(rom), 'BPS round-trip failed'
    ok, s = snesrom.verify_checksum(rom)
    report.update({'rom': os.path.basename(sfc), 'checksum_ok': ok, 'checksum': hex(s),
                   'expansion_used_to': hex(space.ptr), 'hashes': snesrom.hashes(bytes(rom)),
                   'seconds': round(time.time() - t0, 1)})
    json.dump(report, open(os.path.join(args.out, base + '_build.json'), 'w'), indent=1)
    print(json.dumps(report, indent=1))


if __name__ == '__main__':
    main()
