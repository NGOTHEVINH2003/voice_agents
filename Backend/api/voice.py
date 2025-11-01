from fastapi import APIRouter, UploadFile, File
from Backend.services.whisper_service import transcribe_audio
from Backend.services.nlu_service import classify
import tempfile, os

router = APIRouter(prefix="/voice", tags=["Voice"])

@router.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    temp_dir = tempfile.gettempdir()
    temp_path = os.path.join(temp_dir, file.filename)

    with open(temp_path, "wb") as f:
        f.write(await file.read())

    text = transcribe_audio(temp_path)

    result = classify(text)

    return {
        "transcript": text,
        "intent": result["labels"][0],
        "confidence": result["scores"][0],
    }