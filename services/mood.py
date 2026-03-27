# services/mood.py

async def detect_mood(llm, text: str) -> str:

    prompt = f"""
Classify mood into:
happy, sad, flirty, angry, neutral

Text: "{text}"

Only return one word.
"""

    res = await llm.complete(prompt)
    mood = res.text.strip().lower()

    allowed = ["happy", "sad", "flirty", "angry", "neutral"]

    return mood if mood in allowed else "neutral"