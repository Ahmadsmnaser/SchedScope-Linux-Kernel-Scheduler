#!/usr/bin/env bash
set -euo pipefail

ROOTFS_DIR="${1:-rootfs}"
OUTPUT="${2:-rootfs.cpio.gz}"

if [[ ! -d "$ROOTFS_DIR" ]]; then
  echo "rootfs directory not found: $ROOTFS_DIR" >&2
  exit 1
fi

(
  cd "$ROOTFS_DIR"
  find . -print0 | cpio --null -ov --format=newc | gzip -9
) > "$OUTPUT"

echo "Created $OUTPUT from $ROOTFS_DIR"
