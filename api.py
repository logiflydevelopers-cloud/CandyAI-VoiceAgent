from fastapi import FastAPI
from pydantic import BaseModel
import os
import json

from livekit import api

app = FastAPI()


class TokenRequest(BaseModel):
    user_id: str
    character_id: str


@app.post("/get-token")
def get_token(data: TokenRequest):

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
                room="voice-room",
            )
        )
        .to_jwt()
    )

    return {
        "token": token,
        "url": os.getenv("LIVEKIT_URL"),
        "room": "voice-room"
    }