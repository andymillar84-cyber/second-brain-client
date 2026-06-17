#!/usr/bin/env bash
# detect-bundle-id.sh — find the Google Keep PWA's bundle ID and write it where
# the Hammerspoon config (init.lua) reads it from: ~/.hammerspoon/keep_bundle_id.txt
#
# Works for any Chromium browser (Edge, Chrome, Brave, Arc) since each installs a
# PWA as a .app bundle with its own CFBundleIdentifier. Re-run any time the PWA is
# reinstalled. Run AFTER installing the Keep PWA (INSTALL.md step 2).

set -euo pipefail

OUT="$HOME/.hammerspoon/keep_bundle_id.txt"

# Standard install locations for Chromium PWAs on macOS.
SEARCH_DIRS=(
  "$HOME/Applications/Chrome Apps.localized"
  "$HOME/Applications/Edge Apps.localized"
  "$HOME/Applications/Brave Apps.localized"
  "$HOME/Applications"
  "/Applications"
)

bundle_id_of() {
  local app="$1" id
  id="$(mdls -name kMDItemCFBundleIdentifier -raw "$app" 2>/dev/null || true)"
  if [ -z "$id" ] || [ "$id" = "(null)" ]; then
    id="$(defaults read "$app/Contents/Info" CFBundleIdentifier 2>/dev/null || true)"
  fi
  printf '%s' "$id"
}

# Collect candidate Keep PWA apps.
declare -a APPS=()
for dir in "${SEARCH_DIRS[@]}"; do
  [ -d "$dir" ] || continue
  while IFS= read -r -d '' app; do
    APPS+=("$app")
  done < <(find "$dir" -maxdepth 1 -iname '*keep*.app' -print0 2>/dev/null)
done

if [ "${#APPS[@]}" -eq 0 ]; then
  echo "✗ No Keep PWA found." >&2
  echo "  Install it first: open keep.google.com in the browser, then" >&2
  echo "  Edge: ⋯ → Apps → Install this site as an app." >&2
  echo "  Chrome: install icon in the address bar." >&2
  echo "  (See INSTALL.md step 2.) Then re-run this script." >&2
  exit 1
fi

CHOSEN=""
if [ "${#APPS[@]}" -eq 1 ]; then
  CHOSEN="${APPS[0]}"
else
  echo "Multiple Keep-like apps found — pick one:"
  i=1
  for app in "${APPS[@]}"; do
    echo "  [$i] $app  ($(bundle_id_of "$app"))"
    i=$((i + 1))
  done
  printf "Enter number: "
  read -r choice
  idx=$((choice - 1))
  if [ "$idx" -lt 0 ] || [ "$idx" -ge "${#APPS[@]}" ]; then
    echo "✗ Invalid choice." >&2
    exit 1
  fi
  CHOSEN="${APPS[$idx]}"
fi

ID="$(bundle_id_of "$CHOSEN")"
if [ -z "$ID" ]; then
  echo "✗ Found '$CHOSEN' but could not read its bundle ID." >&2
  exit 1
fi

mkdir -p "$HOME/.hammerspoon"
printf '%s\n' "$ID" > "$OUT"

echo "✓ Keep PWA:  $CHOSEN"
echo "✓ Bundle ID: $ID"
echo "✓ Wrote:     $OUT"
echo
echo "Next: copy init.lua to ~/.hammerspoon/init.lua and reload Hammerspoon."
