import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

try:
    from Backend.api import ingest, chat, email, drive
except ImportError:
    print("CẢNH BÁO: Không thể import 'Backend.api'.")
    from fastapi import APIRouter
    ingest = chat = email = APIRouter()


from Backend.config import settings
from Backend.services.audio_processing_service import AudioProcessingSerivce
from Backend.services.whisper_service import Whisper_Service
from Backend.services.tts_service import TTSService
from Backend.services.agent_service import LangChainAgent
from Backend.services.calendar_service import GoogleCalendarService

from Backend.api.voice import create_voice_agent_router

app = FastAPI(title="AI Business Assistant - Advanced RAG (FAISS)")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

print("Initializing services...")
try:
    if not settings.ELEVEN_API_KEY:
        raise ValueError("ELEVEN_API_KEY environment variable not set.")
    if not settings.GOOGLE_API_KEY:
        raise ValueError("GOOGLE_API_KEY environment variable not set.")

    vad_service = AudioProcessingSerivce(aggressiveness=settings.VAD_AGGRESSIVE)

    transcription_service = Whisper_Service(
        model_name=settings.WHISPER_MODEL,
        device=settings.WHISPER_DEVICE,
        compute_type=settings.WHISPER_COMPUTE_TYPE
    )
    tts_service = TTSService(api_key=settings.ELEVEN_API_KEY)
    calendar_service = GoogleCalendarService(
        service_account_file=settings.GOOGLE_CREDENTIAL,
        calendar_id=settings.CALENDAR_ID
    )

    agent_service = LangChainAgent(google_api_key=settings.GOOGLE_API_KEY, calendar_service= calendar_service)
    print("All services initialized.")

    voice_router = create_voice_agent_router(
        vad_service=vad_service,
        transcription_service=transcription_service,
        tts_service=tts_service,
        agent_service=agent_service
    )
    
    app.include_router(voice_router, prefix="/agent", tags=["Voice Agent"])
    print("Voice Agent router included at /agent.")

except Exception as e:
    print(f"LỖI NGHIÊM TRỌNG khi khởi tạo dịch vụ Voice Agent: {e}")
    print("Endpoint /agent sẽ KHÔNG hoạt động.")



app.include_router(ingest.router, prefix="/api", tags=["RAG Ingest"])
app.include_router(chat.router, prefix="/api", tags=["RAG Chat"])
app.include_router(email.router, prefix="/api", tags=["RAG Email"])
app.include_router(drive.router, prefix="/api", tags=["RAG Drive"])


@app.get("/")
def root():
    """Chuyển hướng đến trang tài liệu API."""
    return RedirectResponse(url="/docs")


# --- Main Entry Point ---
if __name__ == "__main__":
    print("Starting FastAPI server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)

