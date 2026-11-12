# Motorola Signature (vantage): LineageOS 24 (Android 17) system image

A LineageOS 24.0 generic system image for the Motorola Signature (codename `vantage`, product
`vantage_g`, SM8845 "canoe"), with the vantage integration layer and microG, for the unchanged
stock **Android 17** firmware A171WVH.21-16-16. It is the successor of the Android 16 port
(`Motorola-Signature-AOSP16`, image r4, AOSP 16 + TrebleDroid), whose stock
vendor no longer matches the phone since the owner installed stock Android 17.

> Status: see [COMPATIBILITY.md](COMPATIBILITY.md). Every claim is labelled **static**
> (files and sources), **build**, **boot** or **hardware-tested**. Installing it as a DSU guest
> is the owner's step. Current image:
> `out/lineage_vantage-20261111-r2/` (static validation without FAIL), notes in
> [releases/lineage_vantage-20261111-r2.md](releases/lineage_vantage-20261111-r2.md). r1
> booted on the phone on 2026-11-11 (calls and camera work, owner's report).

## Documents

| | |
|---|---|
| [FIRMWARE_A17.md](FIRMWARE_A17.md) | step 1: the A17 firmware analysed and compared with the A16 build |
| [PORTING_A17.md](PORTING_A17.md) | step 2: everything re-derived, and keep/adapt/drop for each Android 16 fix |
| [BUILDING.md](BUILDING.md) | environment, sync, firmware, build, validation, export, build log |
| [COMPATIBILITY.md](COMPATIBILITY.md) | status per feature, with how each was verified |
| [releases/](releases/) | notes per exported image: hashes, install steps, differences from the A16 image |
| [vendor/motorola/vantage/microg/README.md](vendor/motorola/vantage/microg/README.md) | microG: what is included and how the signature check works |

## Architecture

```
 LineageOS 24.0 (android-17.0.0_r1, SDK 37), product lineage_gsi_arm64          built here
 └─ system image (system + system_ext + product, GSI layout, skip_mount.cfg)
     ├─ vendor/motorola/vantage  (integration layer)
     │   ├─ stock A17 Qualcomm IMS + libraries, Motorola Camera 10.0.56.80   pinned by SHA-256
     │   ├─ properties the stock vendor reads, overlays, allowlists, SELinux types
     │   ├─ VantageImsNetwork, VantageRilReady, audio vendor-extension loader  built from source
     │   └─ microG GmsCore + Companion (official release APKs)
     └─ QcRilAm (TrebleDroid's RIL audio bridge, patched)
 ─────────────────── Treble boundary (VINTF, AIDL HALs, SELinux policy 202504) ───────────────
 Stock Motorola Android 17 partitions, untouched: vendor (an Android 16 vendor build,
 WWV36HV-16-ST1.1), odm, vendor_dlkm, system_dlkm, boot, init_boot, vendor_boot, modem, ...
```

## Install `system.img` using Fastboot

Place `system.img` and the matching stock `vbmeta.img` in the directory containing the Platform Tools, or run the commands from the directory containing those images with Platform Tools in your `PATH`.

### 1. Enter the bootloader

```bash
adb reboot bootloader
fastboot devices
```

Confirm that your phone is listed.

### 2. Check the OTA snapshot state

```bash
fastboot getvar snapshot-update-status
```

The status should be `none`. **Do not continue if a snapshot merge/update is in progress.**

### 3. Flash `vbmeta` with verification disabled

```bash
fastboot --disable-verity --disable-verification flash vbmeta vbmeta.img
```

This changes verified-boot behavior and requires the device's bootloader to be unlocked.

### 4. Enter FastbootD

```bash
fastboot reboot fastboot
```

Wait for **FastbootD** (userspace fastboot) to appear. The `system` partition is a dynamic logical partition and should be flashed from FastbootD.

### 5. Flash the system image

```bash
fastboot flash system system.img
```

Wait for a successful result. **If flashing fails, stop; do not proceed to reboot as if installation succeeded.**

### 6. Wipe user data and reboot

```bash
fastboot -w
fastboot reboot
```

> [!CAUTION]
> `fastboot -w` performs a factory reset and **deletes user data**.

The first boot may take longer than usual.


## Layout

| Path | Content |
|---|---|
| `vendor/motorola/vantage/` | integration layer (synced into the tree by `scripts/sync-to-tree.sh`) |
| `vendor/motorola/vantage/proprietary/`, `microg/prebuilt/` | stock files and microG APKs: fetched/extracted, **never committed** |
| `device/motorola/vantage/` | product `lineage_vantage` |
| `patches/` | `packages/apps/QcRilAm`, `system/core`, `vendor/apn` (three patches) |
| `manifests/` | pinned manifest of the LineageOS tree |
| `reports/` | firmware inventory and validation reports |
| `releases/` | notes per exported image |
| `out/`, `work/`, `wsl/` | exported images, scratch, build VM disk (not committed) |

## Ground rules (owner's)

Nothing is flashed, unlocked or wiped; modem/persist/EFS/calibration are never touched; DSU
installs and on-device tests are the owner's. SELinux stays enforcing. No signature-bypass
hacks of our own (microG relies on LineageOS's built-in, microG-only mechanism; see its README).
Stock binaries are never committed. AOSP test keys for now.
