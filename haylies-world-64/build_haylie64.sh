#!/usr/bin/env bash
# Haylie's World 64 - one-shot build (Linux / GitHub Codespaces).
# Usage: ./build_haylie64.sh "/path/to/Super Mario 64 (USA).z64 or .zip"
# Produces ./out/Haylies_World_64.z64. The input ROM is only read, never modified.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
ROM_IN="${1:?pass the path to your clean US ROM (.z64 or .zip)}"
EXPECTED_SHA1="9bef1128717f958171a4afac3ed78ee2bb4e86ce"
HACKERSM64_REPO="https://github.com/HackerN64/HackerSM64.git"
HACKERSM64_REV="8953c07"           # HackerSM64 2.4.0 release (tested)
WORK="${WORK:-$HERE/work}"
OUT="$HERE/out"
say(){ printf '\n== %s ==\n' "$1"; }

say "Dependencies"
if command -v apt-get >/dev/null; then
  SUDO=""; [ "$(id -u)" -ne 0 ] && SUDO=sudo
  $SUDO apt-get update -y
  $SUDO apt-get install -y build-essential git libcapstone-dev pkgconf python3 python3-pil \
       gcc-mips-linux-gnu binutils-mips-linux-gnu unzip
fi

say "HackerSM64 @ $HACKERSM64_REV"
if [ ! -d "$WORK/HackerSM64/.git" ]; then
  mkdir -p "$WORK"
  git clone "$HACKERSM64_REPO" "$WORK/HackerSM64"
fi
cd "$WORK/HackerSM64"
git checkout -q "$HACKERSM64_REV"

say "Verify clean ROM"
case "$ROM_IN" in
  *.zip) unzip -p "$ROM_IN" '*.z64' > baserom.us.z64 ;;
  *)     cp "$ROM_IN" baserom.us.z64 ;;
esac
ACTUAL="$(sha1sum baserom.us.z64 | awk '{print $1}')"
[ "$ACTUAL" = "$EXPECTED_SHA1" ] || { echo "ERROR: ROM SHA1 $ACTUAL != $EXPECTED_SHA1"; exit 1; }
echo "OK: $ACTUAL"

say "Extract assets from your ROM"
python3 extract_assets.py us

say "Apply Haylie patch"
python3 "$HERE/tools/apply_haylie.py"

say "Build"
make -j"$(nproc)"

mkdir -p "$OUT"
cp build/us_n64/sm64.z64 "$OUT/Haylies_World_64.z64"
sha1sum "$OUT/Haylies_World_64.z64" | tee "$OUT/Haylies_World_64.sha1.txt"
say "DONE -> $OUT/Haylies_World_64.z64"
