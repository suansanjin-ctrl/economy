#!/bin/zsh

set -euo pipefail

LABEL="com.dzh.live-summary-auto-publish"
PLIST_PATH="$HOME/Library/LaunchAgents/$LABEL.plist"
DESKTOP_SHORTCUT="$HOME/Desktop/自动上传HTML"

launchctl bootout "gui/$(id -u)" "$PLIST_PATH" >/dev/null 2>&1 || true
rm -f "$PLIST_PATH"
if [ -L "$DESKTOP_SHORTCUT" ]; then
  rm -f "$DESKTOP_SHORTCUT"
fi

echo "已移除自动发布监听：$LABEL"
