from faster_whisper import WhisperModel
import os

import torch

model = WhisperModel("base", device="cuda" if torch.cuda.is_available() else "cpu")

def transcribe_audio(filepath: str):
    segments, info = model.transcribe(filepath, language="en")
    print("Detected language '%s' with probability %f" % (info.language, info.language_probability))
    text = " ".join([seg.text for seg in segments])
    return text.strip()