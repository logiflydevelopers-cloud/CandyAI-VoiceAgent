import httpx
from configs import settings


class DeepgramTTS:
    def __init__(self):
        self.api_key = settings.DEEPGRAM_API_KEY

        self.url = "https://api.deepgram.com/v1/speak?model=aura-asteria-en"

        self.headers = {
            "Authorization": f"Token {self.api_key}",
            "Content-Type": "application/json"
        }

    async def generate_audio(self, text: str):
        print("🔊 TTS Request:", text)

        async with httpx.AsyncClient(timeout=None) as client:
            response = await client.post(
                self.url,
                headers=self.headers,
                json={
                    "text": text
                }
            )

            print("📡 TTS Status:", response.status_code)

            if response.status_code != 200:
                print("❌ TTS Error:", response.text)
                return None

            audio_bytes = response.content
            print(f"🔊 Audio size: {len(audio_bytes)} bytes")

            return audio_bytes