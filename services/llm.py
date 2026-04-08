from openai import OpenAI
from configs import settings

from services.memory import SimpleMemory
from services.prompt_builder import build_character_prompt
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
            # -----------------------------------
            # 1. FAST MOOD DETECTION (NO LLM)
            # -----------------------------------
            mood = self._detect_mood_fast(user_text)
            self.memory.set_mood(user_id, mood)

            # -----------------------------------
            # 2. STORE USER MESSAGE
            # -----------------------------------
            self.memory.add_message(user_id, "user", user_text)

            # -----------------------------------
            # 3. CONTEXT
            # -----------------------------------
            context = self.memory.get_context(user_id)

            # -----------------------------------
            # 4. CHARACTER
            # -----------------------------------
            character = get_character_by_id(character_id)

            # -----------------------------------
            # 5. PROMPT
            # -----------------------------------
            system_prompt = build_character_prompt(character)

            system_prompt += f"""

Current User Context:
- User Name: {context['name']}
- Current Mood: {context['mood']}

Recent Conversation:
{context['history']}
"""

            # -----------------------------------
            # 6. LLM CALL (ONLY ONE CALL NOW ⚡)
            # -----------------------------------
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_text}
                ],
                temperature=0.8,
            )

            reply = response.choices[0].message.content.strip()

            # -----------------------------------
            # 7. STORE AI RESPONSE
            # -----------------------------------
            self.memory.add_message(user_id, "assistant", reply)

            return reply

        except Exception as e:
            print("LLM Error:", e)
            return "Hmm... something feels off. Can you say that again?"

    # -----------------------------------
    # FAST MOOD DETECTION (TEXT + TONE)
    # -----------------------------------
    def _detect_mood_fast(self, text: str) -> str:
        text_lower = text.lower()

        # 🔥 FLIRTY
        if any(w in text_lower for w in ["love", "baby", "miss you", "kiss"]):
            return "flirty"

        # 😡 ANGRY (short + aggressive)
        if any(w in text_lower for w in ["hate", "angry", "idiot", "stupid"]):
            return "angry"

        # 😢 SAD
        if any(w in text_lower for w in ["sad", "lonely", "tired", "bad"]):
            return "sad"

        # 😊 HAPPY
        if any(w in text_lower for w in ["great", "awesome", "happy", "good"]):
            return "happy"

        # 🔥 TONE SIGNALS
        if text.endswith("!"):
            return "happy"

        if len(text.split()) <= 2:
            return "angry"

        if "..." in text:
            return "sad"

        return "neutral"