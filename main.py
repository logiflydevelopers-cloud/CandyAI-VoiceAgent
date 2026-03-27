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
import logging
import json
from services.character_service import get_character_by_id

logging.getLogger("pymongo").setLevel(logging.WARNING)

memory_store = SimpleMemory()

load_dotenv()
import os

print("LIVEKIT_URL:", os.getenv("LIVEKIT_URL"))
print("LIVEKIT_API_KEY:", os.getenv("LIVEKIT_API_KEY"))

# --------------------------------------------------
# SIMPLE VOICE AGENT
# --------------------------------------------------

class VoiceAgent(Agent):

    def __init__(self, chat_ctx: ChatContext, user_id: str, character_data):
        self.user_id = user_id
        self.character_data = character_data
        self.memory_store = memory_store

        super().__init__(
            chat_ctx=chat_ctx,
            instructions=build_character_prompt(character_data),
            llm=openai.LLM(model="gpt-4o-mini"),
        )

    async def on_user_turn_completed(self, turn_ctx, new_message):

        user_text = new_message.text_content

        # -------------------------
        # 🧠 ADD USER MESSAGE
        # -------------------------
        self.memory_store.add_message(self.user_id, "user", user_text)

        # -------------------------
        # 🎭 SIMPLE MOOD DETECTION (fast version)
        # -------------------------
        text = user_text.lower()

        if any(x in text for x in ["sad", "upset", "bad day", "depressed"]):
            mood = "sad"
        elif any(x in text for x in ["love", "baby", "miss you", "😘", "😉"]):
            mood = "flirty"
        elif any(x in text for x in ["angry", "mad", "frustrated"]):
            mood = "angry"
        elif any(x in text for x in ["happy", "great", "awesome"]):
            mood = "happy"
        else:
            mood = "neutral"

        self.memory_store.set_mood(self.user_id, mood)

        # -------------------------
        # 🧠 NAME DETECTION
        # -------------------------
        if "my name is" in text:
            name = user_text.split("my name is")[-1].strip().split(" ")[0]
            self.memory_store.set_name(self.user_id, name)

        # -------------------------
        # GET UPDATED CONTEXT
        # -------------------------
        ctx = self.memory_store.get_context(self.user_id)

        # -------------------------
        # DYNAMIC PROMPT INJECTION
        # -------------------------
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

        turn_ctx.add_message(
            role="system",
            content=dynamic_prompt
        )

# --------------------------------------------------
# SERVER
# --------------------------------------------------

server = AgentServer()

@server.rtc_session(agent_name="voice-agent")
async def my_agent(ctx: agents.JobContext):

    print("✅ Agent job received")

    # -------------------------
    # 🔗 STEP 1: CONNECT
    # -------------------------
    await ctx.connect()
    print("🔗 Room connected")

    # -------------------------
    # 👤 STEP 2: WAIT FOR USER
    # -------------------------
    participant = await ctx.wait_for_participant()

    if not participant:
        print("❌ No participant joined")
        return

    user_id = participant.identity
    print("👤 User ID:", user_id)

    # -------------------------
    # 📦 STEP 3: READ METADATA
    # -------------------------
    metadata = {}

    if participant.metadata:
        try:
            metadata = json.loads(participant.metadata)
        except Exception as e:
            print("⚠️ Metadata parse failed:", e)

    character_id = metadata.get("character_id", "gf_1")
    print("🎭 Character ID:", character_id)

    # -------------------------
    # 🎭 STEP 4: LOAD CHARACTER
    # -------------------------
    character_data = get_character_by_id(character_id)

    print("✅ Character loaded:", character_data.get("name"))

    # -------------------------
    # 🧠 CHAT CONTEXT
    # -------------------------
    initial_ctx = ChatContext()

    # -------------------------
    # 🎤 STT SETUP
    # -------------------------
    base_stt = openai.STT(model="gpt-4o-transcribe")

    vad_model = silero.VAD.load(
        min_speech_duration=0.1,
        min_silence_duration=0.5,
    )

    streaming_stt = agents.stt.StreamAdapter(
        stt=base_stt,
        vad=vad_model,
    )

    # -------------------------
    # 🤖 SESSION SETUP
    # -------------------------
    session = AgentSession(
        stt=streaming_stt,
        llm=openai.LLM(model="gpt-4o-mini"),
        tts=openai.TTS(voice="nova"),
    )

    # -------------------------
    # 🚀 START AGENT
    # -------------------------
    await session.start(
        room=ctx.room,
        agent=VoiceAgent(
            chat_ctx=initial_ctx,
            user_id=user_id,
            character_data=character_data,
        ),
        room_options=room_io.RoomOptions(),
    )

    # -------------------------
    # 💬 INITIAL MESSAGE
    # -------------------------
    await session.generate_reply(
        instructions="Start with a sweet, natural girlfriend-style greeting."
    )


# --------------------------------------------------
# ENTRYPOINT
# --------------------------------------------------

if __name__ == "__main__":
    from livekit.agents import cli
    cli.run_app(server)