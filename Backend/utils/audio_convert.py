import numpy as np
import soundfile as sf
from io import BytesIO

def mulaw_to_wav(mulaw_bytes: bytes, sample_rate=16000):
    """
    Chuyển Twilio μ-law (16kHz, 8-bit mono) → WAV PCM16 (BytesIO)
    """
    if not mulaw_bytes:
        raise ValueError("Empty μ-law input")

    # Giải mã μ-law
    mulaw = np.frombuffer(mulaw_bytes, dtype=np.uint8)
    mulaw = ~mulaw
    sign = ((mulaw & 0x80) >> 7)
    exponent = (mulaw & 0x70) >> 4
    mantissa = mulaw & 0x0F
    magnitude = ((mantissa << 4) + 8) << exponent
    pcm16 = ((magnitude - 132) * ((-1) ** sign)).astype(np.int16)

    # Ghi WAV vào bộ nhớ
    buf = BytesIO()
    sf.write(buf, pcm16, sample_rate, format='WAV', subtype='PCM_16')
    buf.seek(0)
    return buf
