# Next-agent prompt after v0.1 boots

You are working in HackerN64/HackerSM64 on Haylie's World 64.

First read `START_HERE_iPHONE.md`, `apply_haylie_v01.py`, and inspect the current diff. The user is iPhone-only. Preserve a clean US baserom and never commit ROM bytes.

The v0.1 milestone is only a bootable identity proof using Mario's skeleton and animations. After the user confirms the ROM boots and the model is visible, implement Phase 2 in small reversible batches:

1. Refine Haylie's head geometry so it reads as the approved character, while retaining compatible head animation switches.
2. Improve the pink glasses geometry and brown ponytail, checking clipping during idle, run, jump, swim, climb, crouch, cap-off, and Wing Cap states.
3. Replace the cap logo with a clean white heart and preserve Metal/Vanish behavior.
4. Replace title/HUD/name references only after the character model is stable. Target visible player identity first, then title screen and HUD.
5. Build after each batch. Never change multiple subsystems without a successful intermediate ROM.

Acceptance gate for each batch:
- build succeeds
- ROM boots
- player is visible
- idle/run/jump work
- no black screen or crash
- changes are committed separately from prior working state

Do not claim a 3D model is final without an in-emulator screenshot or video from the user.
