from __future__ import annotations

import argparse
import html
import json
import os
import re
from collections import Counter
from datetime import datetime, timezone
from email.parser import BytesParser
from email.policy import default
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path, PurePosixPath
from urllib.parse import urlparse


PROJECT_ROOT = Path(__file__).resolve().parent.parent
LAB_DATA_ROOT = PROJECT_ROOT / "lab-data"
TASKS_ROOT = LAB_DATA_ROOT / "tasks"
ASSETS_ROOT = LAB_DATA_ROOT / "assets"
SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "dist", "build", ".next", ".turbo", "__pycache__"}
KEY_FILE_GROUPS = {
    "python": ["pyproject.toml", "requirements.txt", "poetry.lock"],
    "node": ["package.json", "pnpm-lock.yaml", "yarn.lock", "package-lock.json"],
    "go": ["go.mod"],
    "rust": ["Cargo.toml"],
    "java": ["pom.xml", "build.gradle", "settings.gradle"],
    "docker": ["Dockerfile", "docker-compose.yml", "docker-compose.yaml"],
    "agent": ["AGENTS.md", "CLAUDE.md", ".mcp.json"],
}
LANGUAGE_MAP = {
    ".py": "Python",
    ".js": "JavaScript",
    ".mjs": "JavaScript",
    ".cjs": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".jsx": "JavaScript",
    ".ps1": "PowerShell",
    ".md": "Markdown",
    ".json": "JSON",
    ".toml": "TOML",
    ".yaml": "YAML",
    ".yml": "YAML",
    ".go": "Go",
    ".rs": "Rust",
    ".java": "Java",
    ".kt": "Kotlin",
    ".cs": "C#",
    ".cpp": "C++",
    ".c": "C",
}


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def slugify(value: str) -> str:
    clean = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip()).strip("-").lower()
    return clean or "task"


def task_id_from_title(title: str) -> str:
    return f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{slugify(title)[:48]}"


def ensure_layout() -> None:
    for path in [
        TASKS_ROOT,
        ASSETS_ROOT / "reports",
        ASSETS_ROOT / "insights",
        ASSETS_ROOT / "playbooks",
        ASSETS_ROOT / "policy-candidates",
    ]:
        path.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def safe_relative_path(raw_name: str) -> Path:
    normalized = raw_name.replace("\\", "/").lstrip("/")
    cleaned = PurePosixPath(normalized)
    parts = [part for part in cleaned.parts if part not in ("", ".", "..")]
    if not parts:
        raise ValueError("empty upload path")
    return Path(*parts)


def collect_inventory(root: Path) -> dict:
    file_count = 0
    dir_count = 0
    total_bytes = 0
    extensions: Counter[str] = Counter()
    languages: Counter[str] = Counter()
    key_hits: dict[str, list[str]] = {group: [] for group in KEY_FILE_GROUPS}
    largest_files: list[tuple[int, str]] = []

    for current_root, dirs, files in os.walk(root):
        dirs[:] = [item for item in dirs if item not in SKIP_DIRS]
        current_path = Path(current_root)
        if current_path != root:
            dir_count += 1
        for file_name in files:
            file_path = current_path / file_name
            try:
                stat = file_path.stat()
            except OSError:
                continue
            rel = file_path.relative_to(root).as_posix()
            file_count += 1
            total_bytes += stat.st_size
            suffix = file_path.suffix.lower()
            extensions[suffix or "<none>"] += 1
            language = LANGUAGE_MAP.get(suffix)
            if language:
                languages[language] += 1
            largest_files.append((stat.st_size, rel))
            for group, names in KEY_FILE_GROUPS.items():
                if file_name in names:
                    key_hits[group].append(rel)

    largest_files.sort(reverse=True)
    project_types = [group for group, hits in key_hits.items() if hits]
    return {
        "root_path": str(root),
        "scanned_at": now_utc(),
        "file_count": file_count,
        "dir_count": dir_count,
        "total_bytes": total_bytes,
        "top_extensions": extensions.most_common(12),
        "top_languages": languages.most_common(8),
        "project_types": project_types,
        "key_files": {group: hits[:12] for group, hits in key_hits.items() if hits},
        "largest_files": [{"path": path, "bytes": size} for size, path in largest_files[:12]],
    }


def build_report(task: dict, inventory: dict) -> str:
    top_langs = ", ".join(f"{name}({count})" for name, count in inventory["top_languages"][:5]) or "未识别"
    project_types = ", ".join(inventory["project_types"]) or "未识别"
    return "\n".join(
        [
            f"# {task['title']}",
            "",
            f"- `task_id`: {task['task_id']}",
            f"- `source_mode`: {task['source_mode']}",
            f"- `submitted_at`: {task['submitted_at']}",
            f"- `goal`: {task['goal'] or '未填写'}",
            "",
            "## 首轮分析",
            "",
            f"- 项目类型信号：{project_types}",
            f"- 文件总数：{inventory['file_count']}",
            f"- 目录总数：{inventory['dir_count']}",
            f"- 总体积：{inventory['total_bytes']} bytes",
            f"- 主要语言：{top_langs}",
            "",
            "## 下一步建议",
            "",
            "- 先基于关键文件和目录树做项目分层，再决定是走代码审计、workflow 体检还是 harness 体检。",
            "- 如果这是一个完整程序目录，优先检查 `AGENTS.md`、构建文件、依赖文件、容器文件和 CI 配置。",
            "- 如果目录很大，后续分析应优先读取索引与关键入口文件，避免全量灌入上下文。",
        ]
    )


def create_task_dirs(task_id: str) -> dict[str, Path]:
    task_root = TASKS_ROOT / task_id
    paths = {
        "task_root": task_root,
        "input": task_root / "input",
        "workspace": task_root / "workspace",
        "logs": task_root / "logs",
        "outputs": task_root / "outputs",
        "artifacts": task_root / "artifacts",
    }
    for path in paths.values():
        path.mkdir(parents=True, exist_ok=True)
    return paths


def create_task(title: str, goal: str, source_mode: str, source_path: str | None = None) -> dict:
    ensure_layout()
    task_id = task_id_from_title(title)
    paths = create_task_dirs(task_id)
    task = {
        "task_id": task_id,
        "title": title,
        "goal": goal,
        "source_mode": source_mode,
        "source_path": source_path,
        "status": "intaked",
        "submitted_at": now_utc(),
        "task_root": str(paths["task_root"]),
    }
    write_json(paths["task_root"] / "task.json", task)
    return task


def finalize_task(task: dict, analysis_root: Path, note: str | None = None) -> dict:
    task_root = Path(task["task_root"])
    inventory = collect_inventory(analysis_root)
    if note:
        inventory["note"] = note
    report = build_report(task, inventory)
    write_json(task_root / "artifacts" / "inventory.json", inventory)
    (task_root / "outputs" / "report.md").write_text(report, encoding="utf-8")
    task["status"] = "analyzed"
    task["analyzed_at"] = now_utc()
    write_json(task_root / "task.json", task)
    return {"task": task, "inventory": inventory, "report": report}


def intake_local_path(source_path: Path, title: str, goal: str) -> dict:
    if not source_path.exists() or not source_path.is_dir():
        raise FileNotFoundError(f"source path not found: {source_path}")
    task = create_task(title=title, goal=goal, source_mode="local_path", source_path=str(source_path))
    task_root = Path(task["task_root"])
    write_json(task_root / "artifacts" / "source-pointer.json", {"source_path": str(source_path)})
    return finalize_task(task, source_path, note="本任务直接分析本地路径，未复制原项目文件。")


def intake_uploaded_files(files: list[dict], title: str, goal: str) -> dict:
    task = create_task(title=title, goal=goal, source_mode="folder_upload")
    input_root = Path(task["task_root"]) / "input"
    saved = 0
    for file_item in files:
        if not file_item.get("filename"):
            continue
        rel_path = safe_relative_path(file_item["filename"])
        target = input_root / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "wb") as handle:
            handle.write(file_item["content"])
        saved += 1
    if saved == 0:
        raise ValueError("no uploaded files received")
    return finalize_task(task, input_root, note=f"通过浏览器文件夹上传接收了 {saved} 个文件。")


def list_recent_tasks(limit: int = 12) -> list[dict]:
    if not TASKS_ROOT.exists():
        return []
    tasks = []
    for task_dir in sorted(TASKS_ROOT.iterdir(), reverse=True):
        task_file = task_dir / "task.json"
        if task_file.exists():
            tasks.append(json.loads(task_file.read_text(encoding="utf-8")))
        if len(tasks) >= limit:
            break
    return tasks


class LabHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/":
            self._send_html(self.render_index())
            return
        if path.startswith("/tasks/"):
            task_id = path.split("/")[-1]
            self._send_html(self.render_task(task_id))
            return
        self.send_error(404, "Not Found")

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        if path != "/api/tasks":
            self.send_error(404, "Not Found")
            return
        fields, files = self.parse_multipart_form()
        title = (fields.get("title") or "project-intake").strip()
        goal = (fields.get("goal") or "").strip()
        source_path = (fields.get("source_path") or "").strip()
        try:
            result = intake_local_path(Path(source_path), title, goal) if source_path else intake_uploaded_files(files, title, goal)
        except Exception as exc:  # noqa: BLE001
            self._send_json({"ok": False, "error": str(exc)}, status=400)
            return
        self._send_json({"ok": True, "task_id": result["task"]["task_id"], "task_url": f"/tasks/{result['task']['task_id']}"})

    def parse_multipart_form(self) -> tuple[dict[str, str], list[dict]]:
        content_type = self.headers.get("Content-Type", "")
        content_length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(content_length)
        raw = f"Content-Type: {content_type}\r\nMIME-Version: 1.0\r\n\r\n".encode("utf-8") + body
        message = BytesParser(policy=default).parsebytes(raw)
        fields: dict[str, str] = {}
        files: list[dict] = []
        for part in message.iter_parts():
            name = part.get_param("name", header="content-disposition")
            if not name:
                continue
            filename = part.get_filename()
            payload = part.get_payload(decode=True) or b""
            if filename:
                files.append({"field": name, "filename": filename, "content": payload})
            else:
                fields[name] = payload.decode(part.get_content_charset() or "utf-8", errors="replace")
        return fields, files

    def render_index(self) -> str:
        tasks_html = "".join(
            f"<li><a href='/tasks/{html.escape(task['task_id'])}'>{html.escape(task['title'])}</a> "
            f"<span>{html.escape(task['status'])}</span></li>"
            for task in list_recent_tasks()
        ) or "<li>还没有任务</li>"
        return f"""<!doctype html><html><head><meta charset='utf-8'><title>Open Lab</title>
<style>body{{font-family:Segoe UI,sans-serif;max-width:960px;margin:32px auto;padding:0 16px}}section{{border:1px solid #ddd;padding:16px;margin:16px 0;border-radius:12px}}label{{display:block;margin:10px 0 4px}}input,textarea{{width:100%;padding:10px;box-sizing:border-box}}button{{margin-top:12px;padding:10px 16px}}small{{color:#555}}</style></head>
<body><h1>Open Lab</h1><p>开放入口已启用。你可以上传整个项目文件夹，或者直接填本机项目路径进行首轮分析。</p>
<section><h2>上传整个文件夹</h2><form id='upload-form'><label>任务标题</label><input name='title' value='program-folder-intake'><label>分析目标</label><textarea name='goal' rows='3'>先做项目清单、入口文件识别、关键配置识别与后续实验建议。</textarea><label>项目文件夹</label><input id='folder-input' type='file' webkitdirectory directory multiple><small>浏览器会保留相对路径并上传到当前 lab 任务目录。</small><br><button type='submit'>创建上传分析任务</button></form></section>
<section><h2>本机路径导入</h2><form method='post' action='/api/tasks' enctype='multipart/form-data'><label>任务标题</label><input name='title' value='local-path-intake'><label>分析目标</label><textarea name='goal' rows='3'>对整个程序目录做首轮架构、依赖、workflow 与 harness 分析。</textarea><label>本机路径</label><input name='source_path' placeholder='F:\\01-Projects\\your-project'><button type='submit'>按本机路径创建任务</button></form></section>
<section><h2>最近任务</h2><ul>{tasks_html}</ul></section>
<script>
document.getElementById('upload-form').addEventListener('submit', async (event) => {{
  event.preventDefault();
  const form = event.currentTarget;
  const files = document.getElementById('folder-input').files;
  const data = new FormData();
  data.append('title', form.title.value);
  data.append('goal', form.goal.value);
  for (const file of files) {{
    data.append('files', file, file.webkitRelativePath || file.name);
  }}
  const response = await fetch('/api/tasks', {{ method: 'POST', body: data }});
  const payload = await response.json();
  if (!payload.ok) {{
    alert(payload.error || '创建任务失败');
    return;
  }}
  window.location.href = payload.task_url;
}});
</script></body></html>"""

    def render_task(self, task_id: str) -> str:
        task_root = TASKS_ROOT / task_id
        task = json.loads((task_root / "task.json").read_text(encoding="utf-8"))
        inventory = json.loads((task_root / "artifacts" / "inventory.json").read_text(encoding="utf-8"))
        report = (task_root / "outputs" / "report.md").read_text(encoding="utf-8")
        return f"""<!doctype html><html><head><meta charset='utf-8'><title>{html.escape(task['title'])}</title>
<style>body{{font-family:Segoe UI,sans-serif;max-width:1080px;margin:32px auto;padding:0 16px}}pre{{white-space:pre-wrap;background:#f6f6f6;padding:16px;border-radius:12px}}a{{color:#0055aa}}</style></head>
<body><p><a href='/'>返回 Open Lab</a></p><h1>{html.escape(task['title'])}</h1>
<p><strong>task_id:</strong> {html.escape(task['task_id'])}</p>
<p><strong>source_mode:</strong> {html.escape(task['source_mode'])}</p>
<p><strong>task_root:</strong> {html.escape(task['task_root'])}</p>
<h2>首轮报告</h2><pre>{html.escape(report)}</pre>
<h2>Inventory JSON</h2><pre>{html.escape(json.dumps(inventory, ensure_ascii=False, indent=2))}</pre></body></html>"""

    def _send_html(self, body: str, status: int = 200) -> None:
        encoded = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _send_json(self, payload: dict, status: int = 200) -> None:
        encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)


def main() -> None:
    parser = argparse.ArgumentParser(description="Open Lab intake server")
    subparsers = parser.add_subparsers(dest="command", required=True)

    serve_parser = subparsers.add_parser("serve", help="start local lab server")
    serve_parser.add_argument("--host", default="127.0.0.1")
    serve_parser.add_argument("--port", type=int, default=8765)

    intake_parser = subparsers.add_parser("intake-local", help="create a task from a local project path")
    intake_parser.add_argument("--source-path", required=True)
    intake_parser.add_argument("--title", required=True)
    intake_parser.add_argument("--goal", default="")

    args = parser.parse_args()
    if args.command == "serve":
        ensure_layout()
        server = ThreadingHTTPServer((args.host, args.port), LabHandler)
        print(f"Open Lab running at http://{args.host}:{args.port}")
        server.serve_forever()
        return

    result = intake_local_path(Path(args.source_path), args.title, args.goal)
    print(result["task"]["task_id"])
    print(result["task"]["task_root"])


if __name__ == "__main__":
    main()
