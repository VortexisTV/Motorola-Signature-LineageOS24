# lineage_vantage 2026-11-11 (test image, r1)

> First DSU boot on 2026-11-11 by the owner: home screen reached, calls and Motorola Camera
> work (owner's report, no logs). The status bar clock sat almost in the left corner; fixed in
> `lineage_vantage-20261111-r2`, which also adds the refresh rate settings. The text below is
> as written before that boot.

LineageOS 24.0 (Android 17) system image for the **Motorola Signature** (codename `vantage`,
product `vantage_g`, XT2603-1) running stock firmware **A171WVH.21-16-16** (Android 17).
LineageOS `24.0-20261111-UNOFFICIAL-vantage`, build `CP2A.260605.016`, `userdebug`, AOSP/LineageOS
test keys, security patch level **2026-11-01**. Includes **microG** (GmsCore 0.3.17.252432,
Companion 0.3.17.40226). Only `system` is replaced; vendor, odm, boot, modem and everything
else stay stock.

It succeeds the Android 16 image `vantage_td-20261011-r4`, which no longer matches the phone
since stock was updated to Android 17.

**Nothing in this image has run on a phone.** Every statement below is a static check of the
files (label **static**) unless it says otherwise.

Built on 2026-11-11 (build 7 in `BUILDING.md` section 9) from the folder `J:\lineageos-signature`
as it is now; the folder is not under version control yet.

## Files

| File | Size | SHA-256 |
|---|---|---|
| `system_raw.gz` | 1,476,095,730 bytes | `f6b9f61d750f969a0051102b35afdd3c878bfa5e1fb4a6a0b6c6f448d756cd9c` |
| `system.img` (what the archive unpacks to) | 3,005,046,784 bytes | `08286f830556d23364b9c6c9ebb386a8a9d93361be032d86b4f3e20dd8a1a0f8` |

Both are in `out/lineage_vantage-20261111/`, with `SHA256SUMS` and `SIZES`. `system_raw.gz` is
the gzip of the raw (non-sparse) ext4 image, the form the Dynamic System Update installer takes.

```bash
sha256sum -c SHA256SUMS
```

## What was checked

`validate-image.sh` on this exact image: exit status 0: 94 PASS, **0 FAIL**, 9 WARNING (reviewed; COMPATIBILITY.md), 13 UNKNOWN (hardware behaviour only a phone can show), 1 INFO (reports in `reports/vantage/`).
`COMPATIBILITY.md` lists each feature with its evidence. In short (static):

- the combined SELinux policy (this image + stock A17 vendor/odm) compiles as the A17 `init`
  compiles it, including the 202504 mapping and `plat_sepolicy_genfs_202504.cil`; the vendor's
  rules on the IMS and camera app domains bind to our domains, and what those two domains may
  do matches stock A17 except two service lookups the camera does not use (as on A16);
- VINTF: the tree's `checkvintf` finds this image compatible with the stock vendor/odm, apart
  from a list of vendor HALs that only Motorola's own system-side matrix declares (not checked
  at boot);
- the 34 pinned stock entries are in the image: 31 files byte-identical to the A17 firmware,
  the IMS app re-signed with this image's platform key (payload unchanged, as on A16), and 2
  recreated library links;
- privileged-permission allowlists cover every privileged permission requested (enforced
  at boot);
- microG: both APKs are microG's release files, signed with the key LineageOS's framework
  recognises, and the spoofing switch is compiled into this image;
- the three source patches are applied and visible in the binaries.

Not checkable without the phone: boot, registration, VoLTE calls, SMS, call audio, camera,
microG services. The Android 16 image r4 did all of those on the A16 stock vendor; that is
history, not evidence for this image.

## Differences from the Android 16 image r4

| | r4 (Android 16) | this image |
|---|---|---|
| Base | AOSP 16 + TrebleDroid | LineageOS 24.0 (Android 17) |
| Stock firmware | W2WVS36.55-95-5-1 (A16) | A171WVH.21-16-16 (A17) |
| Security patch level | 2025-06-05 | 2026-11-01 |
| microG | no | yes |
| adb on the guest | on at first boot (`persist.sys.usb.config=adb`), no authorisation prompt (`ro.adb.secure=0`), `adb root` available | not switched on by the image (the build adds `persist.sys.usb.config=adb` only when `ro.debuggable=1`): expect to enable USB debugging in Developer options; authorisation prompt (`ro.adb.secure=1`); **no** `adb root` (LineageOS sets `ro.debuggable=0` on `userdebug`) |
| Video calling | not offered | not offered (the A17 IMS app's video back end, `imsvtdaemon`, is not ported) |
| Wi-Fi calling | not offered | not offered |
| Camera app | Motorola Camera 10.0.56.61 | 10.0.56.80 (from the A17 firmware) |

## Before you install

- **This is a test build.** `userdebug`, signed with public test keys. Do not use it as a daily
  system.
- It is for this model and stock build A171WVH.21-16-16 only.
- The bootloader must be unlocked (verified boot state `orange`): a DSU guest signed with test
  keys is accepted only then. The image's patch level is not older than stock's, so the stock
  first-stage `init` takes no rollback branch.
- About 40 GiB of free user data is needed (guest data 8 GiB, the image, and the reserve
  the installer keeps the size of `super`), plus the archive while it is on the phone.
- A DSU guest lives in free space of user data with its own data; stock is not modified and a
  reboot returns to it. Discard an earlier guest first (notification on stock).

## Install (Dynamic System Update)

`vendor/motorola/vantage/scripts/dsu-preflight.sh` checks the archive and the phone
(read-only) and prints these commands with the values of this image:

```bash
ADB=/h/androidtools/platform-tools/adb.exe bash vendor/motorola/vantage/scripts/dsu-preflight.sh
```

In Git Bash every adb command with a device path needs `MSYS_NO_PATHCONV=1`.

```bash
MSYS_NO_PATHCONV=1 adb push out/lineage_vantage-20261111/system_raw.gz /storage/emulated/0/Download/
```

```bash
MSYS_NO_PATHCONV=1 adb shell am start-activity -n com.android.dynsystem/com.android.dynsystem.VerificationActivity -a android.os.image.action.START_INSTALL -d file:///storage/emulated/0/Download/system_raw.gz --el KEY_SYSTEM_SIZE 3005046784 --el KEY_USERDATA_SIZE 8589934592 --ez KEY_ONE_SHOT true
```

Confirm on the phone, wait for the notification to finish, tap **Restart**. To go back: reboot.
On stock the notification offers **Discard**, which removes the guest.

On the guest, to let `device-session.sh` (or any adb command) in: finish the setup screens,
Settings > About phone > tap **Build number** seven times, Developer options > **USB debugging**
on, accept the computer's key.

microG: open the microG Settings app and run its self-check; device registration and Cloud
Messaging are off until switched on there. Runtime permissions are not pre-granted.

## What is inside

Everything is built from source except 32 files from the stock A17 firmware, plus 2 library
links to them (the Qualcomm IMS
service and its libraries, Motorola Camera and its signature library, the APN database, the audio
vendor-extension library; list with hashes: `vendor/motorola/vantage/proprietary-files.txt`) and
the two microG release APKs (`vendor/motorola/vantage/scripts/fetch-microg.sh`, pinned
SHA-256). The stock files belong to Motorola and Qualcomm; microG is Apache-2.0.

Three source patches (`patches/`): TrebleDroid's RIL audio bridge (QcRilAm, added by a local
manifest), one table entry in `init` (`ro.carrier`), and an opt-out switch in LineageOS's APN
module so the stock APN database is installed instead of LineageOS's. Each patch starts with its
reason. `BUILDING.md` describes how to build the image.
