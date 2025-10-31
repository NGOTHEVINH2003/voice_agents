# Backend/api/ws_voice.py
from fastapi import APIRouter, WebSocket, Response
import json, base64
from Backend.services.whisper_service import transcribe_audio
from Backend.services.rag_service import query_rag
from Backend.services.eleven_realtime import text_to_speech
from Backend.utils.audio_convert import mulaw_to_wav

router = APIRouter(prefix="/ws", tags=["voice"])

@router.post("/twilio-webhook")
async def twilio_webhook():
    xml_response = """
    <Response>
      <Connect>
        <Stream url="wss://1776ea7e5abc.ngrok-free.app/ws/voice"/>
      </Connect>
    </Response>
    """
    return Response(content=xml_response, media_type="text/xml")

@router.websocket("/voice")
async def ws_voice_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("🎧 Voice WebSocket connected")
    audio_buffer = bytearray()

    print("CHECK 1 COMPLETE")

    try:
        while True:
            msg = await websocket.receive_text()
            data = json.loads(msg)
            event = data.get("event")
            print("CHECK 2 COMPLETE")
            if event == "media":
                audio_b64 = data["media"]["payload"]
                audio_bytes = base64.b64decode(audio_b64)
                audio_buffer.extend(audio_bytes)

                # xử lý mỗi khối ~1s
                if len(audio_buffer) > 16000:
                    mulaw_bytes = bytes(audio_buffer)
                    audio_buffer.clear()
                    print("CHECK 3 COMPLETE")
                    wav_bytes = mulaw_to_wav(mulaw_bytes)
                    # 1️⃣ Whisper STT

                    print("CHECK 4 COMPLETE")
                    text = transcribe_audio(wav_bytes)

                    print("CHECK 5 COMPLETE")
                    if not text.strip():
                        continue
                    print(f"👤 User: {text}")

                    # 2️⃣ RAG (Gemini)
                    answer = query_rag(text)
                    print(f"🤖 AI: {answer}")

                    # 3️⃣ ElevenLabs TTS
                    reply_audio = text_to_speech(answer)
                    reply_b64 = base64.b64encode(reply_audio).decode("utf-8")

                    # 4️⃣ Gửi lại audio
                    await websocket.send_text(json.dumps({
                        "event": "media",
                        "media": {"payload": reply_b64}
                    }))

    except Exception as e:
        print("❌ Voice WS error:", e)
    finally:
        await websocket.close()
        print("🔌 WebSocket disconnected")
