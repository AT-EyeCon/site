#!/usr/bin/env python3
"""PREVIEW-ONLY harness (never used for the release ROM).

Boots straight into Castle Grounds and either spins Haylie on a turntable while
cycling cap states (mode 1) or drives scripted controller input (mode 2), so the
model can be checked headlessly with `mupen64plus --testshots`.
Usage (from a *copy* of the patched HackerSM64 tree): apply_preview.py <mode>
"""
import sys
from pathlib import Path
mode = int(sys.argv[1])
cfg = Path('include/config/config_debug.h')
t = cfg.read_text()
t = t.replace('// #define TEST_LEVEL LEVEL_BOB', '#define TEST_LEVEL LEVEL_CASTLE_GROUNDS')
cfg.write_text(t)

m = Path('src/game/mario.c')
t = m.read_text()
hook = r'''
#define HAYLIE_PREVIEW %d
static u32 sHayliePreviewT = 0;
static void haylie_preview_input(struct MarioState *m) {
#if HAYLIE_PREVIEW == 2
    u32 t = sHayliePreviewT;
    struct Controller *c = m->controller;
    c->stickX = 0; c->stickY = 0; c->stickMag = 0; c->buttonPressed = 0; c->buttonDown = 0;
    if (t >= 40 && t < 64) { c->stickX = -64; c->stickMag = 64; }            // turn around (away from castle)
    if (t >= 64 && t < 230) { c->stickY = -64; c->stickMag = 64; }           // run toward camera
    if (t == 110 || t == 160 || t == 176 || t == 192) { c->buttonPressed = A_BUTTON; }
    if ((t >= 110 && t < 118) || (t >= 160 && t < 200)) { c->buttonDown |= A_BUTTON; }
    if (t >= 260 && t < 300) { c->buttonDown |= Z_TRIG; if (t == 260) c->buttonPressed |= Z_TRIG; }
    if (t == 320 || t == 332 || t == 344) { c->buttonPressed |= B_BUTTON; c->buttonDown |= B_BUTTON; }
#endif
}
static void haylie_preview_update(struct MarioState *m) {
#if HAYLIE_PREVIEW == 1
    u32 t = sHayliePreviewT;
    u32 seg = (t / 256) %% 6;
    m->flags &= ~(MARIO_WING_CAP | MARIO_METAL_CAP | MARIO_VANISH_CAP | MARIO_CAP_ON_HEAD | MARIO_CAP_IN_HAND);
    m->flags |= MARIO_NORMAL_CAP;
    switch (seg) {
        case 0: m->flags |= MARIO_CAP_ON_HEAD; break;
        case 1: m->flags |= MARIO_CAP_IN_HAND; break;
        case 2: m->flags |= MARIO_CAP_ON_HEAD | MARIO_WING_CAP; break;
        case 3: m->flags |= MARIO_CAP_ON_HEAD | MARIO_METAL_CAP; break;
        case 4: m->flags |= MARIO_CAP_ON_HEAD | MARIO_VANISH_CAP; break;
        default: m->flags |= MARIO_CAP_ON_HEAD; break;
    }
    m->capTimer = 200;
    m->marioObj->header.gfx.angle[1] += (s16)(t * 0x100);
#endif
    sHayliePreviewT++;
}
''' % mode
anchor = 's32 execute_mario_action(UNUSED struct Object *obj) {'
assert anchor in t
t = t.replace(anchor, hook + anchor)
t = t.replace('        play_infinite_stairs_music();\n', '        haylie_preview_update(gMarioState);\n        play_infinite_stairs_music();\n', 1)
# inject input just before the action loop reads it
a2 = '        mario_reset_bodystate(gMarioState);\n'
assert a2 in t, 'input anchor'
t = t.replace(a2, '        haylie_preview_input(gMarioState);\n' + a2, 1)
m.write_text(t)
print('preview harness mode', mode)
