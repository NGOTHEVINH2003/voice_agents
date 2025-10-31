import numpy as np

def mulaw_to_pcm16_numpy(mulaw_bytes: bytearray) -> np.ndarray:
    """
    Converts 8-bit mulaw audio bytes to a 16-bit linear PCM numpy array.
    This replaces the deprecated audioop.ulaw2lin(data, 2).
    
    Vectorized implementation for speed.
    """
    # 1. Convert bytearray to numpy array of uint8
    mulaw_array = np.frombuffer(mulaw_bytes, dtype=np.uint8)
    
    # 2. Mu-law to PCM16 conversion (G.711 standard)
    BIAS = 0x84  # 132
    
    # Invert bits
    t = ~mulaw_array & 0xFF
    
    # Extract sign, exponent, and mantissa
    sign = (t & 0x80)
    exponent = (t & 0x70) >> 4
    mantissa = (t & 0x0F)
    
    # Calculate PCM magnitude
    pcm_magnitude = ((mantissa << 3) + BIAS) << exponent
    
    # Apply bias and sign to get 16-bit PCM
    # We use np.where for efficient conditional logic
    pcm_array = np.where(sign == 0, pcm_magnitude - BIAS, BIAS - pcm_magnitude)
    
    # Return as int16 array
    return pcm_array.astype(np.int16)
