# Motorola Signature (vantage) integration layer: hand-maintained part.
# The list of stock prebuilts lives in the generated vantage-vendor.mk.

# System-side SELinux types the stock vendor policy (version 202504) is written against.
SYSTEM_EXT_PUBLIC_SEPOLICY_DIRS += vendor/motorola/vantage/sepolicy/public
SYSTEM_EXT_PRIVATE_SEPOLICY_DIRS += vendor/motorola/vantage/sepolicy/private

# Telephony: bind the stock Qualcomm IMS service and restate framework values that stock
# ships in /product overlays (stock /product is not mounted under a generic system image).
PRODUCT_PACKAGES += \
    VantageTelephonyOverlay \
    VantageFrameworkTelephonyOverlay \
    VantageCarrierConfigOverlay

# APN database: the stock Android 17 list (pinned in proprietary-files.txt, installed by the
# generated module apns-conf.xml) instead of LineageOS's generated one, which lacks the carrier's
# initial-attach and tethering APNs. patches/vendor/apn adds this switch to LineageOS's module.
$(call soong_config_set_bool,lineage_apn,use_device_apns,true)

# Telephony: hold the IMS network request. On stock the vendor CNE app does this with a
# permission it only has under Motorola's platform key (telephony/ims-network/README.md).
PRODUCT_PACKAGES += \
    VantageImsNetwork

# Call audio: TrebleDroid's RIL audio bridge (packages/apps/QcRilAm, added by the local manifest
# of scripts/sync-source.sh and patched by patches/packages/apps/QcRilAm). It answers the
# vendor RIL's IQcRilAudio HAL, which stock's QtiTelephonyService answers (TELEPHONY_PORT.md).
# On Android 16 it came with the TrebleDroid product; LineageOS does not have it.
PRODUCT_PACKAGES += \
    QcRilAm

# Telephony: tell the Qualcomm RIL that Android telephony is ready. Until then it keeps incoming
# SMS to itself; on stock Qualcomm's telephony service sends this (telephony/ril-ready/README.md).
PRODUCT_PACKAGES += \
    VantageRilReady

# Stock system-side properties that the vendor side and the framework read (properties.mk).
$(call inherit-product, vendor/motorola/vantage/properties.mk)

# Hardware facts stock keeps in /product overlays: display cutout and status bar height,
# under-display fingerprint position, ambient display, power and mobile-data tuning, corner
# radius (overlays/VantageDeviceOverlay), status bar padding from the rounded corners
# (overlays/VantageSystemUIOverlay); values copied from stock A171WVH.21-16-16.
PRODUCT_PACKAGES += \
    VantageDeviceOverlay \
    VantageSystemUIOverlay

# Settings > Display: LineageOS's maximum/minimum refresh rate lists (165 Hz panel mode).
PRODUCT_PACKAGES += \
    VantageSettingsOverlay

# Call audio: AOSP's audio parameter parser service hosts the stock implementation of
# IHalAdapterVendorExtension through a small loader library (audio/vendorext/README.md).
PRODUCT_PACKAGES += \
    android.hardware.audio.parameter_parser.example_service \
    libvantage_audiohalvendorext

# Camcorder profiles: point AOSP's libmedia at the profile file the stock libmedia reads
# (init/init.vantage.media.rc).
PRODUCT_PACKAGES += \
    init.vantage.media.rc

# Privileged-permission allowlists (identical to the stock grants).
PRODUCT_COPY_FILES += \
    vendor/motorola/vantage/telephony/permissions/privapp-permissions-vantage-telephony.xml:$(TARGET_COPY_OUT_SYSTEM_EXT)/etc/permissions/privapp-permissions-vantage-telephony.xml \
    vendor/motorola/vantage/camera/permissions/privapp-permissions-vantage-camera.xml:$(TARGET_COPY_OUT_PRODUCT)/etc/permissions/privapp-permissions-vantage-camera.xml

# microG, the open-source Google Play services implementation (owner's request, 2026-11-11):
# official release APKs signed by microG, which LineageOS lets claim Google's signature on a
# debuggable build (microg/README.md).
PRODUCT_PACKAGES += \
    GmsCore \
    MicrogCompanion
