import asyncio
import uuid
from fastapi import WebSocket, WebSocketDisconnect
from Backend.config import settings 
from Backend.services.audio_processing_service import AudioProcessingSerivce
from Backend.services.whisper_service import Whisper_Service
from Backend.services.tts_service import TTSService
from Backend.services.agent_service import LangChainAgent

class WebSocketManager:
    """
    Manages a single WebSocket connection and the voice-to-voice pipeline.
    """
    def __init__(self, websocket: WebSocket, vad_service, transcription_service, tts_service, agent_service):
        self.websocket = websocket
        self.vad_service = vad_service
        self.transcription_service = transcription_service
        self.tts_service = tts_service
        self.agent_service = agent_service
        
        self.session_id = str(uuid.uuid4())
        self.vad_buffer = bytearray()
        self.speech_buffer = bytearray()
        self.is_speaking = False
        self.silence_chunks = 0
        
        self.min_speech_bytes = int(settings.MIN_SPEECH_DURATION_S * settings.SAMPLE_RATE * 2)
        self.max_silence_chunks = int((settings.END_OF_SPEECH_SILENCE_S * 1000) / settings.CHUNK_SIZE_MS)

        print(f"WebSocketManager initialized for session: {self.session_id}")
        print(f"Min speech bytes: {self.min_speech_bytes}")
        print(f"Max silence chunks: {self.max_silence_chunks}")

    async def run(self):
        """Main loop to handle the WebSocket connection."""
        await self.websocket.accept()
        print(f"WebSocket connected for session: {self.session_id}")
        
        try:
            while True:
                data = await self.websocket.receive_bytes()
                await self.process_audio_chunk(data)
                
        except WebSocketDisconnect:
            print(f"WebSocket client disconnected: {self.session_id}")
        except Exception as e:
            print(f"An error occurred in WebSocketManager: {e}")
        finally:
            # Cleanup
            if self.websocket.client_state.name == "CONNECTED":
                await self.websocket.close()
            print(f"Connection closed for session: {self.session_id}")

    async def process_audio_chunk(self, data: bytes):
        """Processes a raw audio chunk from the client."""
        self.vad_buffer.extend(data)

        while len(self.vad_buffer) >= settings.CHUNK_SIZE_BYTES:
            chunk_30ms = self.vad_buffer[:settings.CHUNK_SIZE_BYTES]
            self.vad_buffer = self.vad_buffer[settings.CHUNK_SIZE_BYTES:]

            if self.vad_service.is_speech(chunk_30ms):
                if not self.is_speaking:
                    print("Speech started.")
                    self.is_speaking = True
                self.speech_buffer.extend(chunk_30ms)
                self.silence_chunks = 0
            
            elif self.is_speaking:
                self.speech_buffer.extend(chunk_30ms) 
                self.silence_chunks += 1
                
                if self.silence_chunks > self.max_silence_chunks:
                    print("End of speech detected.")
                    await self.process_end_of_speech()
                    self.is_speaking = False
                    self.silence_chunks = 0
            else:
                pass

    async def process_end_of_speech(self):
        """
        Called when end-of-speech is detected.
        Transcribes the buffer, gets an agent response, and streams TTS.
        """
        if len(self.speech_buffer) < self.min_speech_bytes:
            print(f"Speech too short, discarding. ({len(self.speech_buffer)} bytes)")
            self.speech_buffer = bytearray()
            return

        print(f"Processing audio buffer of size: {len(self.speech_buffer)}")
        

        buffer_to_process = self.speech_buffer
        self.speech_buffer = bytearray()
        
        transcribed_text = self.transcription_service.transcribe_audio(buffer_to_process)
        
        if not transcribed_text or transcribed_text.strip().lower() in ["you", "thank you.", "thanks.", "bye."]:
            print(f"Ignoring transcription: '{transcribed_text}'")
            return

        print(f"User said: {transcribed_text}")
        
        response_text = await self.agent_service.process_text(
            transcribed_text, self.session_id
        )
        
        if not response_text:
            print("Agent returned no response.")
            return

        print(f"Agent says: {response_text}")

        print("Streaming TTS response...")
        await self.stream_tts_to_client(response_text)
        print("TTS streaming complete.")

    async def stream_tts_to_client(self, text: str):
        """Streams the TTS audio back to the WebSocket client."""
        try:
            audio_stream = self.tts_service.stream_response(
                text=text,
                voice=settings.TTS_VOICE_ID,
                model=settings.TTS_MODEL,
                output_format=settings.TTS_OUTPUT_FORMAT
            )
            
            for chunk in audio_stream:
                if chunk:
                    await self.websocket.send_bytes(chunk)
        except Exception as e:
            print(f"Error streaming TTS to client: {e}")
