#!/bin/zsh
# main script
set -e
# set pwd to script location
cd "${0:A:h}" 

# generate.py uses external libs
source venv/bin/activate

cd ..
mkdir -p deploy
touch deploy/.gitkeep

# index page
rsync -avx home/* deploy/

for src in sources/*_PAGE_SOURCE(/)
do
	dst="deploy/${${src:t}/_PAGE_SOURCE/}"
	mkdir -p $dst/pages
	scripts/compress.sh --webp "$src" "$dst/pages" || exit 1
	scripts/generate.py --workers $(nproc) --style scripts/viewer_page.css --pages "$dst/pages" --output "$dst" || exit 1
done
