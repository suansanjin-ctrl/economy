#!/usr/bin/env python3

from __future__ import annotations

import argparse
import hashlib
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from publish_report import commit_and_push, publish_source, resolve_source_info


ROOT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_SOURCE_DIR = Path.home() / "Desktop" / "金融学习资料"
DEFAULT_STATE_PATH = ROOT_DIR / ".auto_publish_state.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scan a folder for new HTML items and publish them automatically."
    )
    parser.add_argument(
        "--source-dir",
        default=str(DEFAULT_SOURCE_DIR),
        help="Folder to scan for HTML files or report directories.",
    )
    parser.add_argument(
        "--state-file",
        default=str(DEFAULT_STATE_PATH),
        help="JSON file used to remember processed items.",
    )
    parser.add_argument(
        "--branch",
        default="main",
        help="Git branch used when pushing updates.",
    )
    parser.add_argument(
        "--min-age-seconds",
        type=int,
        default=10,
        help="Skip files that were modified too recently, to avoid publishing half-copied content.",
    )
    return parser.parse_args()


def load_state(state_path: Path) -> dict[str, Any]:
    if not state_path.exists():
        return {"items": {}}

    try:
        return json.loads(state_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"items": {}}


def save_state(state_path: Path, state: dict[str, Any]) -> None:
    state_path.write_text(
        json.dumps(state, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def candidate_paths(source_dir: Path) -> list[Path]:
    candidates: list[Path] = []
    for path in sorted(source_dir.iterdir(), key=lambda item: item.name.lower()):
        if path.name.startswith("."):
            continue
        if path.is_file() and path.suffix.lower() == ".html":
            candidates.append(path)
            continue
        if path.is_dir():
            try:
                resolve_source_info(path, None)
            except SystemExit:
                continue
            candidates.append(path)
    return candidates


def fingerprint_file(path: Path) -> tuple[str, float]:
    stat = path.stat()
    digest = hashlib.sha256(
        f"file::{path.name}::{stat.st_size}::{stat.st_mtime_ns}".encode("utf-8")
    ).hexdigest()
    return digest, stat.st_mtime


def fingerprint_directory(path: Path) -> tuple[str, float]:
    parts: list[str] = []
    newest_mtime = path.stat().st_mtime
    for child in sorted(item for item in path.rglob("*") if item.is_file()):
        stat = child.stat()
        newest_mtime = max(newest_mtime, stat.st_mtime)
        parts.append(
            f"{child.relative_to(path).as_posix()}::{stat.st_size}::{stat.st_mtime_ns}"
        )
    digest = hashlib.sha256(
        ("dir::" + path.name + "::" + "\n".join(parts)).encode("utf-8")
    ).hexdigest()
    return digest, newest_mtime


def fingerprint_path(path: Path) -> tuple[str, float]:
    if path.is_dir():
        return fingerprint_directory(path)
    return fingerprint_file(path)


def should_skip_recent(path: Path, min_age_seconds: int) -> bool:
    _, latest_mtime = fingerprint_path(path)
    return (time.time() - latest_mtime) < min_age_seconds


def publish_candidate(path: Path, branch: str) -> dict[str, Any]:
    title = path.stem if path.is_file() else path.name
    report_record = publish_source(path, title=title)
    commit_and_push(report_record["title"], branch, False, False)
    return report_record


def main() -> None:
    args = parse_args()
    source_dir = Path(args.source_dir).expanduser().resolve()
    state_path = Path(args.state_file).expanduser().resolve()
    state_path.parent.mkdir(parents=True, exist_ok=True)

    if not source_dir.exists():
        print(f"提示：自动发布文件夹不存在：{source_dir}")
        return

    if not source_dir.is_dir():
        print(f"提示：自动发布来源不是文件夹：{source_dir}")
        return

    state = load_state(state_path)
    items = state.setdefault("items", {})
    processed_any = False

    for path in candidate_paths(source_dir):
        if should_skip_recent(path, args.min_age_seconds):
            print(f"跳过：{path.name} 还在写入，稍后会再检查。")
            continue

        fingerprint, _ = fingerprint_path(path)
        path_key = str(path)
        if items.get(path_key, {}).get("fingerprint") == fingerprint:
            continue

        try:
            report_record = publish_candidate(path, args.branch)
        except SystemExit as exc:
            print(f"失败：{path.name} -> {exc}")
            continue

        items[path_key] = {
            "fingerprint": fingerprint,
            "lastReportId": report_record["id"],
            "lastPublishedAt": datetime.now().astimezone().isoformat(timespec="seconds"),
        }
        processed_any = True
        print(f"已自动发布：{path.name} -> {report_record['id']}")

    if processed_any:
        state["sourceDir"] = str(source_dir)
        save_state(state_path, state)
    else:
        print("没有新的 HTML 需要自动发布。")


if __name__ == "__main__":
    main()

