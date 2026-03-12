#!/bin/bash
# M.I.T.E.L. USB Check - Event-driven (no polling)
# Called by udev rules when USB device is inserted

DEVICE=$1
VENDOR=$2
PRODUCT=$3

# Log the event
echo "$(date): USB Event - Device: $DEVICE, Vendor: $VENDOR, Product: $PRODUCT" >> /var/log/mitel-events.log

# Quick threat assessment (no heavy processing)
case "$VENDOR:$PRODUCT" in
    "0781:5580")
        # Rubber ducky detected
        echo "$(date): THREAT - Rubber Ducky detected: $DEVICE" >> /var/log/mitel-threats.log
        # Immediate response - block device
        echo 0 > /sys/bus/usb/devices/$DEVICE/authorized 2>/dev/null
        # Send alert (lightweight)
        echo "ALERT: Rubber Ducky blocked - Device: $DEVICE" | logger -t mitel
        ;;
    "0781:5567")
        # Trusted SanDisk drive
        echo "$(date): TRUSTED - SanDisk drive: $DEVICE" >> /var/log/mitel-events.log
        ;;
    *)
        # Unknown device - quarantine by default
        echo "$(date): QUARANTINE - Unknown device: $VENDOR:$PRODUCT" >> /var/log/mitel-threats.log
        # Block until verified
        echo 0 > /sys/bus/usb/devices/$DEVICE/authorized 2>/dev/null
        echo "ALERT: Unknown USB device quarantined - $VENDOR:$PRODUCT" | logger -t mitel
        ;;
esac

# Exit immediately (no polling)
exit 0
