from dotenv import load_dotenv
from livekit import agents
from livekit.agents import (
    AgentServer,
    Agent,
    AgentSession,
    ChatContext,
    room_io,
)
from livekit.plugins import openai, silero
from services.prompt_builder import build_character_prompt
from services.memory import SimpleMemory
from services.character_service import get_character_by_id

import logging
import json
import os
import asyncio

logging.getLogger("pymongo").setLevel(logging.WARNING)

memory_store = SimpleMemory()

load_dotenv()

print("LIVEKIT_URL:", os.getenv("LIVEKIT_URL"))
print("LIVEKIT_API_KEY:", os.getenv("LIVEKIT_API_KEY"))

# --------------------------------------------------
# VOICE AGENT
# --------------------------------------------------

class VoiceAgent(Agent):

    def __init__(self, chat_ctx: ChatContext, user_id: str, character_data):
        self.user_id = user_id
        self.character_data = character_data
        self.memory_store = memory_store
        self.is_speaking = False   # ✅ NEW (sync fix)

        super().__init__(
            chat_ctx=chat_ctx,
            instructions=build_character_prompt(character_data),
            llm=openai.LLM(
                model="gpt-4o-mini",
                max_tokens=120   # ✅ reduce chunking
            )
        )

    async def on_user_turn_completed(self, turn_ctx, new_message):

        # 🚫 BLOCK if agent is speaking
        if self.is_speaking:
            return

        user_text = new_message.text_content
        logging.info(f"User said: {user_text}")

        # Store memory
        self.memory_store.add_message(self.user_id, "user", user_text)

        text = user_text.lower()

        # Mood detection
        if any(x in text for x in ["sad", "upset", "bad day", "depressed"]):
            mood = "sad"
        elif any(x in text for x in ["love", "baby", "miss you"]):
            mood = "flirty"
        elif any(x in text for x in ["angry", "mad", "frustrated"]):
            mood = "angry"
        elif any(x in text for x in ["happy", "great", "awesome"]):
            mood = "happy"
        else:
            mood = "neutral"

        self.memory_store.set_mood(self.user_id, mood)

        # Name detection
        if "my name is" in text:
            name = user_text.split("my name is")[-1].strip().split(" ")[0]
            self.memory_store.set_name(self.user_id, name)

        ctx = self.memory_store.get_context(self.user_id)

        dynamic_prompt = f"""
User name: {ctx["name"]}
Mood: {ctx["mood"]}

Recent conversation:
{ctx["history"]}

Tone rules:
- sad → caring
- happy → energetic
- flirty → playful
- angry → calm
"""

        # ✅ Inject less frequently (performance + stability)
        if len(ctx["history"]) % 3 == 0:
            turn_ctx.add_message(role="system", content=dynamic_prompt)


# --------------------------------------------------
# SERVER
# --------------------------------------------------

server = AgentServer()


@server.rtc_session(agent_name="voice-agent")
async def my_agent(ctx: agents.JobContext):

    print("Agent job received")

    await ctx.connect()
    print("Room connected")

    @ctx.room.on("track_subscribed")
    def on_track(track, pub, participant):
        print("Received track from:", participant.identity, "| kind:", track.kind)

    participant = await ctx.wait_for_participant()

    if not participant:
        print("No participant joined")
        return

    user_id = participant.identity
    print("User ID:", user_id)

    metadata = {}

    if participant.metadata:
        try:
            metadata = json.loads(participant.metadata)
        except Exception as e:
            print("Metadata parse failed:", e)

    character_id = metadata.get("character_id", "gf_1")
    print("Character ID:", character_id)

    character_data = get_character_by_id(character_id)
    print("Character loaded:", character_data.get("name"))

    initial_ctx = ChatContext()

    # -------------------------
    # STT SETUP (OPTIMIZED)
    # -------------------------
    base_stt = openai.STT(
        model="gpt-4o-mini-transcribe"
    )

    vad_model = silero.VAD.load(
        min_speech_duration=0.3,   # ✅ less noise triggers
        min_silence_duration=0.8,  # ✅ smoother transitions
    )

    streaming_stt = agents.stt.StreamAdapter(
        stt=base_stt,
        vad=vad_model,
    )

    # -------------------------
    # SESSION SETUP (FIXED)
    # -------------------------
    session = AgentSession(
        stt=streaming_stt,
        llm=openai.LLM(
            model="gpt-4o-mini",
            max_tokens=120
        ),
        tts=openai.TTS(
            voice="nova",
            speed=1.0
        ),
        allow_interruptions=True   # ✅ CRITICAL FIX
    )

    agent = VoiceAgent(
        chat_ctx=initial_ctx,
        user_id=user_id,
        character_data=character_data,
    )

    await session.start(
        room=ctx.room,
        agent=agent,
        room_input_options=room_io.RoomInputOptions(
            close_on_disconnect=False
        )
    )

    # -------------------------
    # WRAP REPLY FOR SYNC
    # -------------------------
    async def safe_reply(instructions):
        agent.is_speaking = True
        await asyncio.sleep(0.2)   # ✅ buffer stabilization
        await session.generate_reply(instructions=instructions)
        agent.is_speaking = False

    # -------------------------
    # INITIAL GREETING
    # -------------------------
    await safe_reply(
        "Start with a sweet, natural girlfriend-style greeting."
    )


# --------------------------------------------------
# ENTRYPOINT
# --------------------------------------------------

if __name__ == "__main__":
    from livekit.agents import cli
    cli.run_app(server)