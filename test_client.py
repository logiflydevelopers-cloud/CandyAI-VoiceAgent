import asyncio
import websockets
import json

WS_URL = "ws://candyai-voiceagent.onrender.com/voice"


async def test():
    async with websockets.connect(WS_URL) as ws:
        print("✅ Connected to server")

        # 🔐 Send init data
        await ws.send(json.dumps({
            "user_id": "test_user",
            "character_id": "69afc5a36b69a290cae6969e"  # 👈 put valid Mongo ID
        }))

        print("🎤 Sending fake audio...")

        # ❗ For now: send dummy audio (just to test flow)
        for _ in range(5):
            await ws.send(b"\x00" * 3200)  # fake PCM chunk
            await asyncio.sleep(0.1)

        # 👂 Listen for responses
        while True:
            msg = await ws.recv()

            if isinstance(msg, bytes):
                print(f"🔊 Received audio chunk: {len(msg)} bytes")
            else:
                print("📩", msg)


asyncio.run(test())