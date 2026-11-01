#!/bin/zsh

alias -g neocities="$HOME/.local/share/gem/ruby/3.4.0/bin/neocities"
export NEOCITIES_API_KEY="$(pass neocities.org/controlheart.api)"

cd "${0:A:h}/../deploy" || exit 1
neocities push -e .gitkeep .
