import httpx
from configs import settings


class ElevenLabsTTS:
    def __init__(self):
        self.api_key = settings.ELEVENLABS_API_KEY
        self.voice_id = settings.ELEVENLABS_VOICE_ID

        self.url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}/stream"

        self.headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json"
        }

    async def stream_audio(self, text: str):
        try:
            async with httpx.AsyncClient(timeout=None) as client:
                async with client.stream(
                    "POST",
                    self.url,
                    headers=self.headers,
                    json={
                        "text": text,
                        "model_id": "eleven_turbo_v2",
                        "output_format": "mp3_44100_128",  
                        "voice_settings": {
                            "stability": 0.5,
                            "similarity_boost": 0.8
                        }
                    }
                ) as response:

                    # 🔥 CHECK STATUS FIRST
                    if response.status_code != 200:
                        error_text = await response.aread()
                        print("❌ TTS ERROR:", response.status_code, error_text)
                        return

                    print("✅ TTS connected")

                    # 🔥 CHECK CONTENT TYPE
                    content_type = response.headers.get("content-type", "")
                    print("🎧 Content-Type:", content_type)

                    # should be audio/mpeg
                    if "audio" not in content_type:
                        print("❌ Not audio response!")
                        return

                    # 🔥 STREAM AUDIO
                    async for chunk in response.aiter_bytes():
                        if chunk:
                            print("🔊 TTS chunk:", len(chunk))  # DEBUG
                            yield chunk

        except Exception as e:
            print("❌ TTS Exception:", e)

        print("TTS Status:", response.status_code)