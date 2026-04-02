from fastapi import FastAPI
from pydantic import BaseModel
import os
import json

from livekit import api

app = FastAPI()


class TokenRequest(BaseModel):
    user_id: str
    character_id: str


@app.get("/")
def health():
    return {"status": "ok"}


@app.post("/get-token")
def get_token(data: TokenRequest):

    print("Incoming:", data.dict())

    room = f"room_{data.character_id}"

    # -------------------------
    # 🎫 GENERATE TOKEN
    # -------------------------
    token = (
        api.AccessToken(
            os.getenv("LIVEKIT_API_KEY"),
            os.getenv("LIVEKIT_API_SECRET"),
        )
        .with_identity(data.user_id)
        .with_name(data.user_id)
        .with_metadata(json.dumps({
            "character_id": data.character_id
        }))
        .with_grants(
            api.VideoGrants(
                room_join=True,
                room=room,
            )
        )
        .to_jwt()
    )

    # -------------------------
    # 🚀 DISPATCH AGENT (FIX)
    # -------------------------
    try:
        lkapi = api.LiveKitAPI(
            os.getenv("LIVEKIT_URL"),
            os.getenv("LIVEKIT_API_KEY"),
            os.getenv("LIVEKIT_API_SECRET"),
        )

        lkapi.agent_dispatch.create_dispatch(
            api.CreateAgentDispatchRequest(
                agent_name="voice-agent",  # must match your agent decorator
                room=room,
            )
        )

        print("✅ Agent dispatched to room:", room)

    except Exception as e:
        print("❌ Agent dispatch failed:", str(e))

    # -------------------------
    # 📤 RESPONSE
    # -------------------------
    return {
        "token": token,
        "url": os.getenv("LIVEKIT_URL"),
        "room": room
    }