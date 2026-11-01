#!/usr/bin/env python3
import argparse

from html import escape
from pathlib import Path
from string import Template
from concurrent.futures import ThreadPoolExecutor

IMAGE_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".gif",
    ".webp", ".bmp", ".tiff", ".svg"
}

PAGE_TEMPLATE = Template("""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>$title</title>
<style>
$stylesheet_code
/* palette overrides */
$page_palette_css
</style>
</head>
<body>

<div class="bg" style="background-image: url('pages/$image_name')"></div>

<main>

<label>
<input type="checkbox" id="zoom">
<div class="viewport" id="viewport" tabindex="0">
  <img src="pages/$image_name" alt="$image_name">
</div>
</label>

<div class="help" id="help">
  <div class="help-inner">
    <a href="../index.html">Back to index</a>
    <div class="title">one handed mode ;)</div>
    <div><b>f</b> toggle zoom</div>
    <div><b>a</b> prev page</div>
    <div><b>d</b> next page</div>
    <div><b>w</b> pan (up)</div>
    <div><b>s</b> pan (down)</div>
    <div class="title">for hackers:</div>
    <div><b>h j k l</b> also pan</div>
  </div>
</div>

<nav>

$prev_link

<details>
<summary>[$current_page/$total_images pages]</summary>
<div class="pages">
$dropdown_items
</div>
</details>

$next_link

</nav>

</main>

<script>

(function () {

    const zoom = document.getElementById("zoom");
    const viewport = document.getElementById("viewport");

    const SCROLL_STEP = 80;

    const prev = $has_prev;
    const next = $has_next;

    function goPrev() {
        if (prev) {
            location.href = "page_$prev_idx.html";
        }
    }

    function goNext() {
        if (next) {
            location.href = "page_$next_idx.html";
        } else {
            location.href = "../index.html";
        }
    }

    function syncZoomFocus() {
        if (zoom.checked) {
            viewport.focus({ preventScroll: true });
        }
    }

    zoom.addEventListener("change", syncZoomFocus);

    viewport.addEventListener("click", () => {
        if (zoom.checked) {
            viewport.focus({ preventScroll: true });
        }
    });

    document.addEventListener("keydown", function (e) {

        const k = e.key.toLowerCase();

        if (k === "f") {
            e.preventDefault();
            zoom.checked = !zoom.checked;
            syncZoomFocus();
        }

        else if (k === "a") {
            e.preventDefault();
            goPrev();
        }

        else if (k === "d") {
            e.preventDefault();
            goNext();
        }

        else if (k === "h") {
            e.preventDefault();
            viewport.scrollBy(-SCROLL_STEP, 0);
        }

        else if (k === "j" || k === "s") {
            e.preventDefault();
            viewport.scrollBy(0, SCROLL_STEP);
        }

        else if (k === "k" || k === "w") {
            e.preventDefault();
            viewport.scrollBy(0, -SCROLL_STEP);
        }

        else if (k === "l") {
            e.preventDefault();
            viewport.scrollBy(SCROLL_STEP, 0);
        }

    });

})();

</script>

</body>
</html>
""")


def main():

    parser = argparse.ArgumentParser(
        description="Generate static HTML image reader pages."
    )

    parser.add_argument(
        "--style",
        required=True,
        type=Path,
        help="Path to stylesheet file"
    )

    parser.add_argument(
        "--pages",
        required=True,
        type=Path,
        help="Directory containing image pages"
    )

    parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Output directory"
    )

    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Number of worker threads (default: 1)"
    )

    args = parser.parse_args()

    style_src = args.style.resolve()
    pages_dir = args.pages.resolve()
    output_dir = args.output.resolve()

    if not pages_dir.is_dir():
        raise SystemExit(f"Missing input directory: {pages_dir}")

    if not style_src.is_file():
        raise SystemExit(f"Missing stylesheet: {style_src}")

    with open(style_src, "r", encoding="utf-8") as stylesheet_file:
        stylesheet = stylesheet_file.read()

    images = sorted(
            [
                entry
                for entry in pages_dir.iterdir()
                if entry.is_file()
                and entry.suffix.lower() in IMAGE_EXTENSIONS
            ],
            key=lambda p: p.name.lower(),
        )

    if not images:
        raise SystemExit(f"No images found in {pages_dir}")

    output_dir.mkdir(parents=True, exist_ok=True)

    total = len(images)

    print(f"Found {total} image(s).")
    print(f"Writing pages to: {output_dir}")

    def generate_page(idx, img_path):
        print(f"Making page {idx}: {img_path} ...")

        dropdown_items = []

        for i, _ in enumerate(images):

            marker = ">" if i == idx else " "

            dropdown_items.append(
                f'<a href="page_{i}.html">{marker} Page {i}</a>'
            )

        prev_link = (
            f'<a href="page_{idx - 1}.html">&lt; Prev</a>'
            if idx > 0
            else "<span>&lt; Prev</span>"
        )

        next_link = (
            f'<a href="page_{idx + 1}.html">Next &gt;</a>'
            if idx < total - 1
            else '<a href="../index.html">Return &gt;</a>'
        )

        from PIL import Image
        from material_color_utilities import theme_from_image, Variant

        with Image.open(img_path) as image:
            theme = theme_from_image(
                image,
                contrast=0.5,
                variant=Variant.CONTENT,
            )

        scheme = theme.schemes.dark

        def build_page_palette_css(scheme):
            variables = {
                "--color-bg": scheme.surface,
                "--color-fg": scheme.on_surface,
                "--color-accent": scheme.primary,
                "--color-accent-muted": scheme.secondary,
                "--color-highlight": scheme.tertiary,
                "--color-border": scheme.outline,
                "--color-help-link": scheme.primary,
                "--color-nav-bg": scheme.surface_container,
                "--color-help-bg": scheme.surface_container_high,
                "--color-help-border": scheme.outline,
                "--color-accent-fg": scheme.on_primary,
            }

            declarations = "\n".join(
                f"    {name}: {value};"
                for name, value in variables.items()
            )

            return f":root {{\n{declarations}\n}}"

        page_html = PAGE_TEMPLATE.substitute(
            stylesheet_code=stylesheet,
            page_palette_css=build_page_palette_css(scheme),

            title=escape(f"Image {idx}: {img_path.name}"),
            dropdown_items="\n".join(dropdown_items),
            image_name=escape(img_path.name),

            prev_link=prev_link,
            next_link=next_link,
            current_page=idx,
            total_images=total - 1, # we start from 0

            has_prev="true" if idx > 0 else "false",
            has_next="true" if idx < total - 1 else "false",

            prev_idx=idx - 1 if idx > 0 else 0,
            next_idx=idx + 1 if idx < total - 1 else idx,
        )

        output_file = output_dir / f"page_{idx}.html"

        output_file.write_text(
            page_html,
            encoding="utf-8"
        )

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        list(executor.map(generate_page, range(total), images))


if __name__ == "__main__":
    main()
