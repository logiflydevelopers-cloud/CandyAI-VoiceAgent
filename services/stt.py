import asyncio
from deepgram import DeepgramClient, LiveTranscriptionEvents
from configs import settings


class DeepgramSTT:
    def __init__(self):
        self.dg_client = DeepgramClient(settings.DEEPGRAM_API_KEY)
        self.connection = None
        self.transcript_queue = asyncio.Queue()

    # -----------------------------------
    # CONNECT
    # -----------------------------------
    async def connect(self):
        try:
            self.connection = self.dg_client.listen.live.v("1")

            # 🔥 FIXED HANDLER (Deepgram v3 compatible)
            def handle_transcript(*args, **kwargs):
                try:
                    result = kwargs.get("result")

                    if not result:
                        return

                    alt = result.channel.alternatives
                    if not alt:
                        return

                    transcript = alt[0].transcript

                    if transcript and transcript.strip():
                        asyncio.create_task(
                            self.transcript_queue.put({
                                "text": transcript,
                                "is_final": result.is_final
                            })
                        )

                except Exception as e:
                    print("❌ Transcript Error:", e)

            # 🔥 OPEN HANDLER
            def handle_open(*args, **kwargs):
                print("🟢 Deepgram connected")

            # 🔥 ERROR HANDLER
            def handle_error(*args, **kwargs):
                print("❌ Deepgram Error:", kwargs)

            # ✅ REGISTER EVENTS
            self.connection.on(LiveTranscriptionEvents.Transcript, handle_transcript)
            self.connection.on(LiveTranscriptionEvents.Open, handle_open)
            self.connection.on(LiveTranscriptionEvents.Error, handle_error)

            # ❗ DO NOT AWAIT (important)
            self.connection.start({
                "model": "nova-2",
                "language": "en",
                "encoding": "linear16",
                "sample_rate": 16000,
                "interim_results": True,
                "endpointing": 300,
            })

        except Exception as e:
            print("❌ Connection Error:", e)

    # -----------------------------------
    # SEND AUDIO
    # -----------------------------------
    async def send_audio(self, audio_chunk: bytes):
        try:
            if self.connection:
                self.connection.send(audio_chunk)  # ❗ no await
        except Exception as e:
            print("❌ Send Audio Error:", e)

    # -----------------------------------
    # GET TRANSCRIPT
    # -----------------------------------
    async def get_transcript(self):
        return await self.transcript_queue.get()

    # -----------------------------------
    # CLOSE
    # -----------------------------------
    async def close(self):
        try:
            if self.connection:
                self.connection.finish()  # ❗ no await
                print("🔴 Deepgram closed")
        except Exception as e:
            print("❌ Close Error:", e)