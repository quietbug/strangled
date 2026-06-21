#!/bin/bash
set -euo pipefail

if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <input_dir> <output_dir>"
    exit 1
fi

INPUT_DIR="$1"
OUTPUT_DIR="$2"

mkdir -p "$OUTPUT_DIR"

find "$INPUT_DIR" \
    -maxdepth 1 \
    -type f \
    -name '*.png' \
    -print0 | \
xargs -0 -P"$(nproc)" -I{} sh -c '

    src="$1"

    out_dir="$2"

    base="$(basename "${src%.png}")"

    new_webp="$out_dir/$base.webp"
    new_jpeg="$out_dir/$base.jpeg"

	# Convert to WEBP

    if [ ! -f "$new_webp" ] || [ "$src" -nt "$new_webp" ]; then

        echo "Converting: $src -> $new_webp"

        cwebp "$src" \
            -o "$new_webp" \
            -q 90 \
            -m 6 \
            -af \
            -sharpness 3 \
            -sns 25 \
            -noalpha \
            -sharp_yuv
    else

        echo "Skipping webp conversion: $src"

	fi

	# Convert to JPEG

    if [ ! -f "$new_jpeg" ] || [ "$src" -nt "$new_jpeg" ]; then

        echo "Converting: $src -> $new_jpeg"

		magick "$src" \
			-strip \
			-quality 95 \
			-sampling-factor 4:4:4 \
			-define jpeg:dct-method=float \
			-define jpeg:optimize-coding=true \
			"$new_jpeg"

    else

        echo "Skipping jpeg conversion: $src"

    fi

' _ {} "$OUTPUT_DIR"
