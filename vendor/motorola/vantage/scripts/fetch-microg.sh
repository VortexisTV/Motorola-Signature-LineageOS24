#!/usr/bin/env bash
# Download the official microG release APKs into vendor/motorola/vantage/microg/prebuilt/.
#
#   bash /proj/vendor/motorola/vantage/scripts/fetch-microg.sh [vendor_dir]
#
# The APKs are not committed (they are release binaries of another project). Each download is
# checked against the SHA-256 pinned below, which is the digest GitHub publishes for the
# release asset. They must stay signed by microG: LineageOS lets an app claim Google's
# signature only when it is signed by microG's own key (microg/README.md), so a rebuilt or
# re-signed APK would install but not work. validate-microg.py checks that certificate
# against the one in the tree's frameworks/base.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VDIR="${1:-$(dirname "$HERE")}"
DEST="$VDIR/microg/prebuilt"
REL="https://github.com/microg/GmsCore/releases/download/v0.3.17.252432"

# name | url | sha256
FILES="
GmsCore.apk|$REL/com.google.android.gms-252432034.apk|e5e6cba078bdec812b5450599350e5c1a12c8b7438da5bf77123af170f8c1a35
Companion.apk|$REL/com.android.vending-84022634.apk|9b8616011cc8f026bcbbe094df850794abb9d6d9f23214d7a8f8c4d1033ea012
"

mkdir -p "$DEST"
for entry in $FILES; do
  name="${entry%%|*}"; rest="${entry#*|}"; url="${rest%%|*}"; sha="${rest##*|}"
  if [ -f "$DEST/$name" ] && [ "$(sha256sum "$DEST/$name" | cut -d' ' -f1)" = "$sha" ]; then
    echo "ok (cached): $name"
    continue
  fi
  curl -fsSL --retry 3 -o "$DEST/$name.part" "$url"
  got="$(sha256sum "$DEST/$name.part" | cut -d' ' -f1)"
  if [ "$got" != "$sha" ]; then
    rm -f "$DEST/$name.part"
    echo "SHA-256 MISMATCH for $name from $url (expected $sha, got $got)" >&2
    exit 1
  fi
  mv "$DEST/$name.part" "$DEST/$name"
  echo "ok: $name $sha"
done
