# lineage_vantage 2026-11-11 r3 (test image)

> Superseded by [r4](lineage_vantage-20261112-r4.md) (adds the charging limit).

LineageOS 24.0 (Android 17) system image for the **Motorola Signature** (`vantage`) on stock
firmware **A171WVH.21-16-16**, with microG. Same base, keys, patch level (2026-11-01) and
contents as r2 ([lineage_vantage-20261111-r2.md](lineage_vantage-20261111-r2.md)), plus the
change below. Built on 2026-11-11 (build 9 in `BUILDING.md` section 9).

## New in r3: smoother quick settings and launcher

On r2 the GPU works, but pulling down quick settings or opening the app drawer ran at about
60 fps instead of 120, with about 40 % janky frames (measured over adb,
[reports/ui-smoothness-r2.md](../reports/ui-smoothness-r2.md)). The cause is the background blur:
SurfaceFlinger then composes the whole screen on the GPU, needs about 10.5 ms per frame while the
CPU stays at its lowest clocks, and has only 7.3 ms. With window blurs off it was 1-2 %.

r3 changes three things:

- **SurfaceFlinger uses the vendor's frame budgets.** The stock vendor sets work durations for
  this phone (10.5 ms for SurfaceFlinger, 13.67 ms for apps) that AOSP's SurfaceFlinger ignored;
  r3 turns that mode on (`debug.sf.use_phase_offsets_as_durations=1`). A blurred frame then has
  more than one refresh to be composed, at the cost of about one frame of extra touch-to-screen
  latency.
- **SurfaceFlinger asks for higher clocks when it runs late** (`debug.sf.enable_adpf_cpu_hint=true`,
  Android's ADPF hint session, which the vendor's power HAL supports).
- **The Qualcomm perf HAL can report that it has started** (`vendor.mpctl.init.complete`): its
  SELinux label, missing on r1/r2, is back as on stock.

Static: all three are in the image, and SurfaceFlinger's start-up conditions for the new mode
are met (`built.sf_timing`). On the phone: "r3 is good on performance now" (owner's report,
2026-11-11; not measured over adb). If quick settings still stutters on another setup,
turn off **Developer options > Allow window-level blurs**: on r2 that gave a steady 120 fps.

## Files

| File | Size | SHA-256 |
|---|---|---|
| `system_raw.gz` | 1,476,088,834 bytes | `803d80f2dc5c6df25cf4ade80709a35cf1678ba43bdde4e4c2b836c4018e4cc5` |
| `system.img` (what the archive unpacks to) | 3,005,071,360 bytes | `94c1595d00d2302aaa572e543ec288203b3fb50d006f48b3b4780e70c97062bb` |

In `out/lineage_vantage-20261111-r3/`, with `SHA256SUMS` and `SIZES`.

## What was checked

`validate-image.sh` on this image: exit status 0, 100 PASS, **0 FAIL**, 9 WARNING (the same as
r1 and r2), 13 UNKNOWN (hardware), 1 INFO. New checks: `built.sf_timing`, the property_contexts
entries in `built.sepolicy`, `sepolicy.mapping:vendor_wlc_public_prop`, and the compiled policy
lets the perf HAL set the property, the display HAL read it and the power HAL set the scheduling
of SurfaceFlinger.

On the phone, r1 and r2 booted (home screen, calls, Motorola Camera; owner's report). r3 booted
and runs smoothly (owner's report, 2026-11-11).

## Install

Restart to stock and discard the r2 guest first (notification on stock), then:

```bash
ADB=/h/androidtools/platform-tools/adb.exe bash vendor/motorola/vantage/scripts/dsu-preflight.sh
```

It checks the archive and the phone (read-only) and prints the push and install commands for r3.
For reference, the install command:

```bash
MSYS_NO_PATHCONV=1 adb shell am start-activity -n com.android.dynsystem/com.android.dynsystem.VerificationActivity -a android.os.image.action.START_INSTALL -d file:///storage/emulated/0/Download/system_raw.gz --el KEY_SYSTEM_SIZE 3005071360 --el KEY_USERDATA_SIZE 8589934592 --ez KEY_ONE_SHOT true
```

The guest starts with fresh data. adb is off on it until USB debugging is turned on in
Developer options. To repeat the smoothness measurement, turn USB debugging on and tell the
session that built this image.
