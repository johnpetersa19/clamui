#!/bin/bash
# Generate/update the POT (Portable Object Template) file for ClamUI translations.
#
# Usage:
#   ./scripts/update-pot.sh
#
# Prerequisites:
#   sudo apt install gettext
#
# This script:
#   1. Reads po/POTFILES.in for the list of source files
#   2. Runs xgettext to extract translatable strings
#   3. Outputs po/clamui.pot

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

POTFILES="po/POTFILES.in"
OUTPUT="po/clamui.pot"

if [ ! -f "$POTFILES" ]; then
    echo "Error: $POTFILES not found. Create it with a list of source files." >&2
    exit 1
fi

echo "Extracting translatable strings..."

xgettext \
    --files-from="$POTFILES" \
    --output="$OUTPUT" \
    --language=Python \
    --from-code=UTF-8 \
    --keyword=_ \
    --keyword=N_ \
    --keyword=ngettext:1,2 \
    --keyword=pgettext:1c,2 \
    --add-comments=Translators: \
    --package-name=ClamUI \
    --package-version="$(grep 'version = ' pyproject.toml | head -1 | sed 's/.*"\(.*\)"/\1/')" \
    --copyright-holder="ClamUI Contributors" \
    --msgid-bugs-address="https://github.com/linx-systems/clamui/issues"

# Count extracted strings
COUNT=$(grep -c '^msgid ' "$OUTPUT" 2>/dev/null || echo 0)
# Subtract 1 for the empty msgid header
COUNT=$((COUNT - 1))

echo "Generated $OUTPUT with $COUNT translatable strings."
