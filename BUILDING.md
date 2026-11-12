# Building

How to get from this folder to a DSU-installable LineageOS 24 system image for the Motorola
Signature (vantage) on stock Android 17 firmware A171WVH.21-16-16. Every command below was run on
the development machine on 2026-11-11; section 9 is the log of every build.

Order: environment, source tree, stock firmware, build, validation, export.

## 1. What you need

| | |
|---|---|
| Stock firmware package | build **A171WVH.21-16-16** for the Motorola Signature (`vantage_g`): the folder with `flashfile.xml`, here `H:\AndroidRoms\VANTAGE_G_A171WVH.21_16_16_subsidy_DEFAULT_regulatory_DEFAULT_cid50_CFC.xml`. The build copies 32 files out of it and checks each against the SHA-256 in `vendor/motorola/vantage/proprietary-files.txt`; with another firmware build that check stops the build |
| microG release APKs | downloaded by `scripts/fetch-microg.sh` from microG's GitHub release v0.3.17.252432, checked against pinned SHA-256 |
| Disk | an ext4 filesystem with about 400 GB free (see section 9 for the measured sizes) |
| Memory | 32 GB host; the WSL VM gets 24 GB plus compressed RAM swap (zram) |
| Network | github.com (LineageOS, QcRilAm, microG), android.googlesource.com, mirrors.edge.kernel.org (Ubuntu packages; this machine's DNS does not resolve ubuntu.com) |

## 2. Host and build environment

| Item | Value |
|---|---|
| Host | Windows 11 (10.0.26100), Ryzen 7 9800X3D (16 threads), 31 GB RAM |
| Work folder | `J:\lineageos-signature` (NTFS): this project |
| Build environment | WSL2 distro **`lineage-aosp`** (Ubuntu 24.04.5), its disk `J:\lineageos-signature\wsl\lineage-aosp\ext4.vhdx` |

NTFS cannot hold an Android tree, so sources, extracted firmware and build output live on the
distro's ext4 disk. The scripts assume three paths inside the distro:

| Path | What |
|---|---|
| `/proj` | this folder (`/mnt/j/lineageos-signature`) |
| `/stockfw` | the stock firmware folder (read only) |
| `/work` | `/work/lineage` (source tree and `out/`), `/work/fw` (extracted firmware), `/work/tools` |

Optional: `/a16proj` -> the Android 16 project (`H:\androidtools\platform-tools\CUSTOM ROM`), only
used to compare with the Android 16 firmware analysis.

The WSL VM settings come from `C:\Users\<user>\.wslconfig`, created for the Android 16 port
(`memory=24GB`, `processors=16`, `swap=40GB`); all WSL distros share that one VM.

Create the distro. `wsl --install Ubuntu-24.04` could not download on this machine (its DNS does
not resolve ubuntu.com), so the image was fetched from the kernel.org mirror and checked against
the SHA-256 that Microsoft's `DistributionInfo.json` lists
(`bb415d824822c4b878125729af451a5d18fb13d1cf5cbed9a7393ad64ac6039e`):

```bash
curl -fLo ubuntu-24.04.5-wsl-amd64.wsl https://mirrors.edge.kernel.org/ubuntu-releases/24.04.5/ubuntu-24.04.5-wsl-amd64.wsl
```

```bash
wsl --install --from-file ubuntu-24.04.5-wsl-amd64.wsl --name lineage-aosp --location "J:\lineageos-signature\wsl\lineage-aosp" --no-launch
```

Inside the distro, as root: point apt at the kernel.org mirror (only needed where ubuntu.com
does not resolve), create the links and run the bootstrap:

```bash
sed -i -e 's#http://archive.ubuntu.com/ubuntu/\?#http://mirrors.edge.kernel.org/ubuntu/#g' -e 's#http://security.ubuntu.com/ubuntu/\?#http://mirrors.edge.kernel.org/ubuntu/#g' /etc/apt/sources.list.d/ubuntu.sources
```

```bash
ln -sfn /mnt/j/lineageos-signature /proj && ln -sfn "/mnt/h/AndroidRoms/VANTAGE_G_A171WVH.21_16_16_subsidy_DEFAULT_regulatory_DEFAULT_cid50_CFC.xml" /stockfw
```

```bash
bash /proj/vendor/motorola/vantage/scripts/wsl-bootstrap.sh
```

`wsl-bootstrap.sh` installs the build prerequisites, OpenJDK 21, the firmware tools and `repo`,
creates the user `builder` and `/work`. Then, after every start of the VM, as root:

```bash
wsl -d lineage-aosp -u root -e bash /proj/vendor/motorola/vantage/scripts/wsl-zram.sh
```

and keep one command running for the whole session (the VM shuts down a minute after the last
command and loses zram), for example `wsl -d lineage-aosp -e tail -f /dev/null` in a second
terminal.

## 3. Source tree

| Component | Revision |
|---|---|
| LineageOS | branch `lineage-24.0` (AOSP `android-17.0.0_r1`, SDK 37); every project's commit in `manifests/pinned-lineage-24.0.xml` |
| QcRilAm (RIL audio bridge) | `AndyCGYan/android_packages_apps_QcRilAm` @ `dc599b67cc1e7e9a62ca15eef605e3b2546d0d42`, added by a local manifest |
| Release config | `cp2a` (LineageOS's `vendor/lineage/vars/aosp_target_release`) |
| Product | `lineage_vantage` = `lineage_gsi_arm64` + `vendor/motorola/vantage` + microG |

```bash
wsl -d lineage-aosp -u builder -e bash /proj/vendor/motorola/vantage/scripts/sync-source.sh
```

writes the pinned manifest after syncing. To reproduce exactly the tree an image was built from:

```bash
wsl -d lineage-aosp -u builder -e env PINNED=1 bash /proj/vendor/motorola/vantage/scripts/sync-source.sh
```

## 4. Stock firmware

As root, after the source sync (it takes `unpack_bootimg.py` from the tree):

```bash
wsl -d lineage-aosp -u root -e bash /proj/vendor/motorola/vantage/scripts/extract-firmware.sh
```

Stages `unpack` (MD5 check against `flashfile.xml`, `reports/stock-firmware.sha256`, logical
partitions of `super`, filesystem trees, boot images, APEX payloads to
`/work/fw/A171WVH.21-16-16`), `inventory` (`reports/inventory/*.json`; `files.json`, `elf.json`,
`packages.json` are large and not committed; `packages.json` contains API keys of stock apps and
must never be committed) and `blobs` (the pinned files into `vendor/motorola/vantage/proprietary/`,
which is not committed).

## 5. Build

```bash
wsl -d lineage-aosp -u builder -e bash /proj/vendor/motorola/vantage/scripts/sync-to-tree.sh
```

copies `vendor/motorola/vantage` and `device/motorola/vantage` into the tree, applies
`patches/` (four patches: `lineage-sdk`, `packages/apps/QcRilAm`, `system/core`, `vendor/apn`), fetches the microG APKs and
repeats the `blobs` stage inside the tree. Run it after every change in this folder.

```bash
wsl -d lineage-aosp -u builder -e bash /proj/vendor/motorola/vantage/scripts/build.sh
```

builds `lineage_vantage-cp2a-userdebug`, goal `systemimage`; the image is
`/work/lineage/out/target/product/generic_arm64/system.img`. Overrides: `TARGET`, `RELEASE`,
`VARIANT`, `GOALS`, `JOBS` (default 10).

`userdebug` (or `eng`) is required for microG: LineageOS compiles microG's signature spoofing
into those variants only (`vendor/motorola/vantage/microg/README.md`). LineageOS's `userdebug`
still sets `ro.debuggable=0` (no `adb root`); that does not affect microG.

## 6. After moving the source baseline

`target-system-libs.txt` (libraries the image provides) decides which native dependencies of
stock files must be ported. Regenerate it from the build output and resolve the closure again:

```bash
S=/proj/vendor/motorola/vantage/scripts; V=/proj/vendor/motorola/vantage; OUT=/work/lineage/out/target/product/generic_arm64
python3 -I $S/gen_target_libs.py --system $OUT/system --manifest $V/proprietary-files.txt > $V/target-system-libs.txt
python3 -I $S/resolve_components.py /proj/reports $V/components.json $V/proprietary-files.txt --target-system-libs $V/target-system-libs.txt
```

## 7. Validate

```bash
wsl -d lineage-aosp -u root -e bash /proj/vendor/motorola/vantage/scripts/validate-image.sh
```

Runs every static check against the image and the extracted stock A17 vendor (reports in
`reports/vantage/`). Exit status 0 = no FAIL. A static PASS says the files and configuration are
consistent, not that the image works on a phone.

The full VINTF check is separate (it needs the host tool, `GOALS=checkvintf` with `build.sh`):

```bash
wsl -d lineage-aosp -u root -e bash -c 'A=/work/lineage; O=$A/out/target/product/generic_arm64; F=/work/fw/A171WVH.21-16-16/root; $A/out/host/linux-x86/bin/checkvintf --check-compat --dirmap /system:$O/system --dirmap /system_ext:$O/system/system_ext --dirmap /product:$O/system/product --dirmap /apex:$O/apex --dirmap /vendor:$F/vendor --dirmap /odm:$F/odm -D ro.boot.product.vendor.sku=canoe -D ro.product.first_api_level=36 -D ro.board.first_api_level=202504 -D ro.board.api_level=202504'
```

Expected result for this port: only the "unused HALs" list (vendor HALs that Motorola's own
product matrix declares on stock); see COMPATIBILITY.md.

## 8. Export and install

```bash
wsl -d lineage-aosp -u builder -e bash /proj/vendor/motorola/vantage/scripts/export-image.sh lineage_vantage-20261111
```

writes `out/<name>/` (`system.img`, `system_raw.gz`, `SHA256SUMS`, `SIZES`). Installing as a
DSU guest is the owner's step: `scripts/dsu-preflight.sh` checks archive and phone read-only and
prints the commands (`releases/` has the notes for each image).

## 9. Build log

Every build, failures included.

| Date | Target | Result |
|---|---|---|
| 2026-11-11 08:42 | `lineage_vantage-cp2a-userdebug` | Failed after 47 s in the Soong analysis: `build/make/target/product/gsi/Android.bp: "aosp_system_image" depends on undefined module "Calendar"`. LineageOS disables that AOSP image module only for products named `lineage_gsi_*` (`gsi_release.mk` sets `BUILDING_LINEAGE_GSI`). Fixed in `lineage_vantage.mk` by setting the variable; it has no other effect. (A second start at 08:45 was stopped by a terminal hang-up before it did anything.) |
| 2026-11-11 08:46 | same | Soong analysis passed (7 min); Kati failed: `overriding commands for target .../system/product/etc/permissions/ims_ext_common.xml`. LineageOS builds open-source Qualcomm modules named `ims-ext-common`, `qti-telephony-utils` (`vendor/codeaurora/telephony`) and `libaudiohalvendorextn` (`vendor/qcom/opensource/commonsys/audio`); `PRODUCT_PACKAGES` resolved our three names to those instead of the pinned stock files, and the first one's permission file collided with ours. First attempt at a fix: stock library modules renamed to `vantage-stock-<name>` (stock file name kept through `stem`). |
| 2026-11-11 10:53 | same | Kati failed again: `overriding commands for target .../ims-ext-common.odex`. Soong writes install rules for every installable module, requested or not, so LineageOS's source modules still claimed the stock paths. Fixed in `setup_makefiles.py`: stock names again, every prebuilt `prefer: true` (Soong's prebuilt selection then replaces the same-named source module, also from inside our namespace; partitions match). The two permission files (`ims_ext_common.xml`, `qti_telephony_utils.xml`) cannot be replaced that way; LineageOS's copies are byte-identical to the pinned stock files (same SHA-256), so their modules are installed instead of a copy, and the generator stops if the hashes ever differ. A scan of the tree found no other module named like a stock file. |
| 2026-11-11 11:05 | same | Kati failed: `overriding commands for target .../system/product/etc/apns-conf.xml`: LineageOS generates its own APN list (`vendor/apn`) and installs it there. A check of every remaining copy destination against Soong's install rules found no other clash. LineageOS's list for Optimum 313390 lacks the stock initial-attach and tethering APNs (AOSP adds a default emergency profile itself), and the stock A17 list fails LineageOS's APN schema (Motorola attributes), so it cannot go through LineageOS's module. Fixed with a third source patch, `patches/vendor/apn` (an opt-out switch `lineage_apn.use_device_apns`, set in `vantage.mk`), and a generated `prebuilt_etc` named `apns-conf.xml` for the stock file. |
| 2026-11-11 11:15 | same | **Success** after 3 h 16 min (ninja 3 h 7 min, 211,668 steps, 10 jobs; peak 14 GB RAM + 11 GB zram in use). `system.img` 3,005,018,112 bytes, SHA-256 `970f0ecbd33f38963f7c66aecef3d6dff7859b6080756a833086cb2f927bd828`; `out/` 119 GB, disk 294 GB used in total. Expected warning: `PRODUCT_INSTALL_DEBUG_POLICY_TO_SYSTEM_EXT` (from AOSP's `gsi_release.mk`, as in every GSI: `userdebug_plat_sepolicy.cil` in system_ext, used only with a debug ramdisk, which the stock boot image is not). Section 6 regenerated: 786 libraries (was 759; A17 ships `audio.core-V4`/`audio.common-V5` NDK libraries, no HIDL audio), and the stock-file closure resolves to the same 34 entries, byte for byte. First `validate-image.sh` run: 85 PASS, **6 FAIL**, 10 WARNING, 14 UNKNOWN. Two causes in the image: (1) the SELinux mapping for the 202504 vendor did not contain our two app domains (3 FAILs; LineageOS 24's own version is 202604; fixed with `sepolicy/private/compat/202504/202504.cil`), (2) a carrier-config key Qualcomm renamed on A17 (WARNING; renamed). Three causes in the validators: aapt2 output of long arrays and of dimensions (overlay check), LineageOS's WebView provider filter (`isProviderAvailable`), and microG's switch being a compile-time flag rather than `ro.debuggable` (see `microg/README.md`); also no `symbols/` directory any more, so binaries are matched with Soong's unstripped copies by Build ID. Not exported. |
| 2026-11-11 14:42 | same, with the 202504 mapping and the renamed carrier key | **Success**, incremental, 10 min 39 s. `system.img` 3,005,042,688 bytes, SHA-256 `8bfc7466aeb305f88973679bc3abf217884f98f69aa93466141ed87055120031`. `validate-image.sh`: 93 PASS, 0 FAIL, 9 WARNING, 13 UNKNOWN, but exit 1: the SELinux comparison with stock could not open the policies (Ubuntu 24.04's setools/libsepol 3.5 predate Android 17's netlink extended permissions, `Invalid avtab`). New `analysis_policy.py` compiles both sides again from `init`'s inputs without those statements. The comparison then showed two gaps against stock A17: the A17 product mapping adds the camera to `moto_app_202504`, and A17's `hal_client_domain()` adds `memfd_file` rules the IMS app's ATFWD/IMS-VT HAL clients lacked (PORTING_A17.md). Not exported. |
| 2026-11-11 15:04 | same, with `moto_app_202504` in the 202504 mapping and `hal_client_domain()` for the IMS app's ATFWD/IMS-VT HALs | **Success**, incremental, 10 min 55 s. `system.img` 3,005,046,784 bytes, SHA-256 `08286f830556d23364b9c6c9ebb386a8a9d93361be032d86b4f3e20dd8a1a0f8`. `validate-image.sh`: **exit 0**, 94 PASS, 0 FAIL, 9 WARNING (all also in r4's report), 13 UNKNOWN (hardware), 1 INFO (patch level, no rollback branch). SELinux comparison with stock A17: IMS app 0 missing permissions on labels that exist here, camera 2 (`recovery_service`, `vr_manager_service`, as on A16). **Exported** to `out/lineage_vantage-20261111/`: `system_raw.gz` 1,476,095,730 bytes, SHA-256 `f6b9f61d750f969a0051102b35afdd3c878bfa5e1fb4a6a0b6c6f448d756cd9c`; values pinned in `dsu-preflight.sh` (its local checks pass); notes `releases/lineage_vantage-20261111.md`. Booted by the owner the same day: home screen, calls and camera work (owner's report); the status bar clock sat almost in the left corner. |
| 2026-11-11 16:57 | same, r2: stock's SystemUI `rounded_corner_content_padding` (new `VantageSystemUIOverlay`), stock's `rounded_corner_radius` in `VantageDeviceOverlay`, LineageOS's maximum/minimum refresh rate lists shown (new `VantageSettingsOverlay`) | **Success**, incremental, 10 min 19 s. `system.img` 3,005,071,360 bytes, SHA-256 `5a007af90f7872a88a4f271205a0e9d87600a6cbb4e9479983fa4a56ae169db9`. `validate-image.sh`: exit 0, 98 PASS, 0 FAIL, 9 WARNING (as build 7), 13 UNKNOWN, 1 INFO. Exported to `out/lineage_vantage-20261111-r2/`: `system_raw.gz` 1,476,089,615 bytes, SHA-256 `5db4ea03c480fbf5382e83508a451b492cddcac677cb79084fd46ee97b720ee3`; `dsu-preflight.sh` now pinned to r2; notes `releases/lineage_vantage-20261111-r2.md`. Booted by the owner; GPU checked over adb, quick settings and app drawer drop to 60 fps with blur (`reports/ui-smoothness-r2.md`). |
| 2026-11-11 19:36 | same, r3: `debug.sf.use_phase_offsets_as_durations=1` and `debug.sf.enable_adpf_cpu_hint=true` in `/product` (`properties.mk`), stock's `vendor_wlc_public_prop` with its 202504 mapping and `vendor.mpctl.init.complete` label (`sepolicy/`); validators: `built.sf_timing` (new), property_contexts entries in `built.sepolicy`, `sepolicy.mapping:vendor_wlc_public_prop`, three policy queries | **Success**, incremental, 12 min 14 s. `system.img` 3,005,071,360 bytes, SHA-256 `94c1595d00d2302aaa572e543ec288203b3fb50d006f48b3b4780e70c97062bb`. `validate-image.sh`: exit 0, 100 PASS, 0 FAIL, 9 WARNING (as build 8), 13 UNKNOWN, 1 INFO. Exported to `out/lineage_vantage-20261111-r3/`: `system_raw.gz` 1,476,088,834 bytes, SHA-256 `803d80f2dc5c6df25cf4ade80709a35cf1678ba43bdde4e4c2b836c4018e4cc5`; `dsu-preflight.sh` now pinned to r3 (local checks pass); notes `releases/lineage_vantage-20261111-r3.md`. Booted by the owner: "r3 is good on performance now" (owner's report). |
| 2026-11-12 07:18 | same, r4 first attempt: new `patches/lineage-sdk` (charging control through Motorola's `IMotoHealth` HAL); validators: `patch.image:lineage-sdk` (probe reads dex inside `.jar` files now), policy queries system_server -> Motorola's health HAL | **Success**, incremental, 13 min 28 s; `validate-image.sh` exit 0, 102 PASS, 0 FAIL. Exported, then **withdrawn before release**: reading LineageOS's controller showed that with a limit-only HAL the Auto and Custom schedule modes go to the Limit provider, whose time-based callback threw in system_server (Auto is the default mode). |
| 2026-11-12 07:39 | same, with the Limit provider's time-based callback in the same patch (hold at 80 % in the scheduled window, lift the limit in time to be full at the target time) | **Success**, incremental, 13 min 47 s. `system.img` 3,005,083,648 bytes, SHA-256 `85fe7a9b6395a1eed5d975803ac23b19f0427779de76fbc3713c924369de0195`. `validate-image.sh`: exit 0, 102 PASS, 0 FAIL, 9 WARNING (as build 9), 13 UNKNOWN, 1 INFO. Exported to `out/lineage_vantage-20261112-r4/` (replacing build 10's export): `system_raw.gz` 1,476,093,059 bytes, SHA-256 `7f3e1d5961358ddccb3b7756485112e5a8ce7f1fbe06033e342b0225213b4666`; `dsu-preflight.sh` pinned to it (`KEY_SYSTEM_SIZE` 3005083648); notes `releases/lineage_vantage-20261112-r4.md`. |
