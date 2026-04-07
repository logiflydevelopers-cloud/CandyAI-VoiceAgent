from openai import OpenAI
from configs import settings

from services.memory import SimpleMemory
from services.prompt_builder import build_character_prompt
from services.mood import detect_mood
from services.character_service import get_character_by_id


client = OpenAI(api_key=settings.OPENAI_API_KEY)


class LLMService:
    def __init__(self):
        self.memory = SimpleMemory()

    # -----------------------------------
    # MAIN RESPONSE FUNCTION
    # -----------------------------------
    async def generate_response(self, user_id: str, character_id: str, user_text: str) -> str:
        try:
            # 1. Detect Mood
            mood = await self._detect_mood(user_text)
            self.memory.set_mood(user_id, mood)

            # 2. Store User Message
            self.memory.add_message(user_id, "user", user_text)

            # 3. Get Memory Context
            context = self.memory.get_context(user_id)

            # 4. Load Character from DB
            character = get_character_by_id(character_id)

            # 5. Build Dynamic Prompt
            system_prompt = build_character_prompt(character)

            # 6. Inject Dynamic Context (VERY IMPORTANT)
            system_prompt += f"""

Current User Context:
- User Name: {context['name']}
- Current Mood: {context['mood']}

Recent Conversation:
{context['history']}
"""

            # 7. Call LLM
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_text}
                ],
                temperature=0.8,
            )

            reply = response.choices[0].message.content.strip()

            # 8. Store AI Response
            self.memory.add_message(user_id, "assistant", reply)

            return reply

        except Exception as e:
            print("LLM Error:", e)
            return "Hmm... something feels off. Can you say that again?"

    # -----------------------------------
    # INTERNAL MOOD DETECTION
    # -----------------------------------
    async def _detect_mood(self, text: str) -> str:
        try:
            # lightweight LLM call for mood
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "Classify mood into: happy, sad, flirty, angry, neutral. Only return one word."
                    },
                    {"role": "user", "content": text}
                ],
                temperature=0
            )

            mood = response.choices[0].message.content.strip().lower()

            allowed = ["happy", "sad", "flirty", "angry", "neutral"]
            return mood if mood in allowed else "neutral"

        except Exception as e:
            print("Mood Detection Error:", e)
            return "neutral"