# Haylie & Brooklyn — Mortal Kombat II (SNES) character mod

> This branch holds the MKII mod project. The repository's `main` branch is a static site
> (Cloudflare Pages); don't merge this branch into it.

Haylie replaces **Mileena** and Brooklyn replaces **Kitana** in *Mortal Kombat II (USA) (Rev 1)*
for SNES. Both are fully playable, keep the original move sets, and have their own sprites,
palettes, HUD names, win banners, select-screen portraits and versus portraits. The build is
family-safe: blood is removed for everyone, and fatality-victim frames are blank for both kids.

## Quick start

```sh
# 1. put your ROM here (never committed; build refuses any other ROM)
mkdir -p rom && cp "Mortal Kombat II (USA) (Rev 1).sfc" rom/

# 2. build
python3 tools/build.py all        # Haylie + Brooklyn  -> out/Haylie_Brooklyn_MKII_SNES_TEST.sfc + .bps
python3 tools/build.py haylie     # Haylie only        -> out/Haylie_MKII_SNES.sfc + .bps
python3 tools/build.py brooklyn   # Brooklyn only      -> out/Brooklyn_MKII_SNES.sfc + .bps

# 3. optional: automated emulator check (fresh power-on, no save states)
tools/build_emulator.sh build/emu           # instrumented snes9x libretro core
python3 tools/validate.py out/Haylie_Brooklyn_MKII_SNES_TEST.sfc
```

Requirements: Python 3.10+, `numpy`, `pillow`, `scipy`. `MK2_ROM=/path/rom.sfc` or `--rom` overrides the ROM path.

Expected source ROM: unheadered, 3,145,728 bytes, SHA-1 `f6aa5291759e982ea249c4b76f729ca2f4ab1cf4`.
To apply the patch instead of building, use any BPS patcher (Floating IPS, beat, Rom Patcher JS)
on that exact ROM.

## Layout

```
tools/                 generic, game-agnostic
  build.py             build pipeline (verify hash → frames → encode → patch → checksum → BPS → sheets)
  snesrom.py           hashes, HiROM checksum, BPS create/apply
  snes_emu.py          headless libretro frontend (ctypes) + trace/PPU helpers
  build_emulator.sh    builds the instrumented snes9x core
  mk2_smoke.py         scripted fresh-boot play-through
  validate.py          full automated validation
  dis65816.py          tiny 65816 disassembler (RE helper)
  portrait.py          parametric portrait renderer
adapters/mkii_snes/    everything specific to MKII SNES
  sprites.py           sprite-set decoder (frames, tiles, compression)
  setbuilder.py        sprite-set encoder (tiling within original piece budgets)
  reskin.py            base pose → character frame
  headfind.py          head-anchor detection
  patch.py             ROM expansion, set-routing hook, palettes
  presentation.py      nameplates, win banners, select & versus portraits
  slots.json           fighter-slot addresses
  data/                frame groups, head anchors/overrides, select-screen cell map
characters/
  haylie/  brooklyn/   character.json + art/heads.txt (original pixel art)
  _template/           copy this to add a character
docs/MKII_SNES_FEMALE_FIGHTER_SLOT_MAP.md
```

`out/`, `rom/`, `build/` are git-ignored. No ROM data or extracted game graphics are committed.
Character folders contain only original artwork and settings.

## How the art is made

There are no source photos, and MKII animates fighters with 263 digitized frames, so each
character is generated at build time from the slot's own poses:

1. Decode each base frame of the shared Kitana/Mileena set from your ROM.
2. Find the head (template match on colour classes, plus manual overrides in `data/`).
3. Recolour the body into the character's gi palette: arms and legs become sleeves and trousers,
   the silhouette is loosened by 1 px, the waistband becomes the belt (white for Haylie,
   yellow/black for Brooklyn), and Haylie gets a black undershirt V.
4. Remove the original head and hair (Haylie keeps a ponytail recoloured brown), scale the body
   (Haylie 0.86, Brooklyn 0.72 for younger proportions), then paste the character's hand-drawn
   head in the right view (profile/front/back) and angle.
5. Re-tile every frame into new 16×16/8×8 pieces within the original piece budget, and write
   new sprite sets into the expanded ROM.

The heads are hand-drawn pixel art (`characters/*/art/heads.txt`). The portraits are drawn by
`tools/portrait.py` from the `portrait.spec` in each `character.json`. Both are based only on
the approved reference image.

## Adding or changing a character

1. `cp -r characters/_template characters/<id>` and edit `character.json`: `fighter_slot`
   (`mileena` or `kitana`), palette, proportions, belt, glasses, portrait spec.
2. Draw `art/heads.txt` (profile/front/back).
3. Run
   `python3 tools/build.py <id>`.
4. Check `out/<Name>_MKII_SNES_sprite_sheet.png`, then fix heads in
   `adapters/mkii_snes/data/set8_head_overrides.json` if needed.

## Known limitations

* Bodies keep the original poses, scaled and recoloured, so the animation stays faithful. Fists
  are gi-pink (no separate skin-tone hands).
* Head anchors are automatic; a few fast transitional frames (rolls, flips, somersault balls) show
  a hair-coloured blob rather than a clean face.
* Brooklyn mirror match (Brooklyn vs Brooklyn): P2 uses `EF:9193`, which is also Jade's
  palette, so it was left alone and P2 Brooklyn looks grey. Haylie's mirror palette is done.
* Fatalities *performed by* Haylie/Brooklyn still run Mileena's/Kitana's fatality logic, with no
  blood and the victims' own frames. Disabling them needs engine work and is not done.
* Thrown projectiles (set 24: fans, sais) keep their original look.
* Endings were not changed.
