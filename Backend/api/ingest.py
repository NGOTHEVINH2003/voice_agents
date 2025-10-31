from fastapi import APIRouter, UploadFile, File, Form
from typing import List
from Backend.rag.ingest import ingest_documents_from_paths
from pathlib import Path
import shutil

router = APIRouter(prefix="/ingest", tags=["Ingest"])

UPLOAD_DIR = Path("data")
UPLOAD_DIR.mkdir(exist_ok=True)

@router.post("/upload/")
async def upload_files(files: List[UploadFile] = File(...), namespace: str = Form("default")):
    saved_paths = []
    for f in files:
        dest = UPLOAD_DIR / f.filename
        with open(dest, "wb") as out:
            content = await f.read()
            out.write(content)
        saved_paths.append(str(dest))
    # call ingestion pipeline
    ingest_documents_from_paths(saved_paths, namespace=namespace)
    return {"status": "ok", "ingested_files": [p for p in saved_paths], "namespace": namespace}

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
