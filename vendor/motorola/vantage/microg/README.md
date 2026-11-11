# microG

The owner asked for microG on 2026-11-11. microG is an open-source implementation of Google
Play services (`com.google.android.gms`) and of the Play Store's client interfaces
(`com.android.vending`, "microG Companion"). Apps that use Google's client libraries talk to it
for push messages, location, account sign-in and licence checks.

## What is in the image

| Module | Package | Installed as | Source |
|---|---|---|---|
| `GmsCore` | `com.google.android.gms` 0.3.17.252432 (versionCode 252432034) | `/product/priv-app/GmsCore` | microG release `v0.3.17.252432` (2026-09-29), asset `com.google.android.gms-252432034.apk` |
| `MicrogCompanion` | `com.android.vending` 0.3.17.40226 (versionCode 84022634) | `/product/priv-app/MicrogCompanion` | same release, asset `com.android.vending-84022634.apk` |
| `privapp-permissions-vantage-microg.xml` | | `/product/etc/permissions` | written here |
| `sysconfig-vantage-microg.xml` | | `/product/etc/sysconfig` | written here |

`scripts/fetch-microg.sh` downloads both APKs from microG's GitHub release and checks them
against the SHA-256 that GitHub publishes for the asset. The APKs are not committed. This
release is the same version LineageOS for microG ships (`lineageos4microg/android_vendor_partner_gms`,
`.version_code` files at commit `8b49146`).

Not included: the F-Droid client and its privileged extension (LineageOS for microG adds them;
not asked for), GsfProxy (a legacy component that microG's current releases no longer
publish; LineageOS for microG still adds it), Google's own apps, and the
"Play Integrity" property patch LineageOS for microG offers (it changes `system/core` to report
another device's fingerprint; not done).

## How the signature check works, and what it means for security

Apps verify that `com.google.android.gms` carries Google's certificate before they talk to it.
microG cannot have Google's certificate, so it declares Google's certificate in its manifest
metadata (`fake-signature`) and the OS reports that one to other apps. This is "signature
spoofing".

No patch of ours does this. LineageOS has it built in since 2024 (LineageOS `frameworks/base`
change "Allow signature spoofing for microG Companion/Services"), and only when **all** of these
hold:

- the build variant is `userdebug` or `eng`; a `user` build never spoofs. This is a
  compile-time switch (`MicrogUtils.isDebuggable()` is native and returns the flag
  `ANDROID_DEBUGGABLE`, which Soong sets for those variants), not the run-time property
  `ro.debuggable`: LineageOS's own `userdebug` builds set `ro.debuggable=0`
  (`PRODUCT_NOT_DEBUGGABLE_IN_USERDEBUG`, so no `adb root`) and still spoof,
- the package is `com.google.android.gms` or `com.android.vending`,
- the package is signed with microG's release key (the certificate is compiled into the
  framework),
- the declared fake signature is Google's.

So no other app can use the mechanism, and a re-signed or rebuilt microG would install but not
be recognised. `scripts/validate-microg.py` reads the certificate from the built framework and
compares it with the APKs' signing certificate, and disassembles `isDebuggable()` in the
image's `libandroid_runtime.so` (through its unstripped copy with the same Build ID) to confirm
it returns the constant true.

Consequence for later: if this ROM is ever built as `user` with release keys, microG will run
but apps will not accept it.

## Permissions

Privileged permissions: exactly those the two APKs request and LineageOS 24.0 defines as
`privileged` (14 for GmsCore, 3 for Companion, derived with `aapt` from the APKs and from
`core/res/AndroidManifest.xml`; `validate-microg.py` re-derives them from the image). The
image enforces the privileged-permission allowlist, so a missing entry stops the boot; an extra
one would grant more than microG asks for. `FAKE_PACKAGE_SIGNATURE` does not exist in LineageOS
24.0 and is not listed.

Notable grants: Companion receives `INSTALL_PACKAGES` and `DELETE_PACKAGES` (it can install
apps the user obtains through it, as the Play Store does on stock), GmsCore receives
`INSTALL_LOCATION_PROVIDER` (it acts as the network location provider).

Runtime permissions (location, contacts, phone, SMS, camera, notifications) are **not**
pre-granted. microG's self-check screen asks for them; LineageOS for microG pre-grants them,
which was not copied.

Power: `sysconfig-vantage-microg.xml` exempts GmsCore from Doze and Data Saver (its push
connection serves every app) and from background location throttling, as stock does for Google
Play services.

## Status

Static only. Nothing about microG has been tested on the phone.
