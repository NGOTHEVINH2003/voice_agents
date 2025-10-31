from faster_whisper import WhisperModel
import tempfile

model = WhisperModel("base", device="cpu", compute_type="int8")

def transcribe_audio(audio_bytes: bytes)->str:
    """Convert audio bytes to text for rag"""
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        f.write(audio_bytes)
        tmp_path = f.name
    segments,_ = model.transcribe(tmp_path)
    text = " ".join([s.text for s in segments]).strip()
    return text