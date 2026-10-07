# Haylie's World (Super Mario World conversion)

Haylie replaces Mario as the native SNES player: every player graphic block in GFX32 is redrawn
(hand-drawn faces + templated variants + body recolour), new player/fire palettes, overworld
sprite, status-bar name, and a "HAYLIE'S WORLD" title logo. No overlays, no code hooks.

## Build
Needs Python 3 + Pillow. Put the clean ROM (headerless, SHA-1 6b47bb75…a4c18765) at `clean_smw.sfc`.

    python3 tools/build.py --phase 4 --out build/Haylies_World_SMW_TEST.sfc
    python3 tools/bps.py clean_smw.sfc build/Haylies_World_SMW_TEST.sfc build/Haylies_World_SMW.bps
    python3 tools/playtest.py build/Haylies_World_SMW_TEST.sfc build final   # needs libretro-snes9x
    python3 tools/posecapture.py build/Haylies_World_SMW_TEST.sfc build/pose_emu.png  # every pose x form, real emulator output

`--phase 1` = player only, `3` = + overworld, `4` = + HUD name/title. The clean ROM is never written.

## Layout
- `tools/lz2.py` LC_LZ2 codec · `smwplayer.py` pose→tile model ($00:E00C/E0CC, DMA formula $00:F636)
- `tools/build.py` pipeline · `phase3.py` overworld · `phase4.py` + `title_logo.py` cosmetics
- `tools/emu.py` headless libretro harness · `playtest.py` fresh-boot test · `preview.py`/`sheet.py` sheets
- `art/characters/haylie.json` palettes + body remap; `art/characters/haylie/` blocks, overworld, hud, title

## Adding Brooklyn (Luigi)
Character data is isolated: copy `haylie.json` → `brooklyn.json` with `"replaces": "luigi"` and a new
art folder. Luigi shares Mario's GFX32 tiles in vanilla SMW, so Brooklyn needs a second player-graphics
bank + a small DMA-pointer hook on `$19`/player number (bank 00 $F636) — that is the one code change required.

## Palette (handoff v1)
Player row idx 6-F: skin ffd2ae, light pink ff62b0 (shoes/glasses/scrunchie), cap+shirt f24fa2 / shade 9c3368 / light ff8cc8,
overalls 2650e8 / 1e40b8 / 142c80, skin shade e0a07c, bib heart + cape ffa8d4. Hair uses shared index 3 (8b5a18 ~ 8a552c).
Fire: white cap/shirt, hot-pink overalls. Hands: bare skin everywhere (incl. GFX00 player pieces).
