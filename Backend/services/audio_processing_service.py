import torch
import webrtcvad
from Backend.config import settings

class AudioProcessingSerivce:
    def __init__(self, aggressiveness: int):
        print("initializing AudioProcessingService")
        try:
            self.vad = webrtcvad.Vad(aggressiveness)
            if settings.SAMPLE_RATE not in (8000, 16000, 32000, 48000):
                raise ValueError("VAD only support 8k, 16k, 32k, 48k sample rates.")
            if settings.CHUNK_SIZE_MS not in (10, 20, 30):
                raise ValueError("VAD only support 10, 20, 30 ms chunk size")
            print("VAD initialize successfully")
        except Exception as e:
            print(f"Problem occurred when initializing VAD Service: {e}")
            raise

    
    def is_speech(self, chunk: bytes)-> bool:
        """DETECT IF A 30MS AUDIO CHUNK CONTAINS SPEECH OR NOT.
           CHUNK MUST BE 16K PCM MONO"""
        
        if len(chunk) != settings.CHUNK_SIZE_BYTES:
            print(f"Warning: VAD received chunk of unexpected size: {len(chunk)}")
        try:
            return self.vad.is_speech(chunk, settings.SAMPLE_RATE)
        except Exception as e:
            print(f"VAD error: {e}")
            return False
    