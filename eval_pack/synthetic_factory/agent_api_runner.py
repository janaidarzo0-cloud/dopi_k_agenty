#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import mimetypes
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


def read_json(url: str) -> dict[str, Any]:
    with urllib.request.urlopen(url, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def post_json(url: str, payload: dict[str, Any]) -> dict[str, Any]:
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def multipart(fields: dict[str, str], files: dict[str, Path]) -> tuple[bytes, str]:
    boundary = "----syntheticFactoryBoundary"
    chunks: list[bytes] = []
    for name, value in fields.items():
        chunks.append(f"--{boundary}\r\n".encode())
        chunks.append(f'Content-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode("utf-8"))
    for name, path in files.items():
        ctype = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        chunks.append(f"--{boundary}\r\n".encode())
        chunks.append(f'Content-Disposition: form-data; name="{name}"; filename="{path.name}"\r\n'.encode("utf-8"))
        chunks.append(f"Content-Type: {ctype}\r\n\r\n".encode())
        chunks.append(path.read_bytes())
        chunks.append(b"\r\n")
    chunks.append(f"--{boundary}--\r\n".encode())
    return b"".join(chunks), f"multipart/form-data; boundary={boundary}"


def create_project(base_url: str, case_root: Path) -> str:
    manifest = json.loads((case_root / "agent_input_manifest.json").read_text(encoding="utf-8"))
    api = manifest.get("api_fields") or {}
    data_path = case_root / str(api.get("data_file", "input/survey.sav"))
    if not data_path.exists() and data_path.with_suffix(".csv").exists():
        data_path = data_path.with_suffix(".csv")
    fields = {
        "prompt": str(api.get("prompt") or ""),
        "max_iterations": str(api.get("max_iterations", 24)),
        "question_timeout_seconds": str(api.get("question_timeout_seconds", 5)),
        "review_mode": "true" if api.get("review_mode", True) else "false",
    }
    files = {
        "data_file": data_path,
        "questionnaire_file": case_root / str(api.get("questionnaire_file", "input/questionnaire.txt")),
        "codebook_file": case_root / str(api.get("codebook_file", "input/codebook.json")),
    }
    body, ctype = multipart(fields, files)
    req = urllib.request.Request(f"{base_url.rstrip('/')}/api/projects", data=body, headers={"Content-Type": ctype}, method="POST")
    with urllib.request.urlopen(req, timeout=60) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    return str(payload["project_id"])


def wait_project(base_url: str, project_id: str, timeout_sec: int) -> dict[str, Any]:
    deadline = time.time() + timeout_sec
    state: dict[str, Any] = {}
    while time.time() < deadline:
        state = read_json(f"{base_url.rstrip('/')}/api/projects/{urllib.parse.quote(project_id)}")
        if str(state.get("status", "")).lower() in {"completed", "failed", "stopped", "analytics_ready"}:
            return state
        time.sleep(3)
    raise TimeoutError(f"Project {project_id} did not finish before timeout")


def download_outputs(base_url: str, project_id: str, out_dir: Path, state: dict[str, Any]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "project_state.json").write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        summary = read_json(f"{base_url.rstrip('/')}/api/projects/{urllib.parse.quote(project_id)}/summary")
        if summary.get("summary") is not None:
            (out_dir / "analysis_summary.json").write_text(json.dumps(summary["summary"], ensure_ascii=False, indent=2), encoding="utf-8")
        (out_dir / "api_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass
    try:
        artifacts = read_json(f"{base_url.rstrip('/')}/api/projects/{urllib.parse.quote(project_id)}/artifacts").get("artifacts", [])
        (out_dir / "artifacts_index.json").write_text(json.dumps(artifacts, ensure_ascii=False, indent=2), encoding="utf-8")
        for item in artifacts:
            artifact_path = item.get("path") or item.get("name") or item.get("artifact_path")
            if not artifact_path:
                continue
            url = f"{base_url.rstrip('/')}/api/projects/{urllib.parse.quote(project_id)}/artifacts/{urllib.parse.quote(str(artifact_path))}"
            try:
                with urllib.request.urlopen(url, timeout=60) as resp:
                    (out_dir / Path(str(artifact_path)).name).write_bytes(resp.read())
            except Exception:
                continue
    except Exception:
        pass


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a generated synthetic case through a local Analytic_AI_agent FastAPI server.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--case-root", type=Path, required=True)
    parser.add_argument("--results-root", type=Path, default=Path("projects_eval/synthetic_results"))
    parser.add_argument("--timeout-sec", type=int, default=1800)
    args = parser.parse_args()
    project_id = create_project(args.base_url, args.case_root)
    state = wait_project(args.base_url, project_id, args.timeout_sec)
    if str(state.get("status", "")).lower() == "analytics_ready":
        post_json(f"{args.base_url.rstrip('/')}/api/projects/{urllib.parse.quote(project_id)}/report", {})
        state = wait_project(args.base_url, project_id, args.timeout_sec)
    out_dir = args.results_root / args.case_root.name / "output"
    download_outputs(args.base_url, project_id, out_dir, state)
    print(json.dumps({"case_id": args.case_root.name, "project_id": project_id, "status": state.get("status"), "output_dir": str(out_dir)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
