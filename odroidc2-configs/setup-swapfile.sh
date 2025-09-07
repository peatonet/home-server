#!/bin/bash

SWAPFILE="/swapfile"
SWAPSIZE="512M"

# Check if swapfile already exists
if [ -f "$SWAPFILE" ]; then
  echo "Swapfile $SWAPFILE already exists."
else
  echo "Creating swapfile of size $SWAPSIZE at $SWAPFILE..."
  sudo fallocate -l $SWAPSIZE $SWAPFILE || {
    echo "fallocate failed, trying dd..."
    sudo dd if=/dev/zero of=$SWAPFILE bs=1M count=512 status=progress
  }
  sudo chmod 600 $SWAPFILE
  sudo mkswap $SWAPFILE
  echo "Swapfile created."
fi

# Enable swapfile now
echo "Enabling swapfile..."
sudo swapon $SWAPFILE

# Check if entry already in /etc/fstab
if grep -q "^$SWAPFILE" /etc/fstab; then
  echo "Swapfile entry already exists in /etc/fstab."
else
  echo "Adding swapfile entry to /etc/fstab..."
  echo "$SWAPFILE none swap sw 0 0" | sudo tee -a /etc/fstab
fi

# Show swap status
echo "Current swap status:"
swapon --show
free -h

echo "Swap configuration complete."
