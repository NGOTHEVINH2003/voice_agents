import json, base64, asyncio
from websockets import ServerProtocol
from whisper_service import transcribe_audio
from eleven_realtime import text_to_speech
from rag_service import query_rag

async def handle_twilio_stream(ws: ServerProtocol):
    print("🔗 Twilio connected.")
    audio_buffer = bytearray()
    print("Check 1")
    async for message in ws:
        event = json.loads(message)
        event_type = event.get("event")
        print("Check 2")
        if event_type == "start":
            print("▶️ Stream started.")

        elif event_type == "media":
            audio_b64 = event["media"]["payload"]
            audio_bytes = base64.b64decode(audio_b64)
            audio_buffer.extend(audio_bytes)

            # xử lý từng block 1s audio
            if len(audio_buffer) > 16000:
                audio_chunk = bytes(audio_buffer)
                audio_buffer.clear()

                # 1️⃣ STT
                text = transcribe_audio(audio_chunk)
                if not text.strip():
                    continue
                print(f"👤 User: {text}")

                # 2️⃣ RAG
                answer = query_rag(text)
                print(f"🤖 AI: {answer}")

                # 3️⃣ TTS
                audio_reply = text_to_speech(answer)
                audio_reply_b64 = base64.b64encode(audio_reply).decode("utf-8")

                # 4️⃣ Gửi về Twilio
                await ws.send(json.dumps({
                    "event": "media",
                    "media": {"payload": audio_reply_b64}
                }))

        elif event_type == "stop":
            print("⏹ Stream stopped.")