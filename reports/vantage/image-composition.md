# Image composition

Image `/work/lineage/out/target/product/generic_arm64/system.img`

SHA-256 `85fe7a9b6395a1eed5d975803ac23b19f0427779de76fbc3713c924369de0195`

PASS 26 / FAIL 0 / WARNING 1 / UNKNOWN 0

| Status | Check | Finding |
|---|---|---|
| PASS | `layout.single_image` | /system_ext and /product are symlinks into the image; content lives in /system/system_ext (3513 files) and /system/product (532 files) |
| PASS | `layout.skip_mount` | skip_mount.cfg removes the stock fstab entries /product (product), /system_ext (system_ext); no remaining entry mounts on or under /system, /system_ext or /product |
| PASS | `stock.files` | 31 stock files in the image are byte-identical to the manifest hash and to the stock firmware; 2 JNI links point at files inside the image |
| PASS | `stock.resigned` | system_ext/priv-app/ims/ims.apk: all 13 payload entries equal the stock APK (name, size, CRC-32); only the signature differs, signer = the certificate of this image's framework-res.apk |
| PASS | `built.app` | /system/system_ext/app/VantageImsNetwork/VantageImsNetwork.apk: package vantage.telephony.imsnetwork, signed with this image's platform certificate |
| PASS | `built.app` | /system/system_ext/app/VantageRilReady/VantageRilReady.apk: package vantage.telephony.rilready, signed with this image's platform certificate |
| PASS | `built.app` | /system/app/QcRilAm/QcRilAm.apk: package me.phh.qcrilam, signed with this image's platform certificate |
| PASS | `built.ril_ready` | VantageRilReady runs in the system UID, is persistent and carries the OEM hook request for the RIL |
| PASS | `built.qcrilam_patched` | QcRilAm.apk in the image contains all 3 string literals that only the reliability patch adds, and declares the permission it adds (android.permission.MODIFY_AUDIO_ROUTING) |
| PASS | `built.overlay` | VantageDeviceOverlay -> android, static, priority 100: 14 values and 0 XML elements equal the source |
| PASS | `built.overlay` | VantageSettingsOverlay -> com.android.settings, static, priority 100: 2 values and 0 XML elements equal the source |
| PASS | `built.overlay` | VantageSystemUIOverlay -> com.android.systemui, static, priority 100: 1 values and 0 XML elements equal the source |
| PASS | `built.overlay` | VantageCarrierConfigOverlay -> com.android.carrierconfig, static, priority 100: 0 values and 40 XML elements equal the source |
| PASS | `built.overlay` | VantageFrameworkTelephonyOverlay -> android, static, priority 100: 6 values and 0 XML elements equal the source |
| PASS | `built.overlay` | VantageTelephonyOverlay -> com.android.phone, static, priority 100: 1 values and 0 XML elements equal the source |
| PASS | `built.permissions` | 2 privileged-permission allowlists in the image equal the repository files: /system_ext/etc/permissions/privapp-permissions-vantage-telephony.xml, /product/etc/permissions/privapp-permissions-vantage-camera.xml |
| PASS | `built.privapp_partition` | org.codeaurora.ims (/system_ext/priv-app/ims/ims.apk) has its allowlist on the same partition: privapp-permissions-vantage-telephony.xml |
| PASS | `built.privapp_partition` | com.motorola.camera5 (/product/priv-app/MotCamera5/MotCamera5.apk) has its allowlist on the same partition: privapp-permissions-vantage-camera.xml |
| PASS | `built.sepolicy` | system_ext policy in the image declares vendor_qtelephony, moto_camera_app, vendor_wlc_public_prop and carries all 4 seapp_contexts and 2 property_contexts entries |
| PASS | `built.properties` | all 29 properties of properties.mk are in the build.prop of the partition it names |
| PASS | `built.identity` | ro.product.device/name/brand/manufacturer/model will be vantage/vantage_g/motorola/motorola/motorola signature: the stock values |
| PASS | `built.audio_vendor_extension` | audio parameter parser service, loader, stock library and its dependency, service and file labels, policy domain and both properties are in the image |
| PASS | `built.webview_default` | the effective WebView provider list (android.auto_generated_rro_product__) has com.android.webview as its default, which is /system/product/app/webview/webview.apk; services.jar skips providers that are not installed (LineageOS isProviderAvailable), list order com.google.android.webview, com.google.android.webview.beta, com.google.android.webview.dev, com.google.android.webview.canary, com.android.webview |
| PASS | `built.media_profiles` | init copies the vendor's media variant to ro.media.xml_variant.profiles; the stock vendor image has a profile file for each of _canoe_sku1, _canoe_sku2, _canoe_sku3, _canoe_v1, _canoe_v2, _canoe_v3 |
| PASS | `built.vendor_framework_flag` | ro.vendor.qti.va_aosp.support=1 is set, has its own type vantage_vendor_framework_prop, hal_camera_server may read it, and no stock vendor or odm property_contexts names it |
| PASS | `built.sf_timing` | SurfaceFlinger will run in work-duration mode with the vendor's durations (ns: late.sf=10500000, late.app=13666666, early.sf=10500000, early.app=13666666, earlyGl.sf=10500000, earlyGl.app=13666666) and an ADPF CPU hint session; no phase-offset property or configstore HAL that would make it abort |
| WARNING | `overlays.precedence` | 25 values set by our 6 overlays; 47 overlays in the image and the stock /vendor and /odm overlays for the same targets were compared: 0 active overlay(s) with higher precedence set a different value, 11 could at run time, 1 are overridden by ours or inactive, 4 set the same value |

## `layout.skip_mount`

```
patterns: /oem /product /system_ext /oem/* /product/* /system_ext/* /system/*
still mounted from the stock fstab: /boot /data /dtbo /init_boot /metadata /misc /mnt/product/logks /mnt/product/persist /mnt/vendor/persist /odm /recovery /storage/usbotg /system /system_dlkm /vendor /vendor/bt_firmware /vendor/dsp /vendor/firmware_mnt /vendor/fsg /vendor/soccp_firmware /vendor_boot /vendor_dlkm
```

## `stock.resigned`

```
stock signer None
image signer None
```

## `built.qcrilam_patched`

```
audioserver is down
audioserver is up
cannot watch the audioserver state
```

## `built.overlay`

```
array/config_network_type_tcp_buffers = ['NR_SA_MMWAVE:2097152,6291456,16777216,512000,2097152,8388608', 'NR_SA:2097152,6291456,16777216,512000,2097152,8388608', 'NR_NSA_MMWAVE:2097152,6291456,16777216,512000,2097152,8388608', 'NR_NSA:2097152,6291456,16777216,512000,2097152,8388608', 'LTE:2097152,4194304,8388608,262144,524288,4194304', 'LTE_CA:2097152,4194304,16777216,524288,1048576,8388608', 'UMTS:131072,262144,1452032,4096,16384,1220608', 'HSPA:131072,262144,1452032,4096,16384,1220608', 'HSUPA:131072,262144,1452032,4096,16384,1220608', 'HSDPA:131072,262144,1452032,4096,16384,1220608', 'HSPA+:131072,262144,1452032,4096,16384,1220608', 'EDGE:16384,32768,131072,4096,16384,65536', 'GPRS:4096,8192,24576,4096,8192,24576', 'EvDo_0:131072,262144,1048576,4096,16384,524288', 'EvDo_A:131072,262144,1048576,4096,16384,524288', 'EvDo_B:131072,262144,1048576,4096,16384,524288', 'eHRPD:131072,262144,1048576,4096,16384,524288', 'CDMA:4094,87380,262144,4096,16384,262144', '1xRTT:16384,32768,131072,4096,16384,102400', 'iDEN:4094,87380,262144,4096,16384,262144', 'TD_SCDMA:58254,349525,1048576,58254,349525,1048576']
array/config_udfps_sensor_props = ['611', '2066', '91']
bool/config_dozeAlwaysOnDisplayAvailable = true
bool/config_dozeAlwaysOnEnabled = false
bool/config_powerDecoupleAutoSuspendModeFromDisplay = true
bool/config_powerDecoupleInteractiveModeFromDisplay = true
bool/config_suspendWhenScreenOffDueToProximity = true
dimen/rounded_corner_radius = 100px
dimen/status_bar_height_landscape = 28dp
dimen/status_bar_height_portrait = 130px
integer/config_mobile_mtu = 1410
integer/config_screenBrightnessDoze = 17
string/config_dozeComponent = com.android.systemui/com.android.systemui.doze.DozeService
string/config_mainBuiltInDisplayCutout = M -50,0 L 50,0 L 50,130 L -50,130 Z
```

## `built.overlay`

```
bool/config_show_min_refresh_rate_switch = true
bool/config_show_peak_refresh_rate_switch = true
```

## `built.overlay`

```
dimen/rounded_corner_content_padding = 30px
```

## `built.overlay`

```
array/config_telephonyEuiccDeviceCapabilities = ['gsm,9', 'utran,9', 'eutran,18', 'nfc,17']
array/non_removable_euicc_slots = ['1']
bool/config_enhanced_iwlan_handover_check = false
string/config_qualified_networks_service_package = vendor.qti.iwlan
string/config_wlan_data_service_package = vendor.qti.iwlan
string/config_wlan_network_service_package = vendor.qti.iwlan
```

## `built.overlay`

```
string/config_ims_mmtel_package = org.codeaurora.ims
```

## `overlays.precedence`

```
android dimen/status_bar_height_portrait: also set by com.android.internal.display.cutout.emulation.corner (image /product, mutable, priority 1, property gate on) = 48.000000dp  [mutable: applies only if something enables it at run time]
android string/config_mainBuiltInDisplayCutout: also set by com.android.internal.display.cutout.emulation.corner (image /product, mutable, priority 1, property gate on) = "M 0,0 L -48, 0 C -48,48 -48,48 0,48 Z @dp @right"  [mutable: applies only if something enables it at run time]
android dimen/status_bar_height_portrait: also set by com.android.internal.display.cutout.emulation.double (image /product, mutable, priority 1, property gate on) = 48.000000dp  [mutable: applies only if something enables it at run time]
android string/config_mainBuiltInDisplayCutout: also set by com.android.internal.display.cutout.emulation.double (image /product, mutable, priority 1, property gate on) = "M 0,0 L -72, 0 L -69.9940446283, 20.0595537175 C -69.158213  [mutable: applies only if something enables it at run time]
android dimen/status_bar_height_portrait: also set by com.android.internal.display.cutout.emulation.hole (image /product, mutable, priority 1, property gate on) = 136.000000px  [mutable: applies only if something enables it at run time]
android string/config_mainBuiltInDisplayCutout: also set by com.android.internal.display.cutout.emulation.hole (image /product, mutable, priority 1, property gate on) = "M 128,83 A 44,44 0 0 1 84,127 44,44 0 0 1 40,83 44,44 0 0 1  [mutable: applies only if something enables it at run time]
android dimen/status_bar_height_portrait: also set by com.android.internal.display.cutout.emulation.tall (image /product, mutable, priority 1, property gate on) = 48.000000dp  [mutable: applies only if something enables it at run time]
android string/config_mainBuiltInDisplayCutout: also set by com.android.internal.display.cutout.emulation.tall (image /product, mutable, priority 1, property gate on) = "M 0,0 L -48, 0 L -44.3940446283, 36.0595537175 C -43.558213  [mutable: applies only if something enables it at run time]
android dimen/status_bar_height_landscape: also set by com.android.internal.display.cutout.emulation.waterfall (image /product, mutable, priority 1, property gate on) = 48.000000dp  [mutable: applies only if something enables it at run time]
android dimen/status_bar_height_portrait: also set by com.android.internal.display.cutout.emulation.waterfall (image /product, mutable, priority 1, property gate on) = 28.000000dp  [mutable: applies only if something enables it at run time]
android string/config_mainBuiltInDisplayCutout: also set by com.android.internal.display.cutout.emulation.waterfall (image /product, mutable, priority 1, property gate on) = ""  [mutable: applies only if something enables it at run time]
android dimen/rounded_corner_radius: also set by com.motorola.android.overlay.vendor.common (stock /vendor, static, priority 3, property gate on) = () 24.000000dp  [lower precedence than ours]
android dimen/status_bar_height_landscape: also set by com.android.internal.display.cutout.emulation.corner (image /product, mutable, priority 1, property gate on) = 28.000000dp
android dimen/status_bar_height_landscape: also set by com.android.internal.display.cutout.emulation.double (image /product, mutable, priority 1, property gate on) = 28.000000dp
android dimen/status_bar_height_landscape: also set by com.android.internal.display.cutout.emulation.hole (image /product, mutable, priority 1, property gate on) = 28.000000dp
android dimen/status_bar_height_landscape: also set by com.android.internal.display.cutout.emulation.tall (image /product, mutable, priority 1, property gate on) = 28.000000dp
```
