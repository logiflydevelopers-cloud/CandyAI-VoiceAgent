from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import asyncio

from services.stt import DeepgramSTT
from services.tts import ElevenLabsTTS
from services.llm import LLMService

router = APIRouter()

# Shared services
llm = LLMService()
tts = ElevenLabsTTS()

@router.websocket("/voice")
async def voice_agent(ws: WebSocket):
    print("🔥 SOCKET REQUEST ARRIVED")
    await ws.accept()

    # -----------------------------------
    # INIT DATA
    # -----------------------------------
    try:
        init_data = await ws.receive_json()

        user_id = init_data.get("user_id", "default_user")
        character_id = init_data.get("character_id")

        if not character_id:
            await ws.close()
            return

    except Exception as e:
        print("❌ Init Error:", e)
        await ws.close()
        return

    print(f"✅ Connected: user={user_id}, character={character_id}")

    # -----------------------------------
    # INIT STT (LAZY)
    # -----------------------------------
    stt = DeepgramSTT()
    stt_connected = False

    # -----------------------------------
    # TASKS
    # -----------------------------------
    receive_task = None
    process_task = None

    try:
        # -----------------------------------
        # RECEIVE AUDIO
        # -----------------------------------
        async def receive_audio():
            nonlocal stt_connected

            try:
                while True:
                    message = await ws.receive()

                    # 🔥 HANDLE ALL TYPES
                    if message["type"] == "websocket.disconnect":
                        print("❌ WS disconnect message")
                        break

                    if message.get("bytes") is not None:
                        audio_chunk = message["bytes"]

                    elif message.get("text") is not None:
                        # ignore text (init already done)
                        continue

                    else:
                        continue

                    # ✅ CONFIRM AUDIO ARRIVED
                    print("📦 Audio chunk received:", len(audio_chunk))

                    # 🔥 CONNECT ON FIRST AUDIO
                    if not stt_connected:
                        print("🔥 FIRST AUDIO RECEIVED → connecting Deepgram")
                        await stt.connect()
                        stt_connected = True
                        print("🎧 Deepgram connected")

                    await stt.send_audio(audio_chunk)

            except WebSocketDisconnect:
                print("❌ Client disconnected (receive)")
            except Exception as e:
                print("❌ Receive Error:", e)

        # -----------------------------------
        # PROCESS TRANSCRIPT
        # -----------------------------------
        async def process_transcript():
            try:
                while True:
                    # ⛔ wait until STT is ready
                    if not stt_connected:
                        await asyncio.sleep(0.1)
                        continue

                    data = await stt.get_transcript()

                    if not data:
                        continue

                    text = data.get("text", "")
                    is_final = data.get("is_final", False)

                    # 📝 partial transcript
                    if text:
                        print(f"📝 Partial: {text}")

                        await ws.send_json({
                            "type": "transcript",
                            "text": text,
                            "final": is_final
                        })

                    # 🔥 FINAL SPEECH → PROCESS
                    if is_final and text.strip():
                        print(f"🗣 User: {text}")

                        # 🧠 LLM
                        response_text = await llm.generate_response(
                            user_id=user_id,
                            character_id=character_id,
                            user_text=text
                        )

                        print(f"🤖 AI: {response_text}")

                        # send text
                        await ws.send_json({
                            "type": "ai_text",
                            "text": response_text
                        })

                        # 🔊 STREAM TTS
                        async for chunk in tts.stream_audio(response_text):
                            await ws.send_bytes(chunk)

                        # 🔚 end signal
                        await ws.send_json({
                            "type": "audio_end"
                        })

            except asyncio.CancelledError:
                print("⚠️ Transcript task cancelled")
            except Exception as e:
                print("❌ Process Error:", e)

        # -----------------------------------
        # RUN TASKS
        # -----------------------------------
        receive_task = asyncio.create_task(receive_audio())
        process_task = asyncio.create_task(process_transcript())

        await asyncio.gather(receive_task, process_task)

    except WebSocketDisconnect:
        print(f"❌ Disconnected: user={user_id}")
    except Exception as e:
        print("❌ Socket Error:", e)

    finally:
        # -----------------------------------
        # CLEANUP
        # -----------------------------------
        if receive_task:
            receive_task.cancel()

        if process_task:
            process_task.cancel()

        if stt_connected:
            await stt.close()

        print("🛑 Connection cleaned up")