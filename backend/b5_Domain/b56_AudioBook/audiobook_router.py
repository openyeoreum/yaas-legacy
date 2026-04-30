import asyncio
import json
import mimetypes
import os
import re
import subprocess
import sys
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse, StreamingResponse


audiobook_router = APIRouter(prefix="/api/audiobook", tags=["audiobook"])

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_STORAGE_ROOT = Path("/yaas/storage/s1_Yeoreum/s12_UserStorage/s123_Storage")
LOCAL_STORAGE_ROOT = REPO_ROOT / "storage-legacy/s1_Yeoreum/s12_UserStorage/s123_Storage"
AUDIO_EXTENSIONS = {".wav", ".mp3", ".m4a", ".aac", ".flac", ".ogg"}
RUNNING_JOBS: dict[str, subprocess.Popen] = {}


def now_text() -> str:
    return datetime.now().strftime("%Y%m%d%H%M%S")


def storage_root() -> Path:
    configured = os.getenv("YAAS_STORAGE_ROOT")
    if configured:
        return Path(configured).expanduser().resolve()
    if DEFAULT_STORAGE_ROOT.exists():
        return DEFAULT_STORAGE_ROOT.resolve()
    return LOCAL_STORAGE_ROOT.resolve()


def asset_root() -> Path:
    configured = os.getenv("YAAS_ASSET_ROOT")
    if configured:
        return Path(configured).expanduser().resolve()
    root = storage_root()
    if root.name == "s123_Storage":
        return root.parents[1].resolve()
    local = REPO_ROOT / "storage-legacy/s1_Yeoreum"
    return local.resolve()


def validate_segment(value: str, label: str) -> str:
    if not value or "/" in value or "\\" in value or value in {".", ".."} or ".." in value:
        raise HTTPException(status_code=400, detail=f"Invalid {label}")
    return value


def safe_project_path(email: str, project: str) -> Path:
    email = validate_segment(email, "email")
    project = validate_segment(project, "project")
    root = storage_root()
    path = (root / email / project).resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Project path escapes storage root") from exc
    if not path.exists():
        raise HTTPException(status_code=404, detail="Project not found")
    return path


def rel_path(path: Path, base: Path) -> str:
    return path.resolve().relative_to(base.resolve()).as_posix()


def read_json_file(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def atomic_write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        backup = path.with_name(f"{path.name}.{now_text()}.bak")
        backup.write_bytes(path.read_bytes())
    temp = path.with_name(f"{path.name}.{now_text()}.tmp")
    with temp.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)
        file.write("\n")
    os.replace(temp, path)


def config_path(project_dir: Path, project: str) -> Path:
    return project_dir / f"{project}_config.json"


def audiobook_root(project_dir: Path, project: str) -> Path:
    return project_dir / f"{project}_audiobook"


def master_root(project_dir: Path, project: str) -> Path:
    return audiobook_root(project_dir, project) / f"{project}_master_audiobook_file"


def mixed_root(project_dir: Path, project: str) -> Path:
    return audiobook_root(project_dir, project) / f"{project}_mixed_audiobook_file"


def voice_root(project_dir: Path, project: str) -> Path:
    return mixed_root(project_dir, project) / "VoiceLayers"


def music_root(project_dir: Path, project: str) -> Path:
    return mixed_root(project_dir, project) / "MusicLayers" / "Music1"


def edit_json_path(project_dir: Path, project: str) -> Path:
    candidates = [
        master_root(project_dir, project) / f"[{project}_AudioBook_Edit].json",
        master_root(project_dir, project) / f"[{project}_Audiobook_Edit].json",
        master_root(project_dir, project) / f"{project}_AudioBook_Edit.json",
        master_root(project_dir, project) / f"{project}_Audiobook_Edit.json",
    ]
    for path in candidates:
        if path.exists():
            return path
    return candidates[0]


def voices_json_path(project_dir: Path, project: str) -> Path:
    return voice_root(project_dir, project) / f"{project}_MatchedVoices.json"


def musics_json_path(project_dir: Path, project: str) -> Path:
    candidates = [
        music_root(project_dir, project) / f"[{project}_MatchedMusics].json",
        music_root(project_dir, project) / f"{project}_MatchedMusics.json",
    ]
    for path in candidates:
        if path.exists():
            return path
    return candidates[0]


def inspection_sidecar_path(project_dir: Path, project: str) -> Path:
    return master_root(project_dir, project) / ".yaas_inspection_overrides.json"


def lock_path(project_dir: Path) -> Path:
    return project_dir / ".yaas_audio_job.lock"


def stop_request_path(project_dir: Path) -> Path:
    return project_dir / ".yaas_stop_requested"


def log_dir(project_dir: Path) -> Path:
    return project_dir / ".yaas_workspace_logs"


def is_pid_alive(pid: Optional[int]) -> bool:
    if not pid:
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def read_lock(project_dir: Path) -> dict[str, Any]:
    path = lock_path(project_dir)
    data = read_json_file(path, {}) or {}
    pid = data.get("pid")
    active_status = data.get("status") in {"running", "stopping"}
    running = active_status and is_pid_alive(pid)
    if active_status and not running:
        data = {**data, "status": "stale", "running": False}
    else:
        data = {**data, "running": running}
    data["exists"] = path.exists()
    return data


def is_project_locked(project_dir: Path) -> bool:
    return bool(read_lock(project_dir).get("running"))


def require_unlocked(project_dir: Path) -> None:
    if is_project_locked(project_dir):
        raise HTTPException(status_code=423, detail="Audio generation is running; editing is locked")


def scan_audio_files(base: Path, project_dir: Path, recursive: bool = True) -> list[dict[str, Any]]:
    if not base.exists():
        return []
    iterator = base.rglob("*") if recursive else base.glob("*")
    files = []
    for path in iterator:
        if path.is_file() and path.suffix.lower() in AUDIO_EXTENSIONS:
            stat = path.stat()
            files.append({
                "name": path.name,
                "path": rel_path(path, project_dir),
                "size": stat.st_size,
                "updatedAt": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            })
    return sorted(files, key=lambda item: item["name"])


def latest_modified_folder(project_dir: Path, project: str) -> Optional[Path]:
    base = master_root(project_dir, project) / f"[{project}_Modified]"
    if not base.exists():
        return None
    folders = [p for p in base.iterdir() if p.is_dir() and re.search(r"\d{14}_Modified_Part$", p.name)]
    return max(folders, key=lambda p: p.name) if folders else None


def clean_chunk_text(value: str) -> str:
    text = str(value or "").strip()
    if text.startswith("[") and text.endswith("]"):
        text = text[1:-1].strip()
    return re.sub(r"\s+", " ", text)


def edit_id_text(edit_id: Any) -> str:
    if isinstance(edit_id, float) and edit_id.is_integer():
        return str(int(edit_id))
    return str(edit_id)


def find_chunk_audio(project_dir: Path, project: str, edit_id: Any, actor: str, index: int) -> Optional[str]:
    root = voice_root(project_dir, project)
    if not root.exists():
        return None
    edit_text = edit_id_text(edit_id)
    stems = [
        f"{project}_{edit_text}_{actor}_({index})M",
        f"{project}_{edit_text}_{actor}_({index})",
    ]
    if index == 0:
        stems.extend([
            f"{project}_{edit_text}_{actor}M",
            f"{project}_{edit_text}_{actor}",
        ])
    for stem in stems:
        for ext in AUDIO_EXTENSIONS:
            candidate = root / f"{stem}{ext}"
            if candidate.exists():
                return rel_path(candidate, project_dir)
    prefix = f"{project}_{edit_text}_{actor}"
    matches = [p for p in root.glob(f"{prefix}*") if p.is_file() and p.suffix.lower() in AUDIO_EXTENSIONS]
    if not matches:
        return None
    indexed = [p for p in matches if f"_({index})" in p.stem]
    selected = sorted(indexed or matches, key=lambda p: ("M" not in p.stem, p.name))[0]
    return rel_path(selected, project_dir)


def find_modified_audio(project_dir: Path, project: str, edit_id: Any, actor: str, index: int) -> Optional[str]:
    latest = latest_modified_folder(project_dir, project)
    if not latest:
        return None
    edit_text = edit_id_text(edit_id)
    prefix = f"{project}_{edit_text}_{actor}_({index})Modify"
    matches = [p for p in latest.glob(f"{prefix}*") if p.is_file() and p.suffix.lower() in AUDIO_EXTENSIONS]
    if not matches:
        return None
    return rel_path(sorted(matches, key=lambda p: p.name)[0], project_dir)


def voice_audio_lookup(project_dir: Path, project: str) -> dict[tuple[str, str, int], str]:
    root = voice_root(project_dir, project)
    lookup: dict[tuple[str, str, int], tuple[int, str]] = {}
    if not root.exists():
        return {}
    prefix = f"{project}_"
    for path in root.glob("*"):
        if not path.is_file() or path.suffix.lower() not in AUDIO_EXTENSIONS or not path.stem.startswith(prefix):
            continue
        remainder = path.stem[len(prefix):]
        if "_" not in remainder:
            continue
        edit_text, tail = remainder.split("_", 1)
        priority = 1
        if tail.endswith("M"):
            tail = tail[:-1]
            priority = 0
        chunk_index = 0
        match = re.search(r"_\((\d+)\)$", tail)
        if match:
            chunk_index = int(match.group(1))
            actor = tail[:match.start()]
        else:
            actor = tail
        key = (edit_text, actor, chunk_index)
        value = (priority, rel_path(path, project_dir))
        if key not in lookup or value[0] < lookup[key][0]:
            lookup[key] = value
    return {key: value[1] for key, value in lookup.items()}


def modified_audio_lookup(project_dir: Path, project: str) -> dict[tuple[str, str, int], str]:
    latest = latest_modified_folder(project_dir, project)
    lookup: dict[tuple[str, str, int], str] = {}
    if not latest:
        return lookup
    prefix = f"{project}_"
    for path in latest.glob("*"):
        if not path.is_file() or path.suffix.lower() not in AUDIO_EXTENSIONS or not path.stem.startswith(prefix):
            continue
        remainder = path.stem[len(prefix):]
        if "_" not in remainder or not remainder.endswith("Modify"):
            continue
        edit_text, tail = remainder.split("_", 1)
        tail = tail[:-len("Modify")]
        match = re.search(r"_\((\d+)\)$", tail)
        if not match:
            continue
        chunk_index = int(match.group(1))
        actor = tail[:match.start()]
        lookup[(edit_text, actor, chunk_index)] = rel_path(path, project_dir)
    return lookup


def load_inspection_overrides(path: Path) -> dict[str, dict[str, Any]]:
    payload = read_json_file(path, {}) or {}
    if isinstance(payload, dict) and isinstance(payload.get("items"), dict):
        return payload["items"]
    if isinstance(payload, dict) and isinstance(payload.get("분할검수"), list):
        return {str(item.get("id") or item.get("문장번호")): item for item in payload["분할검수"]}
    return {}


def build_inspection(project_dir: Path, project: str) -> dict[str, Any]:
    edit_path = edit_json_path(project_dir, project)
    edit_data = read_json_file(edit_path, []) or []
    overrides = load_inspection_overrides(inspection_sidecar_path(project_dir, project))
    voice_lookup = voice_audio_lookup(project_dir, project)
    modified_lookup = modified_audio_lookup(project_dir, project)
    items = []
    sentence_number = 0
    for edit in edit_data if isinstance(edit_data, list) else []:
        chunks = edit.get("ActorChunk", [])
        for index, chunk in enumerate(chunks if isinstance(chunks, list) else []):
            chunk_key = "ModifiedChunk" if "ModifiedChunk" in chunk else "Chunk"
            raw_chunk = chunk.get(chunk_key, "")
            edit_id = edit.get("EditId")
            actor = edit.get("ActorName", "")
            item_id = f"{edit_id}:{index}"
            override = overrides.get(item_id, {})
            lookup_key = (edit_id_text(edit_id), actor, index)
            modified_audio = modified_lookup.get(lookup_key)
            audio_path = voice_lookup.get(lookup_key) or modified_audio
            items.append({
                "id": item_id,
                "문장번호": sentence_number,
                "editId": edit_id,
                "chunkIndex": index,
                "tag": edit.get("Tag", ""),
                "actorName": actor,
                "sourceKey": chunk_key,
                "rawChunk": raw_chunk,
                "분할지정문장": clean_chunk_text(raw_chunk),
                "분할파일STT": override.get("분할파일STT", ""),
                "판정": override.get("판정", "보류"),
                "이유": override.get("이유", ""),
                "메모": override.get("메모", ""),
                "audioPath": audio_path,
                "modifiedAudioPath": modified_audio,
                "hasModifiedChunk": chunk_key == "ModifiedChunk" or bool(modified_audio),
            })
            sentence_number += 1
    return {
        "path": str(edit_path),
        "items": items,
        "overrides": overrides,
    }


def project_summary(email_dir: Path, project_dir: Path) -> dict[str, Any]:
    project = project_dir.name
    stat = project_dir.stat()
    audio_root = audiobook_root(project_dir, project)
    return {
        "email": email_dir.name,
        "project": project,
        "path": str(project_dir),
        "hasAudiobook": audio_root.exists(),
        "updatedAt": datetime.fromtimestamp(stat.st_mtime).isoformat(),
    }


@audiobook_router.get("/projects")
def list_projects() -> dict[str, Any]:
    root = storage_root()
    if not root.exists():
        return {"storageRoot": str(root), "projects": []}
    projects = []
    for email_dir in sorted([p for p in root.iterdir() if p.is_dir()], key=lambda p: p.name):
        for project_dir in sorted([p for p in email_dir.iterdir() if p.is_dir()], key=lambda p: p.name):
            projects.append(project_summary(email_dir, project_dir))
    return {"storageRoot": str(root), "projects": projects}


@audiobook_router.get("/assets/voices")
def list_voice_assets() -> dict[str, Any]:
    dataset = REPO_ROOT / "agent/a2_Database/a27_RelationalDatabase/a272_Character/a272-01_VoiceDataSet.json"
    raw = read_json_file(dataset, []) or []
    characters = []
    for block in raw if isinstance(raw, list) else []:
        if isinstance(block, dict) and isinstance(block.get("Characters"), list):
            characters.extend(block["Characters"])
    return {"path": str(dataset), "voices": characters}


@audiobook_router.get("/assets/musics")
def list_music_assets() -> dict[str, Any]:
    base = asset_root() / "s18_AudioBookStorage"
    items = []
    if base.exists():
        for path in base.rglob("*"):
            if path.is_file() and path.suffix.lower() in AUDIO_EXTENSIONS:
                items.append({
                    "name": path.name,
                    "path": str(path),
                    "category": path.parent.name,
                    "relativePath": path.relative_to(base).as_posix(),
                })
    return {"path": str(base), "musics": sorted(items, key=lambda item: item["relativePath"])}


@audiobook_router.get("/{email}/{project}/state")
def project_state(email: str, project: str) -> dict[str, Any]:
    project_dir = safe_project_path(email, project)
    edit_data = read_json_file(edit_json_path(project_dir, project), []) or []
    inspection = build_inspection(project_dir, project)
    latest_modified = latest_modified_folder(project_dir, project)
    master_audio = [
        item for item in scan_audio_files(master_root(project_dir, project), project_dir, recursive=False)
        if "Modified" not in item["path"]
    ]
    voice_audio = scan_audio_files(voice_root(project_dir, project), project_dir)
    modified_audio = scan_audio_files(latest_modified, project_dir) if latest_modified else []
    return {
        "email": email,
        "project": project,
        "projectPath": str(project_dir),
        "storageRoot": str(storage_root()),
        "lock": read_lock(project_dir),
        "paths": {
            "config": str(config_path(project_dir, project)),
            "edit": str(edit_json_path(project_dir, project)),
            "voices": str(voices_json_path(project_dir, project)),
            "musics": str(musics_json_path(project_dir, project)),
            "inspectionSidecar": str(inspection_sidecar_path(project_dir, project)),
        },
        "counts": {
            "edits": len(edit_data) if isinstance(edit_data, list) else 0,
            "chunks": len(inspection["items"]),
            "modifiedChunks": len([item for item in inspection["items"] if item["hasModifiedChunk"]]),
            "regeneration": len([item for item in inspection["items"] if item["판정"] == "재생성"]),
            "voiceAudio": len(voice_audio),
            "modifiedAudio": len(modified_audio),
            "masterAudio": len(master_audio),
        },
        "latestModifiedFolder": str(latest_modified) if latest_modified else None,
        "audio": {
            "voice": voice_audio,
            "modified": modified_audio,
            "master": master_audio,
        },
    }


@audiobook_router.get("/{email}/{project}/edit")
def get_edit(email: str, project: str) -> dict[str, Any]:
    project_dir = safe_project_path(email, project)
    path = edit_json_path(project_dir, project)
    return {"path": str(path), "exists": path.exists(), "locked": is_project_locked(project_dir), "data": read_json_file(path, []) or []}


@audiobook_router.put("/{email}/{project}/edit")
async def put_edit(email: str, project: str, request: Request) -> dict[str, Any]:
    project_dir = safe_project_path(email, project)
    require_unlocked(project_dir)
    body = await request.json()
    data = body.get("data", body) if isinstance(body, dict) else body
    path = edit_json_path(project_dir, project)
    atomic_write_json(path, data)
    return {"ok": True, "path": str(path)}


@audiobook_router.get("/{email}/{project}/voices")
def get_voices(email: str, project: str) -> dict[str, Any]:
    project_dir = safe_project_path(email, project)
    path = voices_json_path(project_dir, project)
    return {"path": str(path), "exists": path.exists(), "locked": is_project_locked(project_dir), "data": read_json_file(path, []) or []}


@audiobook_router.put("/{email}/{project}/voices")
async def put_voices(email: str, project: str, request: Request) -> dict[str, Any]:
    project_dir = safe_project_path(email, project)
    require_unlocked(project_dir)
    body = await request.json()
    data = body.get("data", body) if isinstance(body, dict) else body
    path = voices_json_path(project_dir, project)
    atomic_write_json(path, data)
    return {"ok": True, "path": str(path)}


@audiobook_router.get("/{email}/{project}/musics")
def get_musics(email: str, project: str) -> dict[str, Any]:
    project_dir = safe_project_path(email, project)
    path = musics_json_path(project_dir, project)
    return {"path": str(path), "exists": path.exists(), "locked": is_project_locked(project_dir), "data": read_json_file(path, []) or []}


@audiobook_router.put("/{email}/{project}/musics")
async def put_musics(email: str, project: str, request: Request) -> dict[str, Any]:
    project_dir = safe_project_path(email, project)
    require_unlocked(project_dir)
    body = await request.json()
    data = body.get("data", body) if isinstance(body, dict) else body
    path = musics_json_path(project_dir, project)
    atomic_write_json(path, data)
    return {"ok": True, "path": str(path)}


@audiobook_router.get("/{email}/{project}/config")
def get_config(email: str, project: str) -> dict[str, Any]:
    project_dir = safe_project_path(email, project)
    path = config_path(project_dir, project)
    return {"path": str(path), "exists": path.exists(), "locked": is_project_locked(project_dir), "data": read_json_file(path, {}) or {}}


@audiobook_router.put("/{email}/{project}/config")
async def put_config(email: str, project: str, request: Request) -> dict[str, Any]:
    project_dir = safe_project_path(email, project)
    require_unlocked(project_dir)
    body = await request.json()
    data = body.get("data", body) if isinstance(body, dict) else body
    path = config_path(project_dir, project)
    atomic_write_json(path, data)
    return {"ok": True, "path": str(path)}


@audiobook_router.get("/{email}/{project}/inspection")
def get_inspection(email: str, project: str) -> dict[str, Any]:
    project_dir = safe_project_path(email, project)
    payload = build_inspection(project_dir, project)
    return {"locked": is_project_locked(project_dir), **payload}


@audiobook_router.put("/{email}/{project}/inspection")
async def put_inspection(email: str, project: str, request: Request) -> dict[str, Any]:
    project_dir = safe_project_path(email, project)
    body = await request.json()
    items = body.get("items", body.get("분할검수", [])) if isinstance(body, dict) else body
    if not isinstance(items, list):
        raise HTTPException(status_code=400, detail="Inspection body must contain an items list")
    mapped = {}
    for item in items:
        item_id = str(item.get("id") or item.get("문장번호", ""))
        if item_id:
            mapped[item_id] = {
                "판정": item.get("판정", "보류"),
                "이유": item.get("이유", ""),
                "메모": item.get("메모", ""),
                "분할파일STT": item.get("분할파일STT", ""),
            }
    path = inspection_sidecar_path(project_dir, project)
    atomic_write_json(path, {"updatedAt": datetime.now().isoformat(), "items": mapped})
    return {"ok": True, "path": str(path), "count": len(mapped)}


@audiobook_router.get("/{email}/{project}/audio")
def get_audio(email: str, project: str, path: str) -> FileResponse:
    project_dir = safe_project_path(email, project)
    target = (project_dir / path).resolve()
    try:
        target.relative_to(project_dir.resolve())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Audio path escapes project root") from exc
    if not target.exists() or target.suffix.lower() not in AUDIO_EXTENSIONS:
        raise HTTPException(status_code=404, detail="Audio file not found")
    media_type = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
    return FileResponse(target, media_type=media_type, filename=target.name)


def process_key(email: str, project: str) -> str:
    return f"{email}/{project}"


def monitor_process(project_dir: Path, process: subprocess.Popen, log_path_value: Path) -> None:
    return_code = process.wait()
    current = read_json_file(lock_path(project_dir), {}) or {}
    stopped_by_user = current.get("status") in {"stopping", "stopped"}
    current.update({
        "status": "stopped" if stopped_by_user else ("completed" if return_code == 0 else "failed"),
        "running": False,
        "returnCode": return_code,
        "endedAt": datetime.now().isoformat(),
        "logPath": str(log_path_value),
    })
    atomic_write_json(lock_path(project_dir), current)


@audiobook_router.post("/{email}/{project}/run")
async def run_project(email: str, project: str, request: Request) -> dict[str, Any]:
    project_dir = safe_project_path(email, project)
    if is_project_locked(project_dir):
        raise HTTPException(status_code=423, detail="Audio generation is already running")
    body = await request.json() if request.headers.get("content-type", "").startswith("application/json") else {}
    account = body.get("account") or read_json_file(config_path(project_dir, project), {}).get("account") or "kka6887@naver.com"
    messages_review = body.get("messagesReview", "on")
    logs = log_dir(project_dir)
    logs.mkdir(parents=True, exist_ok=True)
    log_path_value = logs / f"{now_text()}_yaas.log"
    stop_path_value = stop_request_path(project_dir)
    if stop_path_value.exists():
        stop_path_value.unlink()
    script = (
        "import sys\n"
        "from agent.YaaS import YaaSCore\n"
        "email, project, account, messages_review = sys.argv[1:5]\n"
        "YaaSCore(email, project, 'Ko', [], [], {'Search':'', 'Intention':'Similarity', 'Collection':'Book'}, "
        "'', '', '', 'Auto', [], messages_review, account)\n"
    )
    env = os.environ.copy()
    env["PYTHONPATH"] = f"{REPO_ROOT}:{env.get('PYTHONPATH', '')}"
    env["YAAS_STOP_REQUEST_PATH"] = str(stop_path_value)
    with log_path_value.open("ab") as log_file:
        process = subprocess.Popen(
            [sys.executable, "-u", "-c", script, email, project, account, messages_review],
            cwd=str(REPO_ROOT),
            stdout=log_file,
            stderr=subprocess.STDOUT,
            env=env,
            start_new_session=True,
        )
    key = process_key(email, project)
    RUNNING_JOBS[key] = process
    lock_payload = {
        "status": "running",
        "running": True,
        "pid": process.pid,
        "email": email,
        "project": project,
        "account": account,
        "messagesReview": messages_review,
        "startedAt": datetime.now().isoformat(),
        "logPath": str(log_path_value),
    }
    atomic_write_json(lock_path(project_dir), lock_payload)
    thread = threading.Thread(target=monitor_process, args=(project_dir, process, log_path_value), daemon=True)
    thread.start()
    return {"ok": True, "pid": process.pid, "logPath": str(log_path_value)}


@audiobook_router.post("/{email}/{project}/stop")
def stop_project(email: str, project: str) -> dict[str, Any]:
    project_dir = safe_project_path(email, project)
    current = read_lock(project_dir)
    key = process_key(email, project)
    process = RUNNING_JOBS.get(key)
    pid = process.pid if process and process.poll() is None else current.get("pid")
    if not pid or not is_pid_alive(pid):
        current.update({
            "status": "stopped",
            "running": False,
            "endedAt": datetime.now().isoformat(),
        })
        atomic_write_json(lock_path(project_dir), current)
        return {"ok": True, "running": False, "signals": [], "lock": current}

    stop_payload = {
        "requestedAt": datetime.now().isoformat(),
        "pid": pid,
        "mode": "graceful-after-current-edit",
    }
    atomic_write_json(stop_request_path(project_dir), stop_payload)
    current.update({
        "status": "stopping",
        "running": True,
        "stopRequestedAt": datetime.now().isoformat(),
        "stopMode": "graceful-after-current-edit",
    })
    atomic_write_json(lock_path(project_dir), current)
    running = is_pid_alive(int(pid))
    updated = read_json_file(lock_path(project_dir), {}) or current
    updated.update({
        "status": "stopping" if running else "stopped",
        "running": running,
        "stopSignals": [],
        "stopCheckedAt": datetime.now().isoformat(),
    })
    if not running:
        updated["endedAt"] = datetime.now().isoformat()
    atomic_write_json(lock_path(project_dir), updated)
    return {"ok": True, "running": running, "signals": [], "lock": updated}


@audiobook_router.get("/{email}/{project}/logs/stream")
async def stream_logs(email: str, project: str):
    project_dir = safe_project_path(email, project)
    lock = read_lock(project_dir)
    log_path_value = Path(lock.get("logPath", "")) if lock.get("logPath") else None

    async def events():
        offset = 0
        idle_after_done = 0
        while True:
            if log_path_value and log_path_value.exists():
                with log_path_value.open("r", encoding="utf-8", errors="replace") as file:
                    file.seek(offset)
                    chunk = file.read()
                    offset = file.tell()
                if chunk:
                    for line in chunk.splitlines():
                        yield f"data: {line}\n\n"
                    idle_after_done = 0
            current = read_lock(project_dir)
            if not current.get("running"):
                idle_after_done += 1
                if idle_after_done >= 2:
                    yield "event: done\ndata: done\n\n"
                    break
            await asyncio.sleep(1)

    return StreamingResponse(events(), media_type="text/event-stream")


@audiobook_router.post("/{email}/{project}/lock/release")
def release_lock(email: str, project: str) -> dict[str, Any]:
    project_dir = safe_project_path(email, project)
    current = read_json_file(lock_path(project_dir), {}) or {}
    current.update({
        "status": "released",
        "running": False,
        "releasedAt": datetime.now().isoformat(),
    })
    atomic_write_json(lock_path(project_dir), current)
    return {"ok": True, "lock": current}
