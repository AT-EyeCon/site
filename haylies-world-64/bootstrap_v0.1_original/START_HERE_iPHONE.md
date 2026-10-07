# Haylie's World 64, iPhone-only bootstrap

## Goal
Get a first **bootable Haylie character proof** quickly while preserving the clean ROM and Mario's working animation skeleton.

## What v0.1 changes
- pink cap, shirt/arms, and shoes
- white heart cap logo
- removes Mario's moustache texture
- adds low-poly pink glasses
- adds a low-poly brown ponytail
- keeps blue overalls
- keeps original Mario movement and animation data for stability

## What v0.1 deliberately does NOT claim to finish
- final Haylie face/body proportions
- title screen text
- HUD/name text
- voice clips
- Metal/Vanish/Wing visual refinements
- replacement of every Mario textual reference

Those come after the first ROM boots. This avoids repeating the earlier SMW mistake of changing everything before validating the base character pipeline.

## iPhone workflow
1. Open the official HackerN64/HackerSM64 repository in Safari on iPhone and create/open a GitHub Codespace for it. Upload these two files into the Codespace root:
   - `bootstrap_haylie64.sh`
   - `apply_haylie_v01.py`
   Also upload your own `Super Mario 64 (USA).zip`.
2. In the Codespace terminal run exactly:

```bash
chmod +x bootstrap_haylie64.sh && ./bootstrap_haylie64.sh
```

When it finishes, download `Haylies_World_64_v0.1.z64` from the Codespace file list and test it in RetroArch on iPhone.

## Clean ROM verification
Expected SHA-1:
`9bef1128717f958171a4afac3ed78ee2bb4e86ce`

The bootstrap refuses to build if the ROM hash does not match.

## Safety
`baserom.us.z64` and the uploaded ROM ZIP are added to `.gitignore`. Do not commit or publish them.
