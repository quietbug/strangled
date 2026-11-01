#!/bin/bash
set -euo pipefail

DO_JPEG=0
DO_WEBP=0

while (($#)); do
    case "$1" in
        --jpeg) DO_JPEG=1 ;;
        --webp) DO_WEBP=1 ;;
        *) break ;;
    esac
    shift
done

# niceties

if (( ! DO_JPEG && ! DO_WEBP )); then
    echo "Error: specify --jpeg, --webp, or both." >&2
    echo "Usage: $0 [--jpeg] [--webp] <input_dir> <output_dir>" >&2
    exit 1
fi

if [ "$#" -ne 2 ]; then
    echo "Usage: $0 [--jpeg] [--webp] <input_dir> <output_dir>" >&2
    exit 1
fi

INPUT_DIR="$1"
OUTPUT_DIR="$2"

if (( DO_JPEG )) && ! command -v magick >/dev/null 2>&1; then
    echo "Error: ImageMagick is required for --jpeg." >&2
    exit 1
fi

if (( DO_WEBP )) && ! command -v cwebp >/dev/null 2>&1; then
    echo "Error: cwebp is required for --webp." >&2
    exit 1
fi

mkdir -p "$OUTPUT_DIR"

find "$INPUT_DIR" \
    -maxdepth 1 \
    -type f \
    -name '*.png' \
    -print0 |
xargs -0 -r -P"$(nproc)" -I{} sh -c '
    src="$1"
    out_dir="$2"
    do_jpeg="$3"
    do_webp="$4"

    base="$(basename "${src%.png}")"

    if [ "$do_webp" -eq 1 ]; then
        new_webp="$out_dir/$base.webp"

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
    fi

    if [ "$do_jpeg" -eq 1 ]; then
        new_jpeg="$out_dir/$base.jpeg"

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
    fi
' _ {} "$OUTPUT_DIR" "$DO_JPEG" "$DO_WEBP"
