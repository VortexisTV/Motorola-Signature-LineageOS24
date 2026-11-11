#!/usr/bin/env bash
# Initialise and sync the LineageOS 24.0 source tree used for the vantage system image.
#
#   wsl.exe -d lineage-aosp -u builder -e bash /proj/vendor/motorola/vantage/scripts/sync-source.sh
#   wsl.exe -d lineage-aosp -u builder -e env PINNED=1 bash /proj/vendor/motorola/vantage/scripts/sync-source.sh
#
# Baseline (checked 2026-11-11, FEASIBILITY.md):
#   LineageOS  lineage-24.0, based on AOSP android-17.0.0_r1 (SDK 37, matches stock
#              ro.build.version.sdk_full=37.0); product lineage_gsi_arm64 (generic system image)
#   QcRilAm    TrebleDroid's RIL audio bridge (AndyCGYan/android_packages_apps_QcRilAm), the
#              same commit the Android 16 port pinned; patched by patches/packages/apps/QcRilAm.
#              TrebleDroid itself has no Android 17 branch and is not used.
#
# PINNED=0 (default): lineage-24.0 as it is today plus the local manifest below; afterwards
#                     manifests/pinned-lineage-24.0.xml is rewritten with every project's commit.
# PINNED=1:           exactly the commits of manifests/pinned-lineage-24.0.xml.
set -euo pipefail

SRC_DIR="${SRC_DIR:-/work/lineage}"
BRANCH="${BRANCH:-lineage-24.0}"
MANIFEST_URL="${MANIFEST_URL:-https://github.com/LineageOS/android.git}"
QCRILAM_REV="${QCRILAM_REV:-dc599b67cc1e7e9a62ca15eef605e3b2546d0d42}"
JOBS="${JOBS:-8}"
PIN_OUT="${PIN_OUT:-/proj/manifests}"
PIN_FILE="$PIN_OUT/pinned-$BRANCH.xml"
PINNED="${PINNED:-0}"

mkdir -p "$SRC_DIR"
cd "$SRC_DIR"

if [ ! -d .repo/manifests ]; then
  # --depth=1: no history (saves ~100 GB); --git-lfs: some LineageOS projects keep files in LFS.
  repo init -u "$MANIFEST_URL" -b "$BRANCH" --depth=1 --git-lfs --no-clone-bundle </dev/null
fi

if [ "$PINNED" = 1 ]; then
  [ -f "$PIN_FILE" ] || { echo "no pinned manifest at $PIN_FILE" >&2; exit 1; }
  rm -rf .repo/local_manifests
  cp "$PIN_FILE" .repo/manifests/vantage-pinned.xml
  repo init -m vantage-pinned.xml </dev/null
  echo "using the pinned manifest $PIN_FILE"
else
  repo init -m default.xml </dev/null
  mkdir -p .repo/local_manifests
  cat > .repo/local_manifests/vantage.xml <<XML
<?xml version="1.0" encoding="UTF-8"?>
<!-- Added by vendor/motorola/vantage/scripts/sync-source.sh -->
<manifest>
  <remote name="vantage-github" fetch="https://github.com/" />
  <!-- TrebleDroid's RIL audio bridge (call audio on the Qualcomm RIL), Android 16 port's commit -->
  <project path="packages/apps/QcRilAm" name="AndyCGYan/android_packages_apps_QcRilAm"
           remote="vantage-github" revision="$QCRILAM_REV" />
</manifest>
XML
fi
if [ "${INIT_ONLY:-0}" = 1 ]; then
  echo "initialised only (INIT_ONLY=1): $(repo manifest | grep -c '<project ') projects in the manifest"
  exit 0
fi

ok=0
for attempt in 1 2 3 4; do
  echo "=== repo sync attempt $attempt ($(date -Is)) ==="
  if repo sync -c -j"$JOBS" --force-sync --no-tags --no-clone-bundle --optimized-fetch --prune; then
    ok=1
    break
  fi
  JOBS=4
  sleep 30
done
[ "$ok" = 1 ] || { echo "repo sync failed after retries"; exit 1; }

if [ "$PINNED" != 1 ]; then
  mkdir -p "$PIN_OUT"
  repo manifest -r -o "$PIN_FILE"
  echo "pinned manifest written to $PIN_FILE"
fi
echo "=== sync complete ($(date -Is)) ==="
du -sh "$SRC_DIR" 2>/dev/null || true
