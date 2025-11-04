from fastapi import APIRouter, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from Backend.services.audio_processing_service import AudioProcessingSerivce
from Backend.services.whisper_service import Whisper_Service
from Backend.services.tts_service import TTSService
from Backend.services.agent_service import LangChainAgent
from Backend.services.WebsocketConnection_Manager import WebSocketManager

def create_voice_agent_router(
    vad_service: AudioProcessingSerivce,
    transcription_service: Whisper_Service,
    tts_service: TTSService,
    agent_service: LangChainAgent
) -> APIRouter:
    """
    Tạo ra một APIRouter chứa tất cả các endpoint cho
    dịch vụ voice agent (WebSocket, static files).
    """
    router = APIRouter()

    @router.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        """
        Main WebSocket endpoint cho voice-to-voice agent.
        Tạo một manager cho mỗi kết nối.
        """
        manager = WebSocketManager(
            websocket=websocket,
            vad_service=vad_service,
            transcription_service=transcription_service,
            tts_service=tts_service,
            agent_service=agent_service
        )

        print("socket actually connect")
        await manager.run()

    @router.get("/")
    async def get_root():
        """Phục vụ file HTML frontend chính."""
        return FileResponse("Backend/static/index.html")

    router.mount("/", StaticFiles(directory="Backend/static"), name="static_agent")

    return router   
