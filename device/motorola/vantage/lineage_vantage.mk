# Motorola Signature (codename vantage, SM8845 "canoe")
#
# LineageOS 24.0 generic system image (lineage_gsi_arm64: AOSP gsi_arm64 + Lineage's phone
# configuration) plus the vantage integration layer and microG. PRODUCT_DEVICE stays
# generic_arm64, the GSI board: the result is a system image in GSI layout (system_ext and
# product inside, stock /system_ext and /product left unmounted by skip_mount.cfg) that runs on
# the unmodified stock Android 17 vendor.

# The integration layer is inherited first on purpose: for PRODUCT_COPY_FILES the first entry
# for a destination wins.
$(call inherit-product, vendor/motorola/vantage/vantage-vendor.mk)
$(call inherit-product, vendor/motorola/vantage/vantage.mk)

$(call inherit-product, vendor/lineage/build/target/product/lineage_gsi_arm64.mk)

# LineageOS's gsi_release.mk sets this only for products named lineage_gsi_*. It disables AOSP's
# Soong-defined aosp_system_image, which lists AOSP apps LineageOS does not ship (Calendar, ...)
# and otherwise stops the Soong analysis with "depends on undefined module". It has no other use.
BUILDING_LINEAGE_GSI := true

PRODUCT_NAME := lineage_vantage

# What the phone calls itself on stock. The stock vendor and Motorola Camera read these
# (vendor/motorola/vantage/properties.mk, section "Device identity").
PRODUCT_BRAND := motorola
PRODUCT_MANUFACTURER := motorola
PRODUCT_MODEL := motorola signature

PRODUCT_DEVICE := generic_arm64
