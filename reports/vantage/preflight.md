# Preflight: preflight

Generated: 2026-11-11T19:37:08

**PASS 31 / FAIL 0 / WARNING 3 / UNKNOWN 0**

Static analysis only. PASS means the checked property holds in the files; it does not prove that the feature works on hardware.

- manifest: `/proj/vendor/motorola/vantage/proprietary-files.txt`
- maps: `/system=/work/lineage/out/target/product/generic_arm64/system /system_ext=/work/lineage/out/target/product/generic_arm64/system/system_ext /product=/work/lineage/out/target/product/generic_arm64/system/product /apex=/work/lineage/out/target/product/generic_arm64/apex /vendor=/work/fw/A171WVH.21-16-16/root/vendor /odm=/work/fw/A171WVH.21-16-16/root/odm`

| Status | Area | Test | Result |
|---|---|---|---|
| WARNING | java | `java.linkage:ims.apk` | 1 references do not resolve against this image (0 more are also unresolved on stock) |
| WARNING | java | `java.linkage:moto-telephony.jar` | 1 references do not resolve against this image (0 more are also unresolved on stock) |
| WARNING | selinux | `sepolicy.unmapped` | 1 empty versioned attributes belong to labels the vendor's own context files assign; vendor rules on those objects are dead (review each) |
| PASS | image | `image.size` | system image (2866 MiB) fits the dynamic partition group with 10.1 GiB to spare |
| PASS | java | `java.linkage:MotCamera5.apk` | all external references resolve (6 unresolved, all pre-existing on stock) |
| PASS | java | `java.linkage:MotoSignatureApp.apk` | all external references resolve |
| PASS | java | `java.linkage:com.motorola.motosignature.jar` | all external references resolve |
| PASS | java | `java.linkage:ims-ext-common.jar` | all external references resolve |
| PASS | java | `java.linkage:moto-ims-ext.jar` | all external references resolve |
| PASS | java | `java.linkage:qti-telephony-utils.jar` | all external references resolve |
| PASS | native | `native.needed` | DT_NEEDED of all 14 ported native libraries resolve in the image |
| PASS | overlays | `overlay.package:config_qualified_networks_service_package` | string/config_qualified_networks_service_package -> vendor.qti.iwlan found under /vendor |
| PASS | overlays | `overlay.package:config_wlan_data_service_package` | string/config_wlan_data_service_package -> vendor.qti.iwlan found under /vendor |
| PASS | overlays | `overlay.package:config_wlan_network_service_package` | string/config_wlan_network_service_package -> vendor.qti.iwlan found under /vendor |
| PASS | overlays | `overlay.targets:android.overlay.vantage.device` | all 14 overlaid resources exist in android |
| PASS | overlays | `overlay.targets:android.overlay.vantage.telephony` | all 6 overlaid resources exist in android |
| PASS | overlays | `overlay.targets:com.android.carrierconfig.overlay.vantage` | all 1 overlaid resources exist in com.android.carrierconfig |
| PASS | overlays | `overlay.targets:com.android.phone.overlay.vantage` | all 1 overlaid resources exist in com.android.phone |
| PASS | overlays | `overlay.targets:com.android.settings.overlay.vantage` | all 2 overlaid resources exist in com.android.settings |
| PASS | overlays | `overlay.targets:com.android.systemui.overlay.vantage` | all 1 overlaid resources exist in com.android.systemui |
| PASS | permissions | `privapp.allowlist` | all privileged permissions of 2 priv-apps are allowlisted or granted by signature |
| PASS | placement | `files.content` | 26 verbatim-installed files are byte-identical to stock |
| PASS | placement | `files.present` | all 34 manifest files are present at their stock paths |
| PASS | platform | `platform.api_levels` | system (SDK 37, LLNDK 202604) is not older than the vendor (SDK 36, board API 202504) |
| PASS | selinux | `sepolicy.compile` | secilc compiled the system policy together with the stock vendor policy the way init does (12 CIL files, 1699586 byte policy) |
| PASS | selinux | `sepolicy.inputs` | system provides the platform policy and the 202504 mapping file |
| PASS | selinux | `sepolicy.mapping:moto_app` | moto_app_202504 is populated by the system policy with moto_camera_app (39 references in the stock vendor policy bind to it) |
| PASS | selinux | `sepolicy.mapping:moto_camera_app` | moto_camera_app_202504 is populated by the system policy with moto_camera_app (12 references in the stock vendor policy bind to it) |
| PASS | selinux | `sepolicy.mapping:vendor_qtelephony` | vendor_qtelephony_202504 is populated by the system policy with vendor_qtelephony (23 references in the stock vendor policy bind to it) |
| PASS | selinux | `sepolicy.mapping:vendor_wlc_public_prop` | vendor_wlc_public_prop_202504 is populated by the system policy with vendor_wlc_public_prop (10 references in the stock vendor policy bind to it) |
| PASS | selinux | `sepolicy.seapp_domains` | every system-side seapp_contexts domain is declared |
| PASS | signing | `apk.signature` | app certificates match the manifest intent |
| PASS | telephony | `telephony.ims_binding` | org.codeaurora.ims declares an android.telephony.ims.ImsService guarded by BIND_IMS_SERVICE |
| PASS | vintf | `vintf.radio` | all vendor android.hardware.radio.* AIDL versions are accepted by the framework compatibility matrix level 202504 |

## Details

### WARNING: `java.linkage:ims.apk`

1 references do not resolve against this image (0 more are also unresolved on stock)

- methods Landroid/telephony/ims/ImsExternalCallState;-><init>(Ljava/lang/String;Landroid/net/Uri;Landroid/net/Uri;ZIIZZ)V  (used by Lorg/codeaurora/ims/parser/ImsViceParser;)

### WARNING: `java.linkage:moto-telephony.jar`

1 references do not resolve against this image (0 more are also unresolved on stock)

- fields Landroid/os/Build;->SOC_MANUFACTURER_IS_MTK:Z  (used by Lcom/motorola/android/internal/telephony/MotoExtTelephonyRegistry$DiagnosisEventProxy;, Lcom/motorola/android/telephony/MotoExtTelephonyManager;)

### WARNING: `sepolicy.unmapped`

1 empty versioned attributes belong to labels the vendor's own context files assign; vendor rules on those objects are dead (review each)

- 1541 versioned attributes referenced by vendor/odm rules, 1412 populated, 129 empty
- vendor_hal_atfwd_hwservice_202504: vendor_hwservice_contexts: vendor.qti.hardware.radio.atcmdfwd::IAtCmdFwd

### PASS: `apk.signature`

app certificates match the manifest intent

- image platform certificate sha256=c8a2e9bccf597c2fb6dc66bee293fc13f2fc47ec77bc6b2b0d52c11f51192ab8
- /system_ext/priv-app/ims/ims.apk: re-signed with the image platform certificate
- /product/priv-app/MotCamera5/MotCamera5.apk: keeps OEM certificate be8804a55e9045a5
- /system/app/MotoSignatureApp/MotoSignatureApp.apk: keeps OEM certificate be8804a55e9045a5

### PASS: `image.size`

system image (2866 MiB) fits the dynamic partition group with 10.1 GiB to spare

- system image 3005071360 bytes; group mot_dp_group_a max 31134318592; other stock partitions 17328971776; available for system 13805346816

### PASS: `overlay.targets:android.overlay.vantage.device`

all 14 overlaid resources exist in android

- array/config_network_type_tcp_buffers = () (array) size=21 ["NR_SA_MMWAVE:2097152,6291456,16777216,512000,2097152,8388608", "NR_SA:2097152,6291456,16777216,5120
- array/config_udfps_sensor_props = () (array) size=3 [611, 2066, 91]
- bool/config_dozeAlwaysOnDisplayAvailable = () true
- bool/config_dozeAlwaysOnEnabled = () false
- bool/config_powerDecoupleAutoSuspendModeFromDisplay = () true
- bool/config_powerDecoupleInteractiveModeFromDisplay = () true
- bool/config_suspendWhenScreenOffDueToProximity = () true
- dimen/rounded_corner_radius = () 100.000000px
- dimen/status_bar_height_landscape = () 28.000000dp
- dimen/status_bar_height_portrait = () 130.000000px
- integer/config_mobile_mtu = () 1410
- integer/config_screenBrightnessDoze = () 17
- string/config_dozeComponent = () "com.android.systemui/com.android.systemui.doze.DozeService"
- string/config_mainBuiltInDisplayCutout = () "M -50,0 L 50,0 L 50,130 L -50,130 Z"

### PASS: `overlay.targets:android.overlay.vantage.telephony`

all 6 overlaid resources exist in android

- array/config_telephonyEuiccDeviceCapabilities = () (array) size=4 ["gsm,9", "utran,9", "eutran,18", "nfc,17"]
- array/non_removable_euicc_slots = () (array) size=1 [1]
- bool/config_enhanced_iwlan_handover_check = () false
- string/config_qualified_networks_service_package = () "vendor.qti.iwlan"
- string/config_wlan_data_service_package = () "vendor.qti.iwlan"
- string/config_wlan_network_service_package = () "vendor.qti.iwlan"

### PASS: `overlay.targets:com.android.carrierconfig.overlay.vantage`

all 1 overlaid resources exist in com.android.carrierconfig

- xml/vendor = () (file) res/xml/vendor.xml type=XML

### PASS: `overlay.targets:com.android.phone.overlay.vantage`

all 1 overlaid resources exist in com.android.phone

- string/config_ims_mmtel_package = () "org.codeaurora.ims"

### PASS: `overlay.targets:com.android.settings.overlay.vantage`

all 2 overlaid resources exist in com.android.settings

- bool/config_show_min_refresh_rate_switch = () true
- bool/config_show_peak_refresh_rate_switch = () true

### PASS: `overlay.targets:com.android.systemui.overlay.vantage`

all 1 overlaid resources exist in com.android.systemui

- dimen/rounded_corner_content_padding = () 30.000000px

### PASS: `platform.api_levels`

system (SDK 37, LLNDK 202604) is not older than the vendor (SDK 36, board API 202504)

- system sdk=37 sdk_full=37.0 llndk_api=202604 fingerprint=Android/generic_system/generic:17/CP2A.260605.016/eng.builde:userdebug/test-keys
- vendor sdk=36 board_api=202504 fingerprint=motorola/vantage_g/vantage:16/WWV36HV-16-ST1.1/4548c:user/release-keys

### PASS: `privapp.allowlist`

all privileged permissions of 2 priv-apps are allowlisted or granted by signature

- ro.control_privapp_permissions=enforce
- 1332 permission definitions in image
- org.codeaurora.ims: allowlist=['android.permission.INTERACT_ACROSS_USERS', 'android.permission.MODIFY_PHONE_STATE', 'android.permission.READ_NETWORK_USAGE_HISTORY', 'android.permission.READ_PRECISE_PHONE_STATE', 'android.permission.READ_PRIVILEGED_PHONE_STATE', 'android.permission.SUBSTITUTE_NOTIFICATION_APP_NAME', 'android.permission.WRITE_SECURE_SETTINGS']
- com.motorola.camera5: allowlist=['android.permission.START_ACTIVITIES_FROM_BACKGROUND', 'android.permission.STOP_APP_SWITCHES', 'android.permission.WRITE_SECURE_SETTINGS']

### PASS: `sepolicy.inputs`

system provides the platform policy and the 202504 mapping file

- /work/lineage/out/target/product/generic_arm64/system/etc/selinux/plat_sepolicy.cil
- /work/lineage/out/target/product/generic_arm64/system/etc/selinux/plat_sepolicy_genfs_202504.cil
- /work/lineage/out/target/product/generic_arm64/system/etc/selinux/mapping/202504.cil
- /work/lineage/out/target/product/generic_arm64/system/etc/selinux/mapping/202504.compat.cil
- /work/lineage/out/target/product/generic_arm64/system/system_ext/etc/selinux/system_ext_sepolicy.cil
- /work/lineage/out/target/product/generic_arm64/system/system_ext/etc/selinux/mapping/202504.cil
- /work/lineage/out/target/product/generic_arm64/system/system_ext/etc/selinux/mapping/202504.compat.cil
- /work/lineage/out/target/product/generic_arm64/system/product/etc/selinux/product_sepolicy.cil
- /work/lineage/out/target/product/generic_arm64/system/product/etc/selinux/mapping/202504.cil
- /work/fw/A171WVH.21-16-16/root/vendor/etc/selinux/plat_pub_versioned.cil
- /work/fw/A171WVH.21-16-16/root/vendor/etc/selinux/vendor_sepolicy.cil
- /work/fw/A171WVH.21-16-16/root/odm/etc/selinux/odm_sepolicy.cil

### PASS: `telephony.ims_binding`

org.codeaurora.ims declares an android.telephony.ims.ImsService guarded by BIND_IMS_SERVICE

- /work/lineage/out/target/product/generic_arm64/system/system_ext/priv-app/ims/ims.apk

### PASS: `vintf.radio`

all vendor android.hardware.radio.* AIDL versions are accepted by the framework compatibility matrix level 202504

- android.hardware.radio.config: vendor V[4] framework accepts ['3-4']
- android.hardware.radio.data: vendor V[4] framework accepts ['3-4']
- android.hardware.radio.messaging: vendor V[4] framework accepts ['3-4']
- android.hardware.radio.modem: vendor V[4] framework accepts ['3-4']
- android.hardware.radio.network: vendor V[4] framework accepts ['3-4']
- android.hardware.radio.sap: vendor V[1] framework accepts []
- android.hardware.radio.sim: vendor V[4] framework accepts ['3-4']
- android.hardware.radio.voice: vendor V[4] framework accepts ['3-4']

