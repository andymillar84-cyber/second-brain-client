#!/usr/bin/env bash
# Install the Keep auto-labeller as an hourly launchd agent.
# Portable: derives all paths from $HOME and this folder's location, so it works
# on any Mac (Andrew's or a client's) after `git clone`.
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLIST="$HOME/Library/LaunchAgents/com.andrew.keep-autolabel.plist"
STATE="$HOME/.config/keep-autolabel"

mkdir -p "$STATE"                 # launchd opens the log files before the script runs

cat > "$PLIST" <<PLISTEOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.andrew.keep-autolabel</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>$DIR/autolabel.py</string>
    </array>
    <key>StartInterval</key>
    <integer>3600</integer>
    <key>RunAtLoad</key>
    <true/>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
        <key>HOME</key>
        <string>$HOME</string>
    </dict>
    <key>StandardOutPath</key>
    <string>$STATE/launchd.out.log</string>
    <key>StandardErrorPath</key>
    <string>$STATE/launchd.err.log</string>
</dict>
</plist>
PLISTEOF

launchctl unload "$PLIST" 2>/dev/null || true
launchctl load "$PLIST"

echo "✓ installed + loaded (runs hourly, and once now)"
echo "  code:  $DIR/autolabel.py"
echo "  logs:  $STATE/  (daily-YYYY-MM-DD.log is your end-of-day review)"
echo "  pause: launchctl unload \"$PLIST\""
