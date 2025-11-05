from fastapi import APIRouter, HTTPException
from googleapiclient.discovery import build
from google.oauth2 import service_account
import os

router = APIRouter(prefix="/drive", tags=["Drive"])

# Load credentials
SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_DRIVE_SERVICE_ACCOUNT", "service_account.json")
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

# Kết nối Google Drive
def get_drive_service():
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    return build("drive", "v3", credentials=creds)

@router.get("/files")
def list_drive_files():
    """Lấy danh sách file trong Google Drive"""
    service = get_drive_service()

    query = "mimeType != 'application/vnd.google-apps.folder' and trashed = false"

    results = service.files().list(
        q=query,
        pageSize=10,
        fields="files(id, name, mimeType, modifiedTime)"
    ).execute()
    files = results.get("files", [])

    return {"count": len(files), "files": files}