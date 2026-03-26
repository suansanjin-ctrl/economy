#!/bin/zsh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PUBLISH_SCRIPT="$SCRIPT_DIR/scripts/publish_report.py"

trim_input() {
  local value="$1"
  value="${value#\"}"
  value="${value%\"}"
  value="${value#\'}"
  value="${value%\'}"
  printf "%s" "$value"
}

prompt_if_empty() {
  local prompt_text="$1"
  local current_value="${2:-}"
  if [[ -n "$current_value" ]]; then
    printf "%s" "$current_value"
    return
  fi

  printf "%s" "$prompt_text"
  local result
  IFS= read -r result
  printf "%s" "$(trim_input "$result")"
}

SOURCE_PATH="${1:-}"
TITLE="${2:-}"
DATE_VALUE="${3:-}"
ENTRY_FILE="${4:-}"

clear
echo "========================================"
echo " HTML 周报发布"
echo "========================================"
echo

SOURCE_PATH="$(prompt_if_empty '把 HTML 文件或报告目录拖到这里，然后回车: ' "$SOURCE_PATH")"
TITLE="$(prompt_if_empty '标题（可留空，默认用文件名）: ' "$TITLE")"

if [[ -z "$DATE_VALUE" ]]; then
  DEFAULT_DATE="$(date +%F)"
  printf "日期（默认 %s）: " "$DEFAULT_DATE"
  IFS= read -r DATE_VALUE
  DATE_VALUE="$(trim_input "$DATE_VALUE")"
  DATE_VALUE="${DATE_VALUE:-$DEFAULT_DATE}"
fi

if [[ -z "$ENTRY_FILE" ]]; then
  printf "入口 HTML（目录模式才需要，可留空）: "
  IFS= read -r ENTRY_FILE
  ENTRY_FILE="$(trim_input "$ENTRY_FILE")"
fi

if [[ -z "$SOURCE_PATH" ]]; then
  echo
  echo "没有收到来源路径，已退出。"
  read -r "?按回车结束..."
  exit 1
fi

COMMAND=(python3 "$PUBLISH_SCRIPT" "$SOURCE_PATH" --date "$DATE_VALUE")

if [[ -n "$TITLE" ]]; then
  COMMAND+=(--title "$TITLE")
fi

if [[ -n "$ENTRY_FILE" ]]; then
  COMMAND+=(--entry "$ENTRY_FILE")
fi

echo
echo "正在发布..."
echo
"${COMMAND[@]}"

echo
echo "完成。"
read -r "?按回车结束..."

