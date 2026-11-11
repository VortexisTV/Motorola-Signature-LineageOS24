# microG

Generated: 2026-11-11T17:07:58

**PASS 6 / FAIL 0 / WARNING 0 / UNKNOWN 0**

Static analysis only. PASS means the checked property holds in the files; it does not prove that the feature works on hardware.


| Status | Area | Test | Result |
|---|---|---|---|
| PASS | microg | `microg.apks` | both microG APKs are in /product/priv-app and signed by the same key |
| PASS | microg | `microg.debuggable` | LineageOS's microG check is compiled in: MicrogUtils.isDebuggable() in the image's libandroid_runtime.so returns the constant true |
| PASS | microg | `microg.fake_signature` | both manifests declare fake-signature metadata |
| PASS | microg | `microg.privapp` | allowlist equals the privileged permissions microG requests |
| PASS | microg | `microg.signer` | the APKs are signed with a certificate LineageOS accepts for microG |
| PASS | microg | `microg.sysconfig` | Doze/Data Saver/location exemptions installed |

## Details

### PASS: `microg.apks`

both microG APKs are in /product/priv-app and signed by the same key

- com.google.android.gms: differs from the pinned file; signer 9bd06727e62796c0130eb6dab39b73157451582cbd138e86c468acc395d14165
- com.android.vending: differs from the pinned file; signer 9bd06727e62796c0130eb6dab39b73157451582cbd138e86c468acc395d14165

### PASS: `microg.debuggable`

LineageOS's microG check is compiled in: MicrogUtils.isDebuggable() in the image's libandroid_runtime.so returns the constant true

- libandroid_runtime.so Build ID 57d8f12eb1dd9fab66ead9c01476de3c; _ZN7androidL12isDebuggableEP7_JNIEnvP7_jclass.__uniq.311997348663044173435474281781198079709: mov w0, #0x1; ret
- ro.build.type=userdebug, ro.debuggable=0 (run-time property; 0 means no adb root, it does not affect microG)

### PASS: `microg.fake_signature`

both manifests declare fake-signature metadata

- com.google.android.gms: True
- com.android.vending: True

### PASS: `microg.privapp`

allowlist equals the privileged permissions microG requests

- com.google.android.gms: 14 privileged requested, 14 allowlisted
- com.android.vending: 3 privileged requested, 3 allowlisted

### PASS: `microg.signer`

the APKs are signed with a certificate LineageOS accepts for microG

- source: frameworks/base/core/java/com/android/internal/content/MicrogUtils.java (REAL_SIGNATURE)

### PASS: `microg.sysconfig`

Doze/Data Saver/location exemptions installed

- /system/product/etc/sysconfig/sysconfig-vantage-microg.xml

