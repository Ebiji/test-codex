#!/usr/bin/env bash
# SVG を生成して PNG に書き出す（パッケージは 350dpi 相当）
set -euo pipefail
cd "$(dirname "$0")/.."
python3 tools/build.py
mkdir -p exports/patterns exports/flavors
args=(
  design/package_grape.svg exports/package_grape.png 1.4
  design/logo.svg exports/logo.png 2
  design/logo_mono.svg exports/logo_mono.png 2
  design/character_pacchin_grape.svg exports/character_pacchin_grape.png 2
  design/character_shuwarin.svg exports/character_shuwarin.png 2
  design/character_sheet.svg exports/character_sheet.png 1
  design/proposal_board.svg exports/proposal_board.png 1
)
for i in 1 2 3 4 5 6; do args+=(design/patterns/package_grape_$i.svg exports/patterns/package_grape_$i.png 1); done
for f in grape soda cola melon lemon; do args+=(design/flavors/package_$f.svg exports/flavors/package_$f.png 1); done
node tools/render.mjs "${args[@]}"
