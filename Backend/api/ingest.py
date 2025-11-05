from fastapi import APIRouter, UploadFile, File, Form
from typing import List
from Backend.rag.ingest import ingest_documents_from_paths
from typing import Optional
import shutil
import tempfile
from pathlib import Path

router = APIRouter(prefix="/ingest", tags=["Ingest"])

UPLOAD_DIR = Path("data")
UPLOAD_DIR.mkdir(exist_ok=True)

@router.post("/upload/")
async def upload_files(
    files: List[UploadFile] = File(...),
    folder: Optional[str] = Form(None)
):
    """
    Upload file → Ingest → Cleanup sau khi xong.
    Nếu không chọn folder, hệ thống tạo thư mục tạm (temp dir).
    """
    if folder:
        upload_dir = Path(folder)
        upload_dir.mkdir(parents=True, exist_ok=True)
        temp_folder = False
    else:
        upload_dir = Path(tempfile.mkdtemp(prefix="ingest_"))
        temp_folder = True

    saved_paths = []

    for f in files:
        dest = upload_dir / f.filename
        with open(dest, "wb") as out:
            content = await f.read()
            out.write(content)
        saved_paths.append(str(dest))

    try:
        ingest_documents_from_paths(saved_paths)
        status = {"status": "ok", "ingested_files": saved_paths}
    except Exception as e:
        status = {"status": "error", "message": str(e)}

    if temp_folder:
        try:
            shutil.rmtree(upload_dir)
        except Exception as e:
            print(f"[WARN] Cleanup failed: {e}")

    return status


@router.post("/from_folder/")
def ingest_folder(folder: str = Form(...), namespace: str = Form("default")):
    """
    Ingest existing folder on server (folder path)
    """
    p = Path(folder)
    if not p.exists() or not p.is_dir():
        return {"status": "error", "message": "Folder not found"}
    file_paths = [str(x) for x in p.iterdir() if x.is_file()]
    ingest_documents_from_paths(file_paths, namespace=namespace)
    return {"status": "ok", "files": file_paths}
