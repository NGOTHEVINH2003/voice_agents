import os
import sys
import io
from googleapiclient.http import MediaIoBaseDownload
import json
from datetime import datetime
from pathlib import Path

# Thêm project root vào sys.path để import package Backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from Backend.api.drive import get_drive_service, list_drive_files
from Backend.rag.ingest import ingest_documents_from_paths

# -------------------- Cấu hình đường dẫn --------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SNAPSHOT_PATH = os.path.join(BASE_DIR, "../../Backend/drive/data/last_snapshot.json")
LOG_FILE = os.path.join(BASE_DIR, "../../Backend/drive/logs/drive_changes.log")
LOCAL_DOC_DIR = Path(BASE_DIR) / "../../Backend/drive/data/docs"

# -------------------- Tạo file gốc nếu chưa có --------------------
def init_file(path, initial_content=None):
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            if isinstance(initial_content, list):
                json.dump(initial_content, f)
            elif isinstance(initial_content, str):
                f.write(initial_content)

init_file(SNAPSHOT_PATH, [])
init_file(LOG_FILE, f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Log file created.\n")

# -------------------- Hàm snapshot --------------------
def load_snapshot():
    with open(SNAPSHOT_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_snapshot(files):
    os.makedirs(os.path.dirname(SNAPSHOT_PATH), exist_ok=True)
    with open(SNAPSHOT_PATH, "w", encoding="utf-8") as f:
        json.dump(files, f, indent=2)

# -------------------- Hàm logging --------------------
def log_change(message):
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}\n")

def download_drive_file(file_id: str, dest_path: str):
    """
    Download file from Google Drive to local path.

    Args:
        file_id: str - ID của file trên Drive
        dest_path: str - đường dẫn local để lưu file
    """
    service = get_drive_service()

    # Tạo thư mục nếu chưa tồn tại
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)

    # Lấy metadata file (tên, MIME type)
    file_metadata = service.files().get(fileId=file_id, fields="name, mimeType").execute()
    request = service.files().get_media(fileId=file_id)

    # Download bằng MediaIoBaseDownload
    fh = io.FileIO(dest_path, "wb")
    downloader = MediaIoBaseDownload(fh, request)
    done = False

    while not done:
        status, done = downloader.next_chunk()
        # Tùy chọn in tiến trình
        print(f"Downloading {file_metadata['name']}: {int(status.progress() * 100)}%")

    fh.close()
    return {"status": "success", "file_name": file_metadata["name"], "path": dest_path}

def handle_file_changes(added_files, removed_files):
    LOCAL_DOC_DIR.mkdir(parents=True, exist_ok=True)

    # Xóa file cũ
    for f in removed_files:
        local_path = LOCAL_DOC_DIR / f["name"]
        if local_path.exists():
            local_path.unlink()
            log_change(f"Removed local file: {local_path}")

    # Download file mới
    downloaded_paths = []
    for f in added_files:
        local_path = LOCAL_DOC_DIR / f["name"]
        try:
            download_drive_file(file_id=f["id"], dest_path=str(local_path))
            downloaded_paths.append(str(local_path))
            log_change(f"Downloaded {f['name']} to {local_path}")
        except Exception as e:
            log_change(f"Failed to download {f['name']}: {e}")

    # Ingest tất cả file hiện có
    all_paths = [str(p) for p in LOCAL_DOC_DIR.iterdir() if p.is_file()]
    if all_paths:
        ingest_documents_from_paths(all_paths)
    else:
        log_change("No documents to ingest.")

# -------------------- Hàm detect thay đổi --------------------
def detect_file_changes():
    try:
        current_data = list_drive_files()
        current_files = current_data["files"]
    except Exception as e:
        log_change(f"Error listing files: {e}")
        return

    current_ids = {f["id"] for f in current_files}

    old_snapshot = load_snapshot()
    old_ids = {f["id"] for f in old_snapshot}

    added = current_ids - old_ids
    removed = old_ids - current_ids

    added = [f for f in current_files if f["id"] not in old_ids]
    removed = [f for f in old_snapshot if f["id"] not in current_ids]

    if added or removed:
        log_change(f"Changes detected: {len(added)} added, {len(removed)} removed")
        handle_file_changes(added, removed)
        save_snapshot(current_files)
    else:
        log_change("No change detected.")


# -------------------- Test nhanh --------------------
if __name__ == "__main__":
    detect_file_changes()
