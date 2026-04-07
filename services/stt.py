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

            # ✅ FIX: handler MUST accept (self, event)
            def handle_transcript(_, event):
                try:
                    if not event:
                        return

                    alt = event.channel.alternatives
                    if not alt:
                        return

                    transcript = alt[0].transcript

                    if transcript.strip():
                        asyncio.create_task(
                            self.transcript_queue.put({
                                "text": transcript,
                                "is_final": event.is_final
                            })
                        )

                except Exception as e:
                    print("❌ Transcript Error:", e)

            def handle_open(_, event):
                print("🟢 Deepgram connected")

            def handle_error(_, event):
                print("❌ Deepgram Error:", event)

            # ✅ REGISTER HANDLERS
            self.connection.on(LiveTranscriptionEvents.Transcript, handle_transcript)
            self.connection.on(LiveTranscriptionEvents.Open, handle_open)
            self.connection.on(LiveTranscriptionEvents.Error, handle_error)

            # ❗ IMPORTANT: DO NOT AWAIT
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
                # ❗ DO NOT AWAIT
                self.connection.send(audio_chunk)
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
                self.connection.finish()
                print("🔴 Deepgram closed")
        except Exception as e:
            print("❌ Close Error:", e)