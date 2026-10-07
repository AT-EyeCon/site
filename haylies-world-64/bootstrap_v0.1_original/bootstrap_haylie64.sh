#!/usr/bin/env bash
set -euo pipefail

EXPECTED_SHA1="9bef1128717f958171a4afac3ed78ee2bb4e86ce"
PROJECT="Haylies-World-64"

say(){ printf '\n== %s ==\n' "$1"; }

say "Checking environment"
if [ ! -f Makefile ] || [ ! -f extract_assets.py ]; then
  echo "ERROR: Open a HackerSM64 Codespace/repository first, then place this bootstrap package in its root."
  exit 1
fi

# Locate user's ROM or ZIP without committing it.
ROM=""
if [ -f baserom.us.z64 ]; then
  ROM="baserom.us.z64"
elif compgen -G "*.z64" >/dev/null; then
  ROM="$(find . -maxdepth 1 -type f -name '*.z64' | head -n1)"
elif compgen -G "*.zip" >/dev/null; then
  say "Finding and extracting uploaded ROM ZIP"
  python3 - <<'PY'
import zipfile, glob
found=False
for z in glob.glob('*.zip'):
    try:
        with zipfile.ZipFile(z) as f:
            c=[n for n in f.namelist() if n.lower().endswith('.z64')]
            if c:
                open('baserom.us.z64','wb').write(f.read(c[0]))
                print('Using ROM from:', z, '->', c[0])
                found=True
                break
    except zipfile.BadZipFile:
        pass
if not found:
    raise SystemExit('No .z64 found inside any ZIP in this folder')
PY
  ROM="baserom.us.z64"
else
  echo "ERROR: Upload your clean Super Mario 64 (USA).zip or .z64 into this Codespace root."
  exit 1
fi

if [ "$ROM" != "baserom.us.z64" ]; then cp "$ROM" baserom.us.z64; fi
ACTUAL_SHA1="$(sha1sum baserom.us.z64 | awk '{print $1}')"
if [ "$ACTUAL_SHA1" != "$EXPECTED_SHA1" ]; then
  echo "ERROR: Wrong ROM. SHA1=$ACTUAL_SHA1"
  echo "Expected clean US ROM SHA1=$EXPECTED_SHA1"
  exit 1
fi
say "Clean US ROM verified"

# Ensure the ROM can never be accidentally committed.
grep -qxF 'baserom.us.z64' .gitignore 2>/dev/null || echo 'baserom.us.z64' >> .gitignore
grep -qxF 'Super Mario 64 (USA).zip' .gitignore 2>/dev/null || echo 'Super Mario 64 (USA).zip' >> .gitignore

say "Installing Linux build dependencies"
sudo apt-get update -y
sudo apt-get install -y build-essential git libcapstone-dev pkgconf python3 gcc-mips-linux-gnu binutils-mips-linux-gnu

say "Extracting original assets from your ROM"
python3 extract_assets.py

say "Applying Haylie v0.1 character patch"
python3 apply_haylie_v01.py

say "Building ROM"
make NOEXTRACT=1 -j"$(nproc)"

OUT="build/us_n64/sm64.z64"
if [ ! -f "$OUT" ]; then
  echo "ERROR: Build completed without expected output $OUT"
  exit 1
fi
cp "$OUT" Haylies_World_64_v0.1.z64
sha1sum Haylies_World_64_v0.1.z64 > Haylies_World_64_v0.1.sha1.txt

say "DONE"
echo "Output: Haylies_World_64_v0.1.z64"
echo "This v0.1 is the fast character-proof build: pink cap/shirt/shoes, heart cap logo, no moustache, pink 3D glasses, brown ponytail, original Mario skeleton/animations."
echo "Title/HUD/name replacement and refined custom body/head geometry are intentionally Phase 2 after this boots."
