# lineage_vantage 2026-11-11 r2 (test image)

> Booted by the owner on 2026-11-11. Known issue found there: quick settings and the app drawer
> run at about 60 fps with blur ([reports/ui-smoothness-r2.md](../reports/ui-smoothness-r2.md));
> workaround: Developer options > Allow window-level blurs off. Superseded by
> [r3](lineage_vantage-20261111-r3.md).

LineageOS 24.0 (Android 17) system image for the **Motorola Signature** (`vantage`) on stock
firmware **A171WVH.21-16-16**, with microG. Same base, keys, patch level (2026-11-01) and
contents as r1 ([lineage_vantage-20261111.md](lineage_vantage-20261111.md), which also lists the
differences from the Android 16 images), plus the two changes below. Built on 2026-11-11 (build 8
in `BUILDING.md` section 9).

## New in r2

**Status bar clock moved away from the corner.** On r1 the clock sat almost in the left
rounded corner. Stock sets a 30px distance between the status bar content and the rounded
corners (`rounded_corner_content_padding`), which AOSP leaves at 0; r2 sets stock's value
(`overlays/VantageSystemUIOverlay`), so the clock moves about 30px to the right and the icons on
the right stay where they are. It also sets stock's display corner radius (100px; r1 used the
vendor's 24dp). Static: both values are in the image; not yet seen on the phone.

**Refresh rate setting.** Settings > Display now has **Maximum refresh rate** and **Minimum
refresh rate** (LineageOS's own options, hidden on r1). Each lists the panel's modes: 165, 120,
90, 60, 30, 24 Hz.

- **165 Hz all the time:** set *Maximum refresh rate* to 165 Hz first, then *Minimum refresh
  rate* to 165 Hz. Both are needed: the 165 Hz mode cannot switch smoothly to the other rates,
  so Android only uses it when it is the only one allowed, and the maximum setting outranks the
  minimum one.
- **Back to the defaults:** set *Minimum* to 24 Hz and *Maximum* to 120 Hz, the values the
  stock `/vendor` configuration sets (`config_defaultMinRefreshRate`, `config_defaultPeakRefreshRate`).
- Battery saver and the thermal limits still lower the rate. 165 Hz uses more battery.

Stock's own selector offered Auto/60/120/144 Hz; it is a Motorola app and not part of this
image. Static: the options' switches are in the image and the lists are built from the display's
modes at run time; not yet seen on the phone.

## Files

| File | Size | SHA-256 |
|---|---|---|
| `system_raw.gz` | 1,476,089,615 bytes | `5db4ea03c480fbf5382e83508a451b492cddcac677cb79084fd46ee97b720ee3` |
| `system.img` (what the archive unpacks to) | 3,005,071,360 bytes | `5a007af90f7872a88a4f271205a0e9d87600a6cbb4e9479983fa4a56ae169db9` |

In `out/lineage_vantage-20261111-r2/`, with `SHA256SUMS` and `SIZES`.

## What was checked

`validate-image.sh` on this image: exit status 0, 98 PASS, **0 FAIL**, 9 WARNING (the same as
r1), 13 UNKNOWN (hardware), 1 INFO. The four new checks: both new overlays target resources
that exist in SystemUI and Settings, and every value in the built overlays equals the source.

On the phone, r1 reached the home screen and calls and Motorola Camera worked (owner's report,
2026-11-11). Nothing else changed between r1 and r2, so that result carries over, but r2 itself
has not been booted.

## Install

Same as r1, with this image's size. Discard the r1 guest first (notification on stock), then:

```bash
ADB=/h/androidtools/platform-tools/adb.exe bash vendor/motorola/vantage/scripts/dsu-preflight.sh
```

It checks the archive and the phone (read-only) and prints the push and install commands for r2.
For reference, the install command:

```bash
MSYS_NO_PATHCONV=1 adb shell am start-activity -n com.android.dynsystem/com.android.dynsystem.VerificationActivity -a android.os.image.action.START_INSTALL -d file:///storage/emulated/0/Download/system_raw.gz --el KEY_SYSTEM_SIZE 3005071360 --el KEY_USERDATA_SIZE 8589934592 --ez KEY_ONE_SHOT true
```

The guest starts with fresh data, as r1 did. adb is off on it until USB debugging is turned on
in Developer options; there is no `adb root` (r1 note).
