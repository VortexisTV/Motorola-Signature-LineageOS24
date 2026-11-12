# Compatibility and status: LineageOS 24 for the Motorola Signature on stock Android 17

Last updated 2026-11-11, for the image `lineage_vantage-20261111-r3` (build 9, `system.img`
SHA-256 `94c1595d00d2302aaa572e543ec288203b3fb50d006f48b3b4780e70c97062bb`). `validate-image.sh`
on that image: exit status 0, 100 PASS, 0 FAIL, 9 WARNING, 13 UNKNOWN, 1 INFO (reports in
`reports/vantage/`). r2 (build 8, `5a007af9…`) differs only by SurfaceFlinger's frame timing and
the perf HAL's property label; r1 (build 7, `08286f83…`) also by the status bar padding, the
corner radius and the refresh rate settings. The device column describes r1, plus the r2
measurements in the GPU row; r3 has not been booted. Columns:

- **Static**: what host-side analysis of sources, stock firmware and the built image established
  (PASS / FAIL / WARNING / UNKNOWN, with the check's name in `code`).
- **Device**: what a phone showed. First DSU boot of `lineage_vantage-20261111` on 2026-11-11
  by the owner: it reached the home screen (screenshots), and the owner reported "the camera
  app and calling works". No logs were captured, so those cells say "owner's report"; every
  other device cell is UNKNOWN. Where the Android 16 port (image r4, A16 stock vendor) worked on
  hardware, that is noted as history, not as evidence for this image.

A static PASS means files and configuration are consistent. It is not evidence that a feature
works.

## Foundation

| Item | Static | Device | Notes |
|---|---|---|---|
| Base: LineageOS 24.0 `lineage_gsi_arm64` (android-17.0.0_r1, SDK 37) | PASS: built (`lineage_vantage-cp2a-userdebug`); `platform.api_levels`: system SDK 37 / LLNDK 202604, vendor SDK 36 / board API 202504 | **boots** to the home screen as a DSU guest (owner, 2026-11-11, screenshots) | FEASIBILITY.md; pinned manifest `manifests/pinned-lineage-24.0.xml` |
| System SDK vs stock system it replaces (37 / 37.0) | PASS (`cp2a`, stock `sdk_full=37.0`) | UNKNOWN | |
| Vendor interface (board API 202504, SELinux 202504) | PASS: the tree's `checkvintf --check-compat` on this image + stock A17 vendor/odm (SKU `canoe`): vendor manifest against the framework matrices, framework manifest against the vendor's matrix, SELinux version, deprecated HALs; kernel requirements not checked. `vintf.radio` PASS. WARNING: its consistency check of unused HALs lists 104 vendor HAL instances (Qualcomm/Motorola, `android.se.omapi`) that only Motorola's product matrix extension declares (stock A17 with it: COMPATIBLE); not checked at boot, HAL registration uses the vendor manifest | UNKNOWN | the A17 vendor is an Android 16 vendor build |
| Combined SELinux policy (image + stock A17 vendor) compiles as A17 `init` does, incl. `plat_sepolicy_genfs_202504.cil` | PASS (`sepolicy.inputs`, `sepolicy.compile`: 12 CIL files); the vendor's rules bind to our domains (`sepolicy.mapping` for `vendor_qtelephony`, `moto_camera_app`, `moto_app`→camera) | UNKNOWN | boot-critical. The 202504 mapping needs `sepolicy/private/compat/202504/202504.cil` on Android 17 (PORTING_A17.md) |
| Privileged-permission allowlists (enforce) | PASS (`privapp.allowlist`, `permissions.privapp`, `microg.privapp`) | UNKNOWN | boot-critical |
| Image layout (system_ext + product inside, `skip_mount.cfg`) | PASS (`layout.single_image`, `layout.skip_mount`; the stock first-stage `init` applies `skip_mount.cfg`: `init.skip_mount`) | UNKNOWN | |
| Security patch level vs stock (rollback check of the stock first-stage `init`) | INFO: image 2026-11-01, stock 2026-08-01: no rollback branch (`image.spl`) | UNKNOWN | test keys still need an unlocked bootloader (`init.unlock_state`) |
| Signing | AOSP/Lineage **test keys** (owner's decision for now) | n/a | must change before daily use; microG then needs a `userdebug`/`eng` build (see microG) |
| Debugging | `ro.debuggable=0` (LineageOS's `userdebug` default): no `adb root`; adb starts off on a fresh guest, needs USB debugging and the key prompt | UNKNOWN | the A16 images had adb on without a prompt, and root. One line in `lineage_vantage.mk` changes it (owner's decision) |

## Cellular (priority 1)

| Feature | Static | Device | Notes |
|---|---|---|---|
| Radio HAL AIDL V4, both slots | PASS (`radio.hal.standard`: 7 AIDL HALs; `vintf.radio`; `radio.vendor_daemons`) | UNKNOWN (A16 r4: worked) | |
| SIM, registration, LTE/5G data | no device-specific change needed; `ro.telephony.default_network=26,26` restated (`built.properties`) | UNKNOWN (A16 r4: worked) | |
| APN database | PASS (`carrier.apn`; `patch.image:vendor/apn`: the image holds the pinned stock A17 file) | UNKNOWN | A17 stock `apns-conf.xml` |
| IMS service (A17 `org.codeaurora.ims`, shared UID `android.uid.qtiphone`, process `com.qti.phone`) | PASS (`ims.package`, `telephony.ims_binding`, `stock.resigned`, `built.sepolicy`, `qti.client:ims`); SELinux comparison with stock A17: nothing stock allows on a label that exists here is missing. WARNING `java.linkage:ims.apk`: one constructor of the VICE parser does not resolve (same as on A16) | UNKNOWN (A16 r4: worked with the A16 app) | the process-name SELinux line is new for A17 (PORTING_A17.md) |
| IMS network request (`VantageImsNetwork`) | PASS (`ims.network_request`) | UNKNOWN (A16 r4: worked) | |
| VoLTE calls | cannot be established statically; `carrier.volte_flag` PASS | **calls work** (owner's report, 2026-11-11; no log, so VoLTE vs. other bearer not recorded) | |
| Call audio (QcRilAm + audio vendor extension) | PASS (`built.qcrilam_patched`, `audio.bridge_recovery`, `audio.bridge_single_owner`, `audio.call_rx_swoutput`, `qti.client:am`, `built.audio_vendor_extension`; SELinux queries for the parameter-parser service allowed) | UNKNOWN (A16 r4: worked) | |
| SMS send / receive (`VantageRilReady`) | PASS (`built.ril_ready`) | UNKNOWN (A16 r4: worked) | A17 RIL still holds incoming SMS until the ready hook |
| Video calling | **not offered**: back end `imsvtdaemon` not ported; `carrier.video_calling_off` PASS | expected absent | FIRMWARE_A17.md section 3 |
| Wi-Fi calling | **not offered** (as on A16: CNE's Motorola-key permissions; `vendor.oem_signed_apps` WARNING) | expected absent | |
| eSIM | not supported | expected absent | |

## Motorola Camera (priority 2)

| Feature | Static | Device | Notes |
|---|---|---|---|
| Motorola Camera 10.0.56.80 installs with its original signature, library, permissions, SELinux domain | PASS (`app.installed`, `app.required_libraries`, `permissions.privapp`, `selinux.app_context`, `java.linkage:MotCamera5.apk`); SELinux comparison with stock A17: missing only `recovery_service` and `vr_manager_service` lookups (as on A16; the app does not reference them). WARNING `permissions.unavailable` (6 Motorola permissions, as on A16) | **the camera app works** (owner's report, 2026-11-11; which lenses and modes were tried not recorded) | the A17 vendor rules for Motorola apps (`moto_app_202504`) apply to the camera, as on stock A17 |
| Six cameras (vendor-framework flag readable only by the camera HAL) | PASS (`built.vendor_framework_flag`; policy query: camera HAL allowed, 7 other vendor domains refused) | UNKNOWN | |
| Video mode (camcorder profile file) | PASS (`built.media_profiles`, `video.dolby_vision_inputs`) | UNKNOWN | |
| Native libraries inside the camera APK resolve | PASS (`native.vendor_public`; 46 libraries symbol-checked, 0 unresolved). WARNING `native.vendor_private` (17 vendor-private libraries, identical on stock) | UNKNOWN | |

## microG

| Feature | Static | Device | Notes |
|---|---|---|---|
| GmsCore 0.3.17.252432 + Companion 0.3.17.40226 installed, signed by microG | PASS (`microg.apks`: the pinned release files; `microg.privapp`, `microg.sysconfig`) | UNKNOWN | `vendor/motorola/vantage/microg/README.md` |
| Signature check (LineageOS's built-in, `userdebug`/`eng` builds) | PASS (`microg.signer`, `microg.fake_signature`, `microg.debuggable`: `MicrogUtils.isDebuggable()` in the image's `libandroid_runtime.so` returns the constant true, although `ro.debuggable=0`) | UNKNOWN | |
| Push messages, location, sign-in | cannot be established statically | UNKNOWN | user enables device registration and Cloud Messaging in microG settings |

## Other hardware

| Feature | Static | Device | Notes |
|---|---|---|---|
| Display cutout, status bar, fingerprint position, ambient display (`VantageDeviceOverlay`) | PASS (`built.overlay`: 13 values equal the source; `overlays.precedence`: no active overlay overrides them, some optional cutout emulations could at run time) | r1: status bar laid out around the punch hole (screenshots), but the clock sat almost in the left rounded corner (owner). r2 adds stock's SystemUI `rounded_corner_content_padding` (30px) and framework `rounded_corner_radius` (100px): r2 booted, clock position not reported yet | stock values |
| Brightness, Night Light, colour modes | from the stock `/vendor` overlay (unchanged) | UNKNOWN | |
| Refresh rate | stock `/vendor` overlay: default peak 120 Hz, minimum 24 Hz. Panel modes 165, 120, 90, 60, 30, 24 Hz (A16 captures; 165 Hz is a mode group of its own). r2: Settings > Display > Maximum / Minimum refresh rate (`VantageSettingsOverlay`); 165 Hz needs both set to 165 | r2 booted; the new settings not reported on yet (r2 ran at the default 24-120 Hz during the smoothness measurement) | PORTING_A17.md |
| GPU, UI smoothness | r3: PASS `built.sf_timing` (SurfaceFlinger in work-duration mode with the vendor's durations, ADPF CPU hint on, no phase-offset property it would abort on), `sepolicy.mapping:vendor_wlc_public_prop` | r2 (measured over adb, `reports/ui-smoothness-r2.md`): GPU works (Adreno 829, GLES SurfaceFlinger, Vulkan HWUI). Quick settings and app drawer 40 % janky (60 fps) with blur, 1-2 % with window blurs off. r3 not yet measured | PORTING_A17.md; workaround on r2: Developer options, "Allow window-level blurs" off |
| WebView | PASS (`built.webview_default`: `com.android.webview`; LineageOS skips uninstalled providers) | UNKNOWN | |
| Wi-Fi | standard vendor HAL | r1: connected (Wi-Fi icon in the owner's screenshot) | |
| Bluetooth, GNSS, NFC, sensors, fingerprint | standard vendor HALs, unchanged from A16 | UNKNOWN (untested on A16 as well) | |

## Warnings reviewed

All 9 WARNINGs were reviewed; each one also appears in the Android 16 image r4's report:
`java.linkage:moto-telephony.jar` (`Build.SOC_MANUFACTURER_IS_MTK`, a Motorola framework
field), `java.linkage:ims.apk` (r4 had one more unresolved reference), `sepolicy.unmapped`
(the `IAtCmdFwd` HIDL service, whose stock server is not ported), `radio.hal.aosp_ims`,
`vendor.oem_signed_apps`, `app.optional_libraries`, `native.vendor_private`,
`permissions.unavailable`, and `overlays.precedence` (now including `VantageDeviceOverlay`:
only optional cutout emulations could override its values at run time). The 13 UNKNOWNs are the
hardware items only a phone can answer.

## Open items

1. The first DSU boot (r1) was reported without logs. A session with `device-session.sh` (after
   enabling USB debugging on the guest) would turn the remaining UNKNOWNs (SMS, data, IMS
   registration, call audio both ways, microG, SELinux denials) into evidence.
2. Video calling: porting `imsvtdaemon` (binary, AIDL library, SELinux domain from stock's
   system_ext policy) would be a separate piece of work.
3. Release keys; microG then requires keeping a `userdebug`/`eng` build variant or giving up the
   spoofed signature.
4. `adb root` / adb at first boot: LineageOS's default kept; restoring the A16 behaviour is the
   owner's decision (security-relevant).
5. Licence: QcRilAm still has no licence file (as on A16).
6. UI smoothness on r3: repeat the r2 measurement (`reports/ui-smoothness-r2.md`). If blur still
   drops frames, the remaining difference to stock is Qualcomm's SurfaceFlinger extensions and the
   `QPerformance`/`UxPerformance` boost hints, which would mean porting framework code.
