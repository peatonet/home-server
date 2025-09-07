#!/bin/bash

SWAPFILE="/swapfile"
SWAPSIZE="512M"
OLDSWAP="/var/swap"

# --- REMOVE /var/swap if it exists ---
if swapon --show | grep -q "$OLDSWAP"; then
  echo "Disabling existing swap at $OLDSWAP..."
  sudo swapoff "$OLDSWAP"
fi

if [ -f "$OLDSWAP" ]; then
  echo "Removing old swapfile at $OLDSWAP..."
  sudo rm -f "$OLDSWAP"
fi

if grep -q "$OLDSWAP" /etc/fstab; then
  echo "Removing $OLDSWAP entry from /etc/fstab..."
  sudo sed -i "\|$OLDSWAP|d" /etc/fstab
fi

# --- CREATE NEW SWAPFILE IF NEEDED ---
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

# --- ENABLE SWAPFILE NOW ---
echo "Enabling swapfile..."
sudo swapon $SWAPFILE

# --- ADD TO FSTAB IF NOT ALREADY THERE ---
if grep -q "^$SWAPFILE" /etc/fstab; then
  echo "Swapfile entry already exists in /etc/fstab."
else
  echo "Adding swapfile entry to /etc/fstab..."
  echo "$SWAPFILE none swap sw 0 0" | sudo tee -a /etc/fstab
fi

# --- SHOW SWAP STATUS ---
echo "Current swap status:"
swapon --show
free -h

echo "Swap configuration complete."