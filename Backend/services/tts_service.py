from elevenlabs import stream
from elevenlabs.client import ElevenLabs
import os


class TTSService:
    def __init__(self, api_key: str):
        print("Initializing TTS Elevenlabs")
        try:
            self.client = ElevenLabs(api_key=api_key)
            print("Elevenlabs initialized successfully")
        except Exception as e:
            print(f"Failed to initialize elevenlabs client: {e}")
            raise

    
    def stream_response(self, text: str, voice: str, model: str, output_format: str):
        """
        Generate Voice response audio from text.
        Return a generator that yield audio chunks.
        """

        if not text:
            return
        
        print("Streaming TTS for text: '{text}'")

        try:
            audio_stream = self.client.text_to_speech.stream(
                text=text,
                voice_id=voice,
                model_id=model,
                output_format=output_format
            )

            yield from audio_stream
        except Exception as e:
            print(f"Elevenlabs streaming errors: {e}")