# Stock Android 17 firmware: analysis and comparison with the Android 16 build

Step 2 of the LineageOS port, done 2026-11-11 with the Android 16 port's scripts. Every
statement here is a **static check** on the firmware package; nothing was run on the phone.

Machine-generated details: [reports/firmware-a16-vs-a17.md](reports/firmware-a16-vs-a17.md)
(`compare_firmware.py`), `reports/stock-firmware-hashes.md`, `reports/inventory/*.json`
(three large files are not committed), `reports/prop-users-a17.json`.

## 1. Package and integrity

| | |
|---|---|
| Package | `VANTAGE_G_A171WVH.21_16_16_subsidy_DEFAULT_regulatory_DEFAULT_cid50_CFC.xml` (read only) |
| Integrity | `firmware_hashes.py`: 53 of 53 images match the MD5 in `flashfile.xml`, 0 mismatches, 0 missing. The SHA-256 list (`reports/stock-firmware.sha256`) is identical to the one taken on 2026-11-10 |
| Extracted to | `/work/fw/A171WVH.21-16-16` in WSL distro `lineage-aosp` (VHDX on J:) by `extract-firmware.sh` (stages `unpack inventory`) |
| `super` | LP metadata v10.2, 31,138,512,896 bytes, group `mot_dp_group_a` max 31,134,318,592, used 18,066,563,072 by slot a; every logical partition is EROFS |

## 2. What changed between the two builds

| Item | Android 16 (W2WVS36.55-95-5-1) | Android 17 (A171WVH.21-16-16) | Consequence for the port |
|---|---|---|---|
| system / system_ext / product | Android 16, SDK 36.0, `W2WVS36M.55-95-ST2.6` | Android 17, **SDK 37.0**, `A171WVM-16-ST1.1`, security patch 2026-08-01 | the system image must be SDK 37: LineageOS 24.0 (`android-17.0.0_r1`, release config `cp2a`, SDK 37) |
| vendor / odm / dlkm | `W2WVS36V.55-95-ST2.6`, Android 16 | `WWV36HV-16-ST1.1`, **still an Android 16 vendor** (`ro.vendor.build.version.sdk=36`), security patch 2026-08-01 | same Treble boundary as before |
| Vendor API level | `ro.board.api_level=202504`, first 202504, `ro.product.first_api_level=36` | unchanged | |
| Vendor manifests | `manifest_alor.xml`, `manifest_canoe.xml`, target-level 202504 | the same two plus `manifest_whale.xml`, all target-level 202504 | |
| Framework matrices on the stock system | 5, 6, 7, 8, 202404, 202504 | 7, 8, 202404, 202504, **202604** | the vendor's 202504 manifest is inside every Android 17 matrix set |
| Vendor SELinux policy | version 202504, genfs labels 202504 | version 202504, genfs labels 202504; `vendor_sepolicy.cil` rebuilt | system policy must ship mapping `202504` and `plat_sepolicy_genfs_202504.cil` |
| Versioned system types used by the vendor policy | 1,850 | 1,852 (`adaptivemmd`, `hal_thermal_ext_aidl_service` added; neither on the telephony/camera path) | |
| Vendor rules on the layer's re-declared types (`vendor_qtelephony`, `moto_camera_app`, four attributes) | 20 + 9 rules | the same rules (only the two large attribute-set lines differ) | `sepolicy/public` carries over unchanged |

### HAL interfaces (vendor + odm manifests)

Of all radio, IMS, camera, audio, Bluetooth, GNSS, NFC, biometrics, Wi-Fi, power and media
HAL entries, **one** differs: `motorola.hardware.health` gained version 3. Unchanged, among
others: `android.hardware.radio.*` AIDL **V4** on `slot1`/`slot2`, `vendor.qti.hardware.radio.ims`
V20, `qtiradio` V16, `android.hardware.camera.provider` V3, `android.hardware.audio.core` V3,
`vendor.qti.hardware.radio.am` (`IQcRilAudio/slot1,2`, the call-audio bridge's HAL),
`vendor.qti.hardware.radio.qcrilhook` (`IQtiOemHook/oemhook0,1`, used by `VantageRilReady`).

### Apps the port uses

| App | Android 16 | Android 17 | Notes |
|---|---|---|---|
| Motorola Camera `com.motorola.camera5` | 10.0.56.61 (10005661), min/target SDK 35 | **10.0.56.80** (10005680), min/target SDK 35, same Motorola certificate (`be8804a5…`), 46 native libraries (47 before) | same `uses-library` set: `com.motorola.motosignature` (required), `moto-settings`, `moto-core_services`, `moto-active-stylus`, `androidx.window.*` (optional); same 3 privileged permissions |
| `com.motorola.motosignature.app` | 1.0 | 1.0, file changed | |
| Qualcomm IMS `org.codeaurora.ims` | min SDK 36, standalone | **min SDK 37**, **`sharedUserId=android.uid.qtiphone`**, application **`android:process="com.qti.phone"`**, persistent | see section 3 |
| `com.qualcomm.qti.telephonyservice` (stock RIL audio client) | present | **removed** | irrelevant: the port uses QcRilAm |
| `com.qti.phone` (QtiTelephony) | 16 | 17 | not ported, as before |

Shared libraries the stock system side no longer declares: `com.android.extensions.appfunctions`,
`com.android.nfc_extras`, `com.motorola.hardware.camera.desktop`.

### Files pinned by the Android 16 port

Of the 36 lines of the A16 `proprietary-files.txt`: 10 files unchanged, 23 changed,
`libimscamera_jni.so` and its symlink gone, one symlink unchanged. Every pin is re-derived from
the A17 inventory (step 3, `proprietary-files.txt`).

## 3. Findings that change the port

1. **The IMS app moved into Qualcomm's telephony process.** On A17 `org.codeaurora.ims` shares
   UID `android.uid.qtiphone` with `com.qti.phone` and `com.qualcomm.qcrilmsgtunnel` and runs in
   the process `com.qti.phone`. Android picks an app process's SELinux domain from the process
   name, so the policy needs stock's line `name=com.qti.phone domain=vendor_qtelephony` as well as
   the existing `name=org.codeaurora.ims` one, or IMS would run as `platform_app` without the
   vendor rules for `vendor_qtelephony`. Only one string links the IMS code to `com.qti.phone` (a
   broadcast action for a C-IWLAN notification), so the other two packages are not needed.
2. **Video calling moved to a system_ext daemon.** The A17 IMS app gets its video-telephony
   back end from `vendor.qti.ImsVtService.IImsVtRequest/ImsVtService`, served on stock by the new
   on-demand daemon `/system_ext/bin/imsvtdaemon` (own SELinux domain and service type in stock's
   system_ext policy, 157 policy references). It fetches it with `ServiceManager.waitForService`
   when a **video** call starts (`MediaController.onSessionAdded` checks `isVideoCall` first; the
   AIDL-or-JNI choice `isMediaAidlSupported()` reads `ro.board.api_level` /
   `ro.product.first_api_level`). Voice calls do not reach that code. The daemon is not ported;
   video calling stays off as it effectively was on A16 (`carrier_vt_available_bool` is not
   enabled by the carrier overlay, AOSP default false); `validate-telephony.py` checks that.
3. **The IMS app dropped its HIDL fallback** (`vendor.qti.hardware.radio.ims@1.x`); it needs the
   AIDL V20 service, which the vendor provides. `qti-telephony-hidl-wrapper` is no longer used.
4. **The RIL still holds incoming SMS** until the "telephony ready" OEM hook: the A17 RIL property
   database ends with `persist.vendor.radio.poweron_opt` default `1` (`0006.0_config.sql` inserts
   0, `0010`, `0011`, `0012` set 1). `VantageRilReady` stays.
5. **Camcorder profiles are still chosen by a vendor variant**: `init.qti.media.rc` and
   `init.qcom.rc` set `ro.media.xml_variant.codecs` from `vendor.media.target_variant`;
   `/vendor/etc/media_profiles_canoe_sku{1,2,3}.xml` exist next to `media_profiles_V1_0.xml`.
6. **The vendor-framework flag is still read**: `libqti_vndfwk_detect_vendor.so` contains
   `ro.vendor.qti.va_aosp.support` and `ro.vendor.qti.va_odm.support`.

## 4. Properties

`prop_users.py` (static successor of the A16 port's `propusers.py`): the A17 system side sets 382
properties (A16: 358); 40 of them are named in stock vendor/odm files (A16: 41).

- Every property of the A16 `properties.mk` has the same stock value on A17, except
  `persist.sys.dolby.upmapping.filter.notify`, which the A17 system side no longer sets.
- The other vendor-read properties are build identity and generic values that LineageOS sets
  itself, or values the A16 port already reviewed and left out (unchanged on A17).

What TrebleDroid set at run time on the A16 guest (properties in its boot scripts that had a
value on the r4 guest and are not set by the vendor): `sys.usb.ffs.aio_compat`,
`persist.adb.nonblocking_ffs`, `persist.sys.qcom-brightness` (scaling for TrebleDroid's own
brightness patch), `persist.sys.overlay.nightmode` / `devinputjack` (TrebleDroid overlays),
`ro.config.media_vol_*`, `ro.hw.oemName`, `ro.keymaster.*`, `sys.usb.all_controllers`. None of
them is set by the stock system side, so without TrebleDroid the phone gets stock's behaviour for
the first three; the overlay-backed ones are covered by the overlay review (step 3).
