from faster_whisper import WhisperModel
import os
import numpy as np
import torch

class Whisper_Service:
    def __init__(self, model_name: str, device: str, compute_type:str):
        print(f"Loading whisper model: '{model_name} on {device}'..." )
        try:
            self.model = WhisperModel(model_name, device=device, compute_type=compute_type)
            print("Whisper model loaded successfully.")
        except Exception as e:
            print(f"Failed to load Whisper model: {e}")
            print("Ensure 'cuda' is available and drivers are installed if using GPU")
            raise

    def transcribe_audio(self, audio_buffer: bytearray) -> str:
        """Transcribe byte array of 16-bit PCM audio.
           Return transcribed text"""
        
        # if no audio -> return empty
        if not audio_buffer:
            return ""
        
        print(f"Transcribing audio buffer of size: {len(audio_buffer)} bytes")

        audio_np = np.frombuffer(audio_buffer, dtype=np.int16).astype(np.float32) / 32768.0

        try:
            segments, _ = self.model.transcribe(
                audio_np,
                beam_size= 5,
                language= "en"
            )

            transcribed_text = " ".join([seg.text for seg in segments])
            print(f"Transcription complete. Language: {_.language}, Prob: {_.language_probability}")
            print(f"Transcription Text: {transcribed_text}")
            return transcribed_text
        except Exception as e:
            print(f"Whisper transciption error: {e}")
            print("Error Location: Whisper_service.py")
            return ""
        

    
        