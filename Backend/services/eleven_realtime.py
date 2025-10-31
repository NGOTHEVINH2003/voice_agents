from elevenlabs import ElevenLabs
from Backend.config import settings

ELEVEN_API_KEY = settings.ELEVEN_API_KEY

tts_client = ElevenLabs(api_key=ELEVEN_API_KEY)

def text_to_speech(text: str, voice="Rachel"):
    """Create audio from text"""
    audio_stream = tts_client.text_to_speech.convert(
        text=text,
        voice=voice,
        model_id="eleven_multilingual_v2"
    )
    return b"".join(audio_stream)