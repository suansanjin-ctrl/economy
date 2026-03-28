#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parent.parent
SITE_DIR = ROOT_DIR / "site"
REPORTS_DIR = SITE_DIR / "reports"
JSON_MANIFEST_PATH = SITE_DIR / "data" / "reports.json"
JS_MANIFEST_PATH = SITE_DIR / "data" / "reports.js"
GIT_ADD_PATHS = [
    "site",
    "scripts",
    ".github",
    "README.md",
    ".gitignore",
    "publish.command",
]


@dataclass
class SourceInfo:
    source: Path
    entry_relative_path: str
    original_name: str
    source_type: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Copy a weekly HTML report into the site, update the manifest, and optionally commit/push."
    )
    parser.add_argument("source", help="Source HTML file or directory.")
    parser.add_argument("--entry", help="Entry HTML path relative to the source directory.")
    parser.add_argument("--title", help="Display title shown on the homepage.")
    parser.add_argument("--date", help="Display date, for example 2026-03-24.")
    parser.add_argument("--description", help="Optional short description for future use.")
    parser.add_argument("--slug", help="Optional custom slug for the destination folder.")
    parser.add_argument("--branch", default="main", help="Git branch to push. Defaults to main.")
    parser.add_argument("--no-commit", action="store_true", help="Skip git commit.")
    parser.add_argument("--no-push", action="store_true", help="Skip git push.")
    return parser.parse_args()


def fail(message: str) -> None:
    print(f"Error: {message}", file=sys.stderr)
    raise SystemExit(1)


def load_manifest() -> dict[str, Any]:
    if not JSON_MANIFEST_PATH.exists():
        return {"generatedAt": None, "reports": []}

    try:
        return json.loads(JSON_MANIFEST_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"Cannot parse manifest: {exc}")


def save_manifest(manifest: dict[str, Any]) -> None:
    JSON_MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    JSON_MANIFEST_PATH.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    JS_MANIFEST_PATH.write_text(
        "window.REPORTS_MANIFEST = " + json.dumps(manifest, ensure_ascii=False, indent=2) + ";\n",
        encoding="utf-8",
    )


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_value).strip("-").lower()
    return slug or "report"


def normalize_date(value: str) -> str:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date().isoformat()
    except ValueError:
        fail("Date must use the format YYYY-MM-DD.")


def ensure_unique_slug(base_slug: str, existing_reports: list[dict[str, Any]]) -> str:
    existing_ids = {report["id"] for report in existing_reports}
    if base_slug not in existing_ids:
        return base_slug

    index = 2
    while f"{base_slug}-{index}" in existing_ids:
        index += 1
    return f"{base_slug}-{index}"


def resolve_source_info(source_path: Path, entry: str | None) -> SourceInfo:
    if not source_path.exists():
        fail(f"Source path does not exist: {source_path}")

    if source_path.is_file():
        if source_path.suffix.lower() != ".html":
            fail("When source is a file, it must be an .html file.")
        return SourceInfo(
            source=source_path,
            entry_relative_path="index.html",
            original_name=source_path.name,
            source_type="file",
        )

    if source_path.is_dir():
        if entry:
            entry_path = source_path / entry
            if not entry_path.exists() or not entry_path.is_file():
                fail(f"Specified entry file does not exist: {entry}")
            return SourceInfo(
                source=source_path,
                entry_relative_path=entry.replace("\\", "/"),
                original_name=entry_path.name,
                source_type="directory",
            )

        default_entry = source_path / "index.html"
        if default_entry.exists():
            return SourceInfo(
                source=source_path,
                entry_relative_path="index.html",
                original_name="index.html",
                source_type="directory",
            )

        html_files = sorted(path for path in source_path.rglob("*.html") if path.is_file())
        if len(html_files) == 1:
            return SourceInfo(
                source=source_path,
                entry_relative_path=str(html_files[0].relative_to(source_path)).replace("\\", "/"),
                original_name=html_files[0].name,
                source_type="directory",
            )

        fail("Directory source must contain index.html, exactly one HTML file, or use --entry.")

    fail(f"Unsupported source path: {source_path}")


def copy_source(source_info: SourceInfo, destination_dir: Path) -> str:
    if destination_dir.exists():
        fail(f"Destination already exists: {destination_dir}")

    destination_dir.parent.mkdir(parents=True, exist_ok=True)

    if source_info.source_type == "file":
        destination_dir.mkdir(parents=True, exist_ok=False)
        shutil.copy2(source_info.source, destination_dir / "index.html")
        return "index.html"

    shutil.copytree(source_info.source, destination_dir)
    return source_info.entry_relative_path


def sort_reports(reports: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        reports,
        key=lambda report: (
            report.get("date", ""),
            report.get("addedAt", ""),
            report.get("title", ""),
        ),
        reverse=True,
    )


def run_git_command(args: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT_DIR,
        text=True,
        capture_output=True,
        check=check,
    )


def is_git_repo() -> bool:
    result = subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"],
        cwd=ROOT_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
    )
    return result.returncode == 0 and result.stdout.strip() == "true"


def has_remote(name: str) -> bool:
    result = subprocess.run(
        ["git", "remote", "get-url", name],
        cwd=ROOT_DIR,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        text=True,
    )
    return result.returncode == 0


def commit_and_push(title: str, branch: str, skip_commit: bool, skip_push: bool) -> None:
    if not is_git_repo():
        print("提示：当前目录还不是 Git 仓库，已完成本地发布，但未执行 commit / push。")
        print("先运行：git init -b main")
        return

    run_git_command(["add", *GIT_ADD_PATHS])

    if skip_commit:
        print("提示：已按要求跳过 git commit。")
        return

    status = run_git_command(["status", "--short"], check=False)
    if not status.stdout.strip():
        print("提示：没有新的 Git 变更，无需提交。")
    else:
        message = f"Add report: {title}"
        commit = run_git_command(["commit", "-m", message], check=False)
        if commit.returncode != 0:
            fail(commit.stderr.strip() or "git commit failed")
        print(commit.stdout.strip())

    if skip_push:
        print("提示：已按要求跳过 git push。")
        return

    if not has_remote("origin"):
        print("提示：未检测到 origin 远程仓库，已完成本地提交，但还没有推送到 GitHub。")
        print("先运行：git remote add origin git@github.com:你的用户名/你的仓库名.git")
        return

    push = run_git_command(["push", "origin", branch], check=False)
    if push.returncode != 0:
        fail(push.stderr.strip() or "git push failed")
    if push.stdout.strip():
        print(push.stdout.strip())
    if push.stderr.strip():
        print(push.stderr.strip())


def publish_source(
    source_path: Path,
    *,
    entry: str | None = None,
    title: str | None = None,
    date_value: str | None = None,
    description: str | None = None,
    slug: str | None = None,
) -> dict[str, Any]:
    resolved_source_path = source_path.expanduser().resolve()
    resolved_title = title or resolved_source_path.stem
    resolved_date = normalize_date(date_value) if date_value else datetime.now().date().isoformat()
    source_info = resolve_source_info(resolved_source_path, entry)
    manifest = load_manifest()

    base_slug_parts = [resolved_date, slug or slugify(resolved_title or resolved_source_path.stem)]
    base_slug = "-".join(part for part in base_slug_parts if part).strip("-")
    report_id = ensure_unique_slug(base_slug or "report", manifest.get("reports", []))
    destination_dir = REPORTS_DIR / report_id
    entry_relative_path = copy_source(source_info, destination_dir)

    report_record = {
        "id": report_id,
        "title": resolved_title,
        "date": resolved_date,
        "description": description or "",
        "href": f"reports/{report_id}/{entry_relative_path}",
        "originalName": source_info.original_name,
        "sourceType": source_info.source_type,
        "addedAt": datetime.now().astimezone().isoformat(timespec="seconds"),
    }

    reports = manifest.get("reports", [])
    reports.append(report_record)
    manifest["generatedAt"] = datetime.now().astimezone().isoformat(timespec="seconds")
    manifest["reports"] = sort_reports(reports)
    save_manifest(manifest)

    return report_record


def main() -> None:
    args = parse_args()

    source_path = Path(args.source)
    report_record = publish_source(
        source_path,
        entry=args.entry,
        title=args.title,
        date_value=args.date,
        description=args.description,
        slug=args.slug,
    )

    print(f"已发布：{report_record['title']}")
    print(f"目录：{REPORTS_DIR / report_record['id']}")
    print(f"入口：site/{report_record['href']}")

    commit_and_push(report_record["title"], args.branch, args.no_commit, args.no_push)


if __name__ == "__main__":
    main()
