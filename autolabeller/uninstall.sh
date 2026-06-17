#!/usr/bin/env bash
# Remove the Keep auto-labeller launchd agent. Leaves state/logs intact.
set -euo pipefail
PLIST="$HOME/Library/LaunchAgents/com.andrew.keep-autolabel.plist"
launchctl unload "$PLIST" 2>/dev/null || true
rm -f "$PLIST"
echo "✓ uninstalled. State + logs kept at ~/.config/keep-autolabel/ (delete manually if you want a clean slate)."
