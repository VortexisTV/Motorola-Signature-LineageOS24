# lineage_vantage 2026-11-12 r4 (test image)

LineageOS 24.0 (Android 17) system image for the **Motorola Signature** (`vantage`) on stock
firmware **A171WVH.21-16-16**, with microG. Same base, keys, patch level (2026-11-01) and
contents as r3 ([lineage_vantage-20261111-r3.md](lineage_vantage-20261111-r3.md)), plus the
change below. Built on 2026-11-12 (build 11 in `BUILDING.md` section 9).

## New in r4: charging limit

**Settings > Battery > Charging control** is now available. It is LineageOS's own page; on r1-r3
it was hidden because it needs a LineageOS hardware service that the stock vendor does not have.
r4 connects it to the charging limit Motorola's stock vendor already provides (the one stock's
battery protection uses).

- Turn on **Charging control**, choose the mode **Limit**, and set **Charging limit** (70-100 %,
  default 80 %). Charging stops at the limit and starts again 10 points below it (at 70 % for an
  80 % limit), so the battery stays between the two while the phone is plugged in.
- 100 % turns the limit off. Turning **Charging control** off also removes the limit.
- **Auto** (next alarm) and **Custom** (your times) use the same mechanism: during the window the
  battery is held at 80 %, and the limit is lifted early enough to reach 100 % by the target time
  (Android's charge-time estimate plus 30 minutes, one hour if there is no estimate). LineageOS
  needed a fix for this on a limit-only phone (same patch), which would otherwise have stopped
  the system as soon as such a schedule was active while charging.
- The limit is applied again after every boot, once the setting is on.

How: a fourth source patch, `patches/lineage-sdk`, lets LineageOS's charging control use
Motorola's `motorola.hardware.health` HAL when LineageOS's own HAL is missing. The HAL writes the
stock kernel's charging thresholds. Stock's framework calls the same HAL from the same system
process, so the stock SELinux policy already allows it; nothing else changed
(PORTING_A17.md, "Charging limit").

Static: the adapter is in the image, and the compiled policy lets `system_server` find and call
Motorola's HAL. Not yet seen on the phone.

## Files

| File | Size | SHA-256 |
|---|---|---|
| `system_raw.gz` | 1,476,093,059 bytes | `7f3e1d5961358ddccb3b7756485112e5a8ce7f1fbe06033e342b0225213b4666` |
| `system.img` (what the archive unpacks to) | 3,005,083,648 bytes | `85fe7a9b6395a1eed5d975803ac23b19f0427779de76fbc3713c924369de0195` |

In `out/lineage_vantage-20261112-r4/`, with `SHA256SUMS` and `SIZES`. The image is 12,288 bytes
larger than r3, so the install command's `KEY_SYSTEM_SIZE` changes.

## What was checked

`validate-image.sh` on this image: exit status 0, 102 PASS, **0 FAIL**, 9 WARNING (the same as
r1-r3), 13 UNKNOWN (hardware), 1 INFO. New: `patch.tree:lineage-sdk`, `patch.image:lineage-sdk`
(the adapter is in `/system/framework/org.lineageos.platform.jar`), and the policy queries
system_server -> `hal_mothealth_aidl_service` (find) and -> `hal_mothealth_default` (binder call).

On the phone, r1-r3 booted; r3 runs smoothly (owner's report, 2026-11-11). r4 has not been booted.

## Install

Restart to stock and discard the r3 guest first (notification on stock), then:

```bash
ADB=/h/androidtools/platform-tools/adb.exe bash vendor/motorola/vantage/scripts/dsu-preflight.sh
```

It checks the archive and the phone (read-only) and prints the push and install commands for r4.
For reference, the install command:

```bash
MSYS_NO_PATHCONV=1 adb shell am start-activity -n com.android.dynsystem/com.android.dynsystem.VerificationActivity -a android.os.image.action.START_INSTALL -d file:///storage/emulated/0/Download/system_raw.gz --el KEY_SYSTEM_SIZE 3005083648 --el KEY_USERDATA_SIZE 8589934592 --ez KEY_ONE_SHOT true
```

The guest starts with fresh data. To check the limit from a computer, turn on USB debugging:
`adb shell cat /sys/module/qpnp_adaptive_charge/parameters/upper_limit` (and `lower_limit`)
shows the thresholds the kernel uses, `-1` when there is no limit.
