#!/usr/bin/env bash
# Last check before the first DSU installation. Read-only: it hashes the local files, reads
# properties and free space from the phone, and PRINTS the install commands for the exact build
# pinned below. It pushes nothing, installs nothing and reboots nothing.
#
#   ADB=/h/androidtools/platform-tools/adb.exe bash dsu-preflight.sh [release-dir]
#
# Exit status 0 = ready to install, 2 = checks passed but the archive is not on the phone, 1 = a check failed. The pinned values are those of the validated image
# (BUILDING.md build log, releases/<name>.md); change them only together with a new validated build.
set -uo pipefail
export MSYS_NO_PATHCONV=1

# For an image you built yourself, pass the two values export-image.sh prints:
#   IMAGE_SHA256=... IMAGE_SIZE=... bash dsu-preflight.sh <release-dir>
IMAGE_SHA256="${IMAGE_SHA256:-94c1595d00d2302aaa572e543ec288203b3fb50d006f48b3b4780e70c97062bb}"
IMAGE_SIZE="${IMAGE_SIZE:-3005071360}"   # KEY_SYSTEM_SIZE: the uncompressed image, in bytes
USERDATA_SIZE=8589934592       # KEY_USERDATA_SIZE: 8 GiB for the guest
SUPER_SIZE=31138512896         # gsid keeps this much free on a Virtual A/B device
# Stock Android 17 A171WVH.21-16-16, the firmware this image was built and checked against.
STOCK_BUILD=A171WVH.21-16-16
STOCK_SYSTEM_FP="motorola/vantage_g/msi:17/A171WVM-16-ST1.1/b328b:user/release-keys"
STOCK_VENDOR_FP="motorola/vantage_g/vantage:16/WWV36HV-16-ST1.1/4548c:user/release-keys"
STOCK_VBMETA_DIGEST=4862c7d79391dc1c06d1398a6f7c2a27c6ca5be14cb22f91c45f9c752bd787d6   # avbtool calculate_vbmeta_digest on the package
DEVICE_FILE=/storage/emulated/0/Download/system_raw.gz

ADB="${ADB:-adb}"
ROOT="$(cd "$(dirname "$0")/../../../.." && pwd)"
REL="${1:-$ROOT/out/lineage_vantage-20261111-r3}"
GZ="$REL/system_raw.gz"
fail=0
say() { printf '  [%-7s] %s\n' "$1" "$2"; if [ "$1" = FAIL ]; then fail=1; fi; }

echo "Local files ($REL):"
if [ ! -f "$GZ" ]; then
  say FAIL "system_raw.gz not found"
else
  gz_size=$(stat -c %s "$GZ")
  gz_sha=$(sha256sum "$GZ" | cut -d' ' -f1)
  raw_sha=$(gzip -dc "$GZ" | sha256sum | cut -d' ' -f1)
  raw_size=$(gzip -dc "$GZ" | wc -c | tr -d ' ')
  if [ "$raw_sha" = "$IMAGE_SHA256" ] && [ "$raw_size" = "$IMAGE_SIZE" ]; then
    say PASS "system_raw.gz unpacks to the validated image: $raw_size bytes, sha256 $raw_sha"
  else
    say FAIL "system_raw.gz unpacks to $raw_size bytes, sha256 $raw_sha: NOT the validated image $IMAGE_SHA256"
  fi
  if [ -f "$REL/system.img" ]; then
    img_sha=$(sha256sum "$REL/system.img" | cut -d' ' -f1)
    if [ "$img_sha" = "$IMAGE_SHA256" ]; then say PASS "system.img has the same sha256"; else say FAIL "system.img is $img_sha"; fi
  fi
fi

echo "Phone (read-only):"
if [ "$("$ADB" get-state 2>/dev/null | tr -d '\r')" != "device" ]; then
  say FAIL "no phone in adb state 'device'"
else
  gp() { "$ADB" shell getprop "$1" | tr -d '\r'; }
  sysfp=$(gp ro.system.build.fingerprint); vendfp=$(gp ro.vendor.build.fingerprint); product=$(gp ro.product.name)
  if [ "$sysfp" = "$STOCK_SYSTEM_FP" ] && [ "$vendfp" = "$STOCK_VENDOR_FP" ] && [ "$product" = "vantage_g" ]; then
    say PASS "running stock $STOCK_BUILD ($(gp ro.build.display.id)): system and vendor fingerprints match the analysed firmware"
  else
    say FAIL "running system '$sysfp' / vendor '$vendfp', expected stock $STOCK_BUILD (the checks were made against that firmware)"
  fi
  # The image is signed with the AOSP test key, which a DSU install accepts only on an unlocked
  # phone (check_stock_init.py; validate-image.sh reports whether the image's security patch
  # level is older than stock, which would also need this state).
  vbs=$(gp ro.boot.verifiedbootstate)
  if [ "$vbs" = "orange" ]; then say PASS "verified boot state is orange (bootloader unlocked)"; else say FAIL "verified boot state is '$vbs', not orange: the test-keyed image would be rejected"; fi
  digest=$(gp ro.boot.vbmeta.digest)
  if [ "$digest" = "$STOCK_VBMETA_DIGEST" ]; then
    say PASS "vbmeta digest equals the stock package's: /vendor and /odm are the verified stock images"
  else
    say WARNING "vbmeta digest $digest differs from the stock package's; the phone's partitions are not exactly those analysed"
  fi
  gsi=$("$ADB" shell gsi_tool status 2>&1 | tr -d '\r' | head -n 1)
  case "$gsi" in
    normal)    say PASS "gsi_tool status: normal (no DSU image installed or running)" ;;
    running)   say FAIL "a DSU guest is running right now; restart to stock first" ;;
    installed) say FAIL "a DSU image is already installed; discard it from the notification first" ;;
    *)         say WARNING "gsi_tool status says '$gsi'; cannot tell whether a DSU image is installed" ;;
  esac
  level=$("$ADB" shell dumpsys battery | tr -d '\r' | awk '/^ *level:/ {print $2}')
  if [ "${level:-0}" -ge 50 ]; then say PASS "battery $level %"; else say FAIL "battery ${level:-?} %, charge to 50 % first"; fi
  pushed=0
  dev_size=$("$ADB" shell "stat -c %s $DEVICE_FILE 2>/dev/null" | tr -d '\r')
  if [ -n "$dev_size" ] && [ -n "${gz_sha:-}" ]; then
    dev_sha=$("$ADB" shell sha256sum "$DEVICE_FILE" | tr -d '\r' | cut -d' ' -f1)
    if [ "$dev_sha" = "$gz_sha" ]; then pushed=1; say PASS "the archive is already on the phone and intact ($dev_size bytes)"
    else say INFO "an archive of another build is on the phone; the push below replaces it"; fi
  else
    say INFO "the archive is NOT on the phone: the installer would fail at once with 'Install failed'"
  fi
  last=$("$ADB" logcat -b events -d -s dsu_install_failed 2>/dev/null | tr -d '\r' | grep dsu_install_failed | tail -n 1)
  if [ -n "$last" ]; then say INFO "last installer error in the phone's log: ${last#*dsu_install_failed: }"; fi
  avail_kb=$("$ADB" shell df -k /data | tr -d '\r' | awk 'END {print $4}')
  need=$(( USERDATA_SIZE + IMAGE_SIZE + SUPER_SIZE ))
  if [ "$pushed" = 0 ]; then need=$(( need + ${gz_size:-0} )); fi
  if [ "$(( ${avail_kb:-0} * 1024 ))" -ge "$need" ]; then
    say PASS "free space $(( avail_kb / 1048576 )) GiB, needed $(( need / 1073741824 + 1 )) GiB (guest data + system + gsid's reserve)"
  else
    say FAIL "free space $(( ${avail_kb:-0} / 1048576 )) GiB, needed $(( need / 1073741824 + 1 )) GiB"
  fi
fi

echo
if [ "$fail" != 0 ]; then
  echo "Do NOT install: at least one check failed."
  exit 1
fi
# With path conversion off, adb.exe needs the local file as a Windows path (H:/...), not /h/...
GZ_NATIVE="$(cygpath -m "$GZ" 2>/dev/null || echo "$GZ")"
if [ "${pushed:-0}" != 1 ]; then
  cat <<TEXT
Checks passed, but the archive is not on the phone. Push it first ($(( ${gz_size:-0} / 1048576 )) MiB; wait for "1 file pushed"):

  MSYS_NO_PATHCONV=1 "$ADB" push "$GZ_NATIVE" /storage/emulated/0/Download/

(MSYS_NO_PATHCONV=1 matters in Git Bash: without it the shell rewrites /storage/... into
C:/Program Files/Git/storage/... and adb answers "remote secure_mkdirs() failed".)

Then run this script again: it compares the copy on the phone with the validated archive and
prints the install command. This script ran nothing.
TEXT
  exit 2
fi
cat <<TEXT
All checks passed and the archive on the phone is intact. The commands for this exact build
(run them yourself; this script ran none):

  1. MSYS_NO_PATHCONV=1 "$ADB" shell am start-activity -n com.android.dynsystem/com.android.dynsystem.VerificationActivity -a android.os.image.action.START_INSTALL -d file://$DEVICE_FILE --el KEY_SYSTEM_SIZE $IMAGE_SIZE --el KEY_USERDATA_SIZE $USERDATA_SIZE --ez KEY_ONE_SHOT true
  2. confirm with the PIN or fingerprint; the notification shows the progress for a few minutes; then tap Restart
  3. ADB="$ADB" bash "$ROOT/vendor/motorola/vantage/scripts/device-session.sh"
  4. on the guest: finish the setup screens, Settings > About phone > tap "Build number" 7 times,
     Developer options > USB debugging on, accept the computer's key. LineageOS's userdebug build
     starts with adb off and has no adb root (unlike the Android 16 images); the script in
     step 3 waits up to 15 minutes for the guest and saves what the log buffers still hold.

KEY_ONE_SHOT true: the restart after step 2 boots the guest once; the restart after that is stock.
If the notification says "Install failed", run this script again: it shows the installer's error.
TEXT
