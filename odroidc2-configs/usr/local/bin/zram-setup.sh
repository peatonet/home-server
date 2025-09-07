#!/bin/bash
modprobe zram
echo $((128 * 1024 * 1024)) | sudo tee /sys/block/zram0/disksize
mkswap /dev/zram0
swapon -p 100 /dev/zram0
