import os
import torch
from dotenv import load_dotenv
from pathlib import Path
from pinecone import Pinecone, ServerlessSpec

load_dotenv()

class Settings():
    #RAG CONFIG
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_TOKEN")
    LLM_MODEL = os.getenv("LLM_MODEL", "gemini-2.0-flash-exp")
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-base-en-v1.5")
    FAISS_INDEX_DIR = Path(os.getenv("FAISS_INDEX_DIR", "Backend/data/processed/"))
    CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 1000))
    CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 200))
    TOP_K = int(os.getenv("TOP_K", 4))
    #ELEVENLABS TTS CONFIG
    ELEVEN_API_KEY = os.getenv("ELEVEN_API_KEY")
    TTS_VOICE_ID: str = "21m00Tcm4TlvDq8ikWAM" 
    TTS_MODEL: str = "eleven_monolingual_v1"
    TTS_OUTPUT_FORMAT: str = "pcm_16000"
    TTS_OUTPUT_FORMAT_TWILIO: str = "ulaw_8000"
    #WEBRTC AUIO PROCESSING CONFIG
    VAD_AGGRESSIVE: int = 3
    SAMPLE_RATE:int  = 16000
    CHUNK_SIZE_MS: int = 30
    CHUNK_SIZE_BYTES = (SAMPLE_RATE * CHUNK_SIZE_MS // 1000) * 2
    #VOICE BUFFERING
    MIN_SPEECH_DURATION_S = 0.5
    END_OF_SPEECH_SILENCE_S = 0.75
    #WHISPER CONFIG
    WHISPER_MODEL = "base"
    WHISPER_DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
    WHISPER_COMPUTE_TYPE = "int8"
    #GOOGLE CALENDAR CONFIG
    GOOGLE_CREDENTIAL = os.getenv("GOOGLE_SERVICE_ACCOUNT_KEY_PATH", "service_account.json")
    CALENDAR_ID: str = os.getenv("CALENDAR_ID", "")




settings = Settings()
settings.FAISS_INDEX_DIR.mkdir(parents=True, exist_ok=True)