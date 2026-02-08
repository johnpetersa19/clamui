#!/bin/bash
# Verify that po/POTFILES.in is in sync with actual i18n usage.
#
# Checks:
#   1. Every .py file that imports from i18n is listed in POTFILES.in
#   2. Every file in POTFILES.in actually imports from i18n
#
# Usage:
#   ./scripts/check-potfiles.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

POTFILES="po/POTFILES.in"
ERRORS=0

if [ ! -f "$POTFILES" ]; then
    echo "Error: $POTFILES not found." >&2
    exit 1
fi

# Get list of files in POTFILES.in (strip comments and blank lines)
mapfile -t LISTED_FILES < <(grep -v '^#' "$POTFILES" | grep -v '^$' | sort)

# Find all .py files under src/ that import from i18n
# Matches: from .i18n, from ..i18n, from ...i18n, from ..core.i18n, etc.
mapfile -t I18N_FILES < <(
    grep -rl --include="*.py" -E "from \.+((core\.)?i18n|i18n) import" src/ | \
    sort
)

echo "Checking POTFILES.in consistency..."
echo "  Files in POTFILES.in: ${#LISTED_FILES[@]}"
echo "  Files with i18n imports: ${#I18N_FILES[@]}"
echo

# Check 1: Files with i18n imports missing from POTFILES.in
for file in "${I18N_FILES[@]}"; do
    # Skip i18n.py itself
    if [[ "$file" == "src/core/i18n.py" ]]; then
        continue
    fi
    if ! grep -qxF "$file" "$POTFILES"; then
        echo "::error file=$file::Missing from $POTFILES: $file imports i18n but is not listed"
        ERRORS=$((ERRORS + 1))
    fi
done

# Check 2: Files in POTFILES.in that don't import i18n
for file in "${LISTED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo "::error file=$POTFILES::Listed file does not exist: $file"
        ERRORS=$((ERRORS + 1))
        continue
    fi
    if ! grep -qE "from \.+((core\.)?i18n|i18n) import" "$file"; then
        echo "::error file=$file::Listed in $POTFILES but does not import i18n: $file"
        ERRORS=$((ERRORS + 1))
    fi
done

# Check 3: Bare untranslated strings in files that HAVE i18n imports
# Detects: .set_title("Foo") but NOT .set_title(_("Foo"))
# Covers common GTK/Adw UI-setting methods
BARE_WARNINGS=0
UI_METHODS="set_title|set_label|set_subtitle|set_description|set_tooltip_text|set_placeholder_text|set_text|set_body|set_heading"

for file in "${I18N_FILES[@]}"; do
    if [[ "$file" == "src/core/i18n.py" ]]; then
        continue
    fi
    # Find lines with UI methods taking a bare string literal (not wrapped in _())
    # Match: .method("string") but NOT .method(_("string")) or .method(N_("string"))
    # Also skip lines that are comments
    while IFS=: read -r lineno line; do
        # Skip comment lines
        stripped="${line#"${line%%[![:space:]]*}"}"
        if [[ "$stripped" == \#* ]]; then
            continue
        fi
        echo "::warning file=$file,line=$lineno::Possible untranslated string: $line"
        BARE_WARNINGS=$((BARE_WARNINGS + 1))
    done < <(grep -nE "\\.(${UI_METHODS})\(\"[^\"]*\"\)" "$file" \
        | grep -v "_(" \
        | grep -v "# i18n: no-translate" \
        | grep -v '("")' \
        || true)
done

if [ "$ERRORS" -gt 0 ]; then
    echo
    echo "Found $ERRORS POTFILES.in consistency error(s)."
    echo "  - If a file imports i18n, add it to $POTFILES"
    echo "  - If a file no longer uses i18n, remove it from $POTFILES"
    exit 1
fi

if [ "$BARE_WARNINGS" -gt 0 ]; then
    echo
    echo "Found $BARE_WARNINGS possible untranslated string(s)."
    echo "  Wrap user-facing strings with _(): .set_title(_(\"text\"))"
    echo "  If intentional (e.g. app name), add  # i18n: no-translate  to suppress"
    exit 1
fi

echo "POTFILES.in is consistent. All files accounted for."
