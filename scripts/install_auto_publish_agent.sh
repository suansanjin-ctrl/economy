#!/bin/zsh

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
LABEL="com.dzh.live-summary-auto-publish"
PLIST_PATH="$HOME/Library/LaunchAgents/$LABEL.plist"
RUNTIME_ROOT="$HOME/Library/Application Support/live-summary-auto-publish"
RUNTIME_REPO="$RUNTIME_ROOT/repo"
SOURCE_DIR="${1:-$HOME/live-summary-inbox}"
DESKTOP_SHORTCUT="${2:-$HOME/Desktop/自动上传HTML}"
LOG_DIR="$RUNTIME_ROOT/logs"
STATE_FILE="$RUNTIME_ROOT/.auto_publish_state.json"

mkdir -p "$HOME/Library/LaunchAgents"
mkdir -p "$RUNTIME_ROOT"
mkdir -p "$SOURCE_DIR"
mkdir -p "$LOG_DIR"

rsync -a --delete \
  --exclude 'logs/' \
  --exclude '.auto_publish_state.json' \
  --exclude '__pycache__/' \
  --exclude '*.pyc' \
  "$ROOT_DIR/" "$RUNTIME_REPO/"

ln -sfn "$SOURCE_DIR" "$DESKTOP_SHORTCUT"

cat > "$PLIST_PATH" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>$LABEL</string>
  <key>ProgramArguments</key>
  <array>
    <string>/usr/bin/python3</string>
    <string>$RUNTIME_REPO/scripts/auto_publish_from_folder.py</string>
    <string>--source-dir</string>
    <string>$SOURCE_DIR</string>
    <string>--state-file</string>
    <string>$STATE_FILE</string>
    <string>--branch</string>
    <string>main</string>
  </array>
  <key>RunAtLoad</key>
  <true/>
  <key>StartInterval</key>
  <integer>60</integer>
  <key>WorkingDirectory</key>
  <string>$RUNTIME_REPO</string>
  <key>StandardOutPath</key>
  <string>$LOG_DIR/auto_publish.log</string>
  <key>StandardErrorPath</key>
  <string>$LOG_DIR/auto_publish.error.log</string>
</dict>
</plist>
EOF

launchctl bootout "gui/$(id -u)" "$PLIST_PATH" >/dev/null 2>&1 || true
launchctl bootstrap "gui/$(id -u)" "$PLIST_PATH"
launchctl kickstart -k "gui/$(id -u)/$LABEL"

echo "已安装自动发布监听：$LABEL"
echo "监听文件夹：$SOURCE_DIR"
echo "桌面快捷入口：$DESKTOP_SHORTCUT"
echo "后台工作目录：$RUNTIME_REPO"
echo "日志文件：$LOG_DIR/auto_publish.log"
