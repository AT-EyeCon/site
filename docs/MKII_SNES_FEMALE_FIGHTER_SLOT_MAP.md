# MKII SNES — Female Fighter Slot Map (Kitana / Mileena / Jade)

Source: **Mortal Kombat II (USA) (Rev 1)**, SNES, unheadered, 3,145,728 bytes, HiROM FastROM.
All addresses are **HiROM CPU addresses** (file offset = `addr & 0x3FFFFF`). Nothing here is
borrowed from Genesis/arcade/DOS — every item was found in this ROM with the instrumented
emulator in `tools/`.

| | |
|---|---|
| MD5 | `a0b9bebbc80958e36292abd9b8fb758e` |
| SHA-1 | `f6aa5291759e982ea249c4b76f729ca2f4ab1cf4` |
| SHA-256 | `ca2f86ca77f822fcd8e86f5a287f2a76d0becbb81a7bce73ae22909beb2f834c` |
| Internal header | `MORTAL KOMBAT II`, map `$31`, ROM size byte 12 (4 MB), region 1 (USA), version 1 |
| Checksum | `$7221` (3 MB image: sum(first 2 MB) + 2 × sum(last 1 MB)) |

## 1. Fighter identity

| | Kitana | Mileena | Jade |
|---|---|---|---|
| Character id (`$7E:4C10,x`, x = 0 P1 / 2 P2) | 4 | 5 | hidden opponent |
| Select grid cell (row, col) | 1, 2 | 2, 0 | — |
| Sprite set (shared) | **set 8** | **set 8** | **set 8** |
| Fight palette (15 colours + 0) | `EF:9173` | `EF:91B3` | `EF:9193` |
| Mirror-match P2 palette | `EF:9193` (= Jade's) | `EF:91D3` | — |

**Kitana, Mileena and Jade share one sprite set (pure palette swap).** Giving Haylie and Brooklyn
distinct artwork therefore needs *new* sprite sets, not in-place edits. The pairing
Haylie→Mileena / Brooklyn→Kitana was kept; nothing in the ROM made another pairing easier.

## 2. Sprite engine (only what the slots need)

* Set table: `84:CDCC` (bank word per set) + `84:CDEE` (address word), byte index = set id
  (even, 0–32; 17 sets). Only reader: `85:BF78`/`85:BF7E` inside `85:BF66`.
* Set id = high byte of `$7E:4C3C,x` & `$FE`; frame number = low 9 bits (1-based).
* Set header (16 bytes): `[0:2]` bank-table lo, `[2:4]`+`[4]` tile-group table, `[5:7]`+`[7]` frame
  table (frame + bank tables share bank `[7]`), `[8]` box bank, `[9:11]` per-frame effect table,
  `[11]`+`[12:14]` delta table (initial x/y, 15 x-deltas, 15 y-deltas), `[14:16]` hit-box table
  (4 bytes/frame). Set 8 header = `84:B4EE`.
* Frame table: 16-bit address per frame; bank = byte `bank_tbl[(n-1)>>6]`.
* Frame stream (`81:8000`): `count, nlarge`, then per piece: `b` (hi nibble = x-delta index or 0
  → absolute x byte follows; lo nibble = y-delta index or 0 → absolute y byte), then 4 tile words
  (16×16, TL/TR/BL/BR) for the first `nlarge` pieces, 1 tile word (8×8) for the rest.
  Coordinates are signed bytes relative to the object origin. OAM priority = piece order.
* Tile word: bits 0–1 = H/V flip (first word of a piece), bits 2–7 = tile group, bits 8–15 = tile
  index in group. Group table: 4 bytes per group `addr16, bank, flags`.
  * flags bit 7 clear → raw 4bpp tiles, `addr + idx*32`.
  * flags bit 7 set → zero-byte-suppressed tiles, record = `stride*idx` (`stride` = flags & `$3F`),
    4 mask bytes (one per 8-byte quarter, bit k → byte 7-k) followed by the non-zero bytes
    (handlers at `81:A451`).
* Per-fighter VRAM budget: P1 `$0000–$0DFF`, P2 `$2200–$2FFF` of the `7E:76BC` buffer (112 tiles).
* Ground line: in every set-8 frame that touches the floor, the lowest pixel row is origin **+39**.
  Generated frames are scaled around that row and snapped to it, so feet stay on the floor.
* Set 8: **263 frames**, ~7,600 unique tiles. Frames 212–263 are fatality-victim frames
  (inflate/explode, charred, skeleton, decapitated head, sliced body).
* Effects: set 22 = **blood** drops/splats, set 24 = projectiles (fans, sais, shock rings).

## 3. Graphics that are *not* in the sprite set

| Item | Location / mechanism |
|---|---|
| HUD nameplate | 2bpp bitmap (8 px tall, N tiles) from a compressed name blob (`ED:C86A` → `7F:0000`); per-id offset/length tables `83:D704`/`83:D726` + `83:D748`; copied at `83:CD34`, `83:CD94`, `83:D5F3`, `83:D671`. |
| Win banner ("X WINS") | ASCII string, 16-bit pointer table `83:D7B8` (bank `$83`), rendered at fight start by the proportional text renderer `85:B79F`; sites `83:D126`, `83:D1DE`, `83:D213`, `85:A4B5` (each followed by `LDX #$0083`). |
| Select-screen portraits | Mode 4 BG1, 8bpp, one image: compressed at `C1:0000` (35,712 bytes) → `7F:0000` by the script command `80:83E9`; palette `EF:40AE` (portraits use colours 16–207). Mileena window x58–89 y149–199, Kitana x130–161 y92–143. |
| Versus portraits | 71 tiles × 48 bytes (6 bit-planes, 64 colours), 7×10 tiles = 56×80 px. Tile stream table `82:DCD9` (4 bytes/id): Kitana `C7:4D32`, Mileena `C7:587D`. Palette table `82:DD09`. Loader `82:D4F7…`. |
| Decompressor | `85:B9FC`: header `size16, mode8`; back-to-front LZ; `0x40\|(n-1)` = n literal bytes, `0x00` = end. Mode 2 = interleaved. |
| Win/name ASCII list `EF:F199` | Not used by HUD or banner (left unchanged). |
| Battle Plan (1P ladder) face icons | Sprite **set 32**: 21×32 icons, frames 7–20 (Kitana = 12, Mileena = 14). Icon palette id = `0x80 + frame`, looked up in the palette pointer table `85:D33D` (3 bytes per id): Kitana `EF:060A`, Mileena `EF:064A`. Loader `83:F8CC`. |
| Endings | Not investigated (out of scope; see README). |

## 4. What the build changes

| Change | Where |
|---|---|
| ROM expanded 3 MB → 4 MB; all new data in banks `F0–FF` | header ROM-size byte already = 4 MB |
| Set table copied to `F0`, 2 new sets appended (Haylie, Brooklyn), blood set → blank set | `85:BF78`, `85:BF7E` |
| Set-routing hook (set 8 + fighter slot + char id 5/4 → new set) | `JSL` at `85:BF6B` |
| Fight palettes | `EF:91B3` (Haylie), `EF:9173` (Brooklyn), `EF:91D3` (Haylie mirror) |
| Nameplate hook ×4 | `83:CD34`, `83:CD94`, `83:D5F3`, `83:D671` |
| Win-banner strings relocated to `F0` | 4 `LDA $83D7B8,x` + `LDX #$0083` sites |
| Select portraits (masked byte patch after decompression) | `JSL` at `80:83E9` |
| VS portraits (new literal streams + palettes) | entries 4/5 of `82:DCD9`, `82:DD09` |
| Battle Plan icons: set 32 re-encoded with new frames 12/14; palette ids 0x8C/0x8E repointed | set table entry 32, `85:D33D + 3*0x8C`, `+ 3*0x8E` |

## 5. Animation-group checklist (set 8 → both new sets)

Idle, walk, crouch, jump, block, punch and kick ranges were observed in the emulator (trace of
`$4C3C` while P1 performed each action). The other ranges come from sprite-sheet review and are
approximate. Every frame 1–211 is regenerated regardless, so the grouping only affects reporting.

| Group | Frames | Haylie | Brooklyn |
|---|---|---|---|
| Idle / stance | 33–38 (1–14 alt stance) | replaced | replaced |
| Walk fwd / back | 49–56 | replaced | replaced |
| Crouch / crouch block | 90–91, 68–69 | replaced | replaced |
| Jump up / flip | 145–146, 135–142, 15–16 | replaced | replaced |
| Block | 117–118 | replaced | replaced |
| Punches / uppercut | 119–126 | replaced | replaced |
| Kicks / sweep / roundhouse | 154–155, 160–176 | replaced | replaced |
| Hit reactions / knockdown / get-up | 83–107, 160–211 | replaced | replaced |
| Specials (sai / fan / roll / teleport) | 17–32, 39–48, 57–60, 108–116, 147–159, 205–211 | replaced (weapons recoloured to gi palette) | replaced |
| Victory / misc | 61–82 | replaced | replaced |
| Fatality-victim (gore) | 212–263 | **blank** | **blank** |

**All 211 normal frames are regenerated for each character; no original Mileena/Kitana body,
face or mask pixels are used as-is.** Bodies are re-posed from the original silhouettes (see
README, "How the art is made"). Projectile objects (thrown fans/sais, set 24) are unchanged.
