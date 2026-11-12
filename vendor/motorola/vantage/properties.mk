# Properties the stock system-side partitions set and something that runs in this ROM reads.
#
# Stock keeps them in /system, /system_ext and /product build.prop. A generic system image mounts
# none of those, so the stock vendor side (RIL, data, camera, init scripts) and the framework
# would run without them. Each entry was selected on the Android 16 port from the running guest
# (first DSU boot, 2026-10-10): missing there, set by stock, and read by a stock /vendor or /odm
# file or by a file of this image. Re-checked against stock Android 17 (A171WVH.21-16-16) with
# scripts/prop_users.py on 2026-11-11: every value is unchanged there (FIRMWARE_A17.md section 4).
# The partition is the one stock uses, which keeps the precedence the same (product overrides
# vendor/odm, system is overridden by them). Exception: the SurfaceFlinger section near the end
# holds two values of this ROM's own, not stock's (reason there).

# --- Radio -------------------------------------------------------------------------------
# Default network mode 26 = NR/LTE/GSM/WCDMA for both slots. Without it the framework falls
# back to mode 0 and tells the modem to use 2G/3G only: no service on an LTE/NR-only network
# (seen on the first boot: filteredRaf = UMTS|GSM, registration state "searching").
PRODUCT_PRODUCT_PROPERTIES += \
    ro.telephony.default_network=26,26

# telephony.lteOnCdmaDevice: framework and TeleService. persist.vendor.data.mode: the vendor's
# init.class_main.sh starts its data daemons (dataqti, dataadpl) only for "concurrent".
PRODUCT_SYSTEM_PROPERTIES += \
    telephony.lteOnCdmaDevice=1 \
    persist.vendor.data.mode=concurrent

# Read by the stock RIL database (qcrilNr.db), the RIL, rmt_storage, cnd and libcne.
PRODUCT_PRODUCT_PROPERTIES += \
    persist.vendor.radio.force_gba_over_isim_app=1 \
    persist.vendor.cne.feature=1 \
    persist.vendor.cne.logging.qxdm=3974 \
    ro.vendor.radio.imei.sv=1 \
    ro.mot.build.customerid=global

PRODUCT_SYSTEM_EXT_PROPERTIES += \
    persist.vendor.dpm.feature=11

# Stock values for the same vendor radio/IMS stack; no reader was found by name in the vendor
# files (the names may be composed at run time), kept so the vendor sees what it sees on stock.
PRODUCT_SYSTEM_PROPERTIES += \
    ro.vendor.use_data_netmgrd=true

PRODUCT_PRODUCT_PROPERTIES += \
    persist.vendor.radio.jbims=1 \
    persist.vendor.rcs.singlereg.feature=1 \
    persist.vendor.vt.supported=1 \
    persist.vendor.data.iwlan.enable=true \
    persist.vendor.sys.cnd.iwlan=1

# Video-call timing read by the ported lib-imsvt.so and the vendor's lib-imsvtcore.so.
PRODUCT_PRODUCT_PROPERTIES += \
    persist.vendor.ims.cam_sensor_delay=20 \
    persist.vendor.ims.display_delay=40 \
    persist.vendor.ims.playout_delay=50

# --- Device identity -----------------------------------------------------------------------
# Stock: ro.product.device=vantage, ro.product.name=vantage_g, model "motorola signature".
# The vendor derives ro.vendor.product.device/name from them (init.oem.hw.sh) and its RIL,
# rmt_storage and camera algorithm libraries read them; Motorola Camera selects its device
# configuration by ro.product.device and refused to start as "tdgsi" on the first boot.
# Brand, manufacturer and model come from PRODUCT_BRAND/MANUFACTURER/MODEL in vantage_td.mk;
# device and name cannot follow PRODUCT_DEVICE/PRODUCT_NAME (they name the build target), so
# the base properties are set here and init then skips deriving them.
PRODUCT_PRODUCT_PROPERTIES += \
    ro.product.device=vantage \
    ro.product.name=vantage_g \
    ro.build.product=vantage

# Read by vendor init scripts, the face and secure-element HAL start conditions, and the camera.
PRODUCT_SYSTEM_PROPERTIES += \
    ro.product.is_production=true

# --- Qualcomm "vendor-enhanced framework" flag ---------------------------------------------------
# libqti_vndfwk_detect answers isRunningWithVendorEnhancedFramework() from this property (and
# ro.vendor.qti.va_odm.support, which the vendor sets itself). Without it the camera HAL
# loads its reduced GSI camera configuration: 2 cameras instead of 6, no logical
# multi-camera, and Motorola Camera reports "Multiple cameras aren't working". Proven on
# the device: setting it and restarting the camera provider brought all 6 devices back
# (SECOND_BOOT_REPORT.md section 5), and so did a boot with it set (THIRD_BOOT_REPORT.md).
#
# The value is the stock one, but only the camera HAL may read it: the property has its own
# SELinux type (sepolicy/private/property.te). The audio and Bluetooth HALs, CNE, the IMS and
# RTP daemons, qcc-vendor and the GNSS XTRA daemon read the flag as "Qualcomm's system-side
# services are present". They are not, and in the boot where everyone saw the flag the XTRA
# daemon gave up waiting for one of them and stayed down.
PRODUCT_SYSTEM_PROPERTIES += \
    ro.vendor.qti.va_aosp.support=1

# --- Camera, media -----------------------------------------------------------------------
PRODUCT_SYSTEM_EXT_PROPERTIES += \
    persist.vendor.camera.expose.aux=1

PRODUCT_SYSTEM_PROPERTIES += \
    ro.media.recorder-max-base-layer-fps=60

# persist.sys.dolby.upmapping.filter.notify (A16 stock: true) is not set by stock Android 17 and
# was dropped.
PRODUCT_PRODUCT_PROPERTIES += \
    persist.sys.dolby.upmapping.filter.enable=false

# --- SurfaceFlinger frame timing (r3; not stock values) ---------------------------------------
# Measured on r2 (2026-11-11, reports/ui-smoothness-r2.md): with the quick settings shade or the
# launcher's app drawer blurred, every layer is composed on the GPU and SurfaceFlinger needs about
# 10.5 ms per frame while the CPU stays at its lowest clocks; at 120 Hz that misses every other
# vsync (about 40 % janky frames; with window blurs off, 1-2 %). Stock does not have this problem
# because its system runs Qualcomm's SurfaceFlinger and boost libraries, which this ROM does not.
#
# use_phase_offsets_as_durations=1: the vendor already sets debug.sf.{late,early,earlyGl}.{sf,app}
# .duration (SurfaceFlinger 10.5 ms, apps 13.67 ms) but also =0, so AOSP's SurfaceFlinger ignores
# those durations and gives itself vsync + 1 ms to the next vsync (7.3 ms at 120 Hz). With =1 it
# uses the vendor's durations. Costs about one frame of extra latency. SurfaceFlinger aborts at
# start in this mode if any phase-offset property is set; none is, on this vendor
# (check_image_composition.py, built.sf_timing).
# enable_adpf_cpu_hint=true: SurfaceFlinger reports its frame times to the power HAL (ADPF hint
# session), which may raise the CPU clocks for its threads when it runs late. The vendor's power
# HAL supports hint sessions, and its SELinux policy lets it set scheduling of surfaceflinger.
#
# Product, because /product/etc/build.prop is read after /vendor/build.prop and so overrides the
# vendor's use_phase_offsets_as_durations=0.
PRODUCT_PRODUCT_PROPERTIES += \
    debug.sf.use_phase_offsets_as_durations=1 \
    debug.sf.enable_adpf_cpu_hint=true

# --- Call audio: vendor parameters for the AIDL audio HAL (audio/vendorext/README.md) --------
PRODUCT_SYSTEM_EXT_PROPERTIES += \
    ro.audio.ihaladaptervendorextension_enabled=true \
    ro.audio.ihaladaptervendorextension_libname=libvantage_audiohalvendorext.so
