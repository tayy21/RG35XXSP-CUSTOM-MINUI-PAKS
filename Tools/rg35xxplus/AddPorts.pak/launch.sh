#!/bin/sh

PORTS_DIR="/mnt/sdcard/Roms/PORTS"
TOOLS_DIR="/mnt/sdcard/Tools/rg35xxplus"

# Create the tools folder if it doesn't exist
mkdir -p "$TOOLS_DIR"

# Loop over all .sh files in PORTS
for shfile in "$PORTS_DIR"/*.sh; do
  # Skip loop if no .sh files exist
  [ ! -e "$shfile" ] && echo "No .sh files found in $PORTS_DIR" && exit 1

  # Get the base name without extension
  base=$(basename "$shfile" .sh)

  # Target .pak folder
  target_folder="$TOOLS_DIR/${base}.pak"

  # If the folder already exists, skip it
  if [ -d "$target_folder" ]; then
    echo "Folder $target_folder already exists. Skipping."
    continue
  fi

  # Create the .pak folder
  mkdir -p "$target_folder"

  # Create launch.sh inside it
  cat > "$target_folder/launch.sh" << EOF
#!/bin/sh

PORT_NAME="$base"

cd /mnt/sdcard/Roms/PORTS

chmod +x "./\$PORT_NAME.sh"
exec ./"\$PORT_NAME.sh"
EOF

  # Make launch.sh executable
  chmod +x "$target_folder/launch.sh"

  echo "Created $target_folder/launch.sh for $base"
done
