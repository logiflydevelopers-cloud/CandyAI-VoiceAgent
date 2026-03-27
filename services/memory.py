class SimpleMemory:

    def __init__(self, max_history=10):
        self.user_data = {}
        self.max_history = max_history

    def get_user(self, user_id):
        return self.user_data.setdefault(user_id, {
            "name": None,
            "mood": "neutral",
            "history": []  # [{"role": "user/assistant", "text": "..."}]
        })

    # -------------------------
    # BASIC SETTERS
    # -------------------------

    def set_name(self, user_id, name):
        if name:
            self.get_user(user_id)["name"] = name.strip().capitalize()

    def set_mood(self, user_id, mood):
        self.get_user(user_id)["mood"] = mood

    # -------------------------
    # MESSAGE HANDLING
    # -------------------------

    def add_message(self, user_id, role, message):
        user = self.get_user(user_id)

        user["history"].append({
            "role": role,
            "text": message
        })

        # keep only last N messages
        user["history"] = user["history"][-self.max_history:]

    # -------------------------
    # CONTEXT FOR LLM
    # -------------------------

    def get_context(self, user_id):
        data = self.get_user(user_id)

        # format history for prompt
        formatted_history = "\n".join([
            f'{msg["role"]}: {msg["text"]}'
            for msg in data["history"][-5:]
        ])

        return {
            "name": data["name"] or "baby",
            "mood": data["mood"],
            "history": formatted_history
        }

    # -------------------------
    # OPTIONAL: RESET USER
    # -------------------------

    def clear(self, user_id):
        if user_id in self.user_data:
            del self.user_data[user_id]