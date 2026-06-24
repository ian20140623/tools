#!/usr/bin/env bash
# 編譯 ocr_clip。產物 = tools/ocr-clip/ocr_clip（gitignore，不進版控）。
# 換機 / git pull 後跑一次即可。
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
swiftc -O "$DIR/scripts/ocr_clip.swift" -o "$DIR/ocr_clip"
echo "built: $DIR/ocr_clip"
