import os
from dotenv import load_dotenv
from pathlib import Path
from pinecone import Pinecone, ServerlessSpec

load_dotenv()

class Settings():
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_TOKEN")
    ELEVEN_API_KEY = os.getenv("ELEVEN_API_KEY")
    LLM_MODEL = os.getenv("LLM_MODEL", "gemini-2.0-flash-exp")
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-base-en-v1.5")
    FAISS_INDEX_DIR = Path(os.getenv("FAISS_INDEX_DIR", "Backend/data/processed/"))
    CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 1000))
    CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 200))
    TOP_K = int(os.getenv("TOP_K", 4))
    TTS_VOICE_ID: str = "21m00Tcm4TlvDq8ikWAM" 
    TTS_MODEL: str = "eleven_monolingual_v1"
    TTS_OUTPUT_FORMAT: str = "ulaw_8000"

settings = Settings()
settings.FAISS_INDEX_DIR.mkdir(parents=True, exist_ok=True)