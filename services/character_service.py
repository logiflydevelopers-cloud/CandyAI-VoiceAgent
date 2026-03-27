from database.mongo import characters_collection


# -----------------------------------
# CLEAN DOCUMENT HELPER
# -----------------------------------
def serialize_character(doc):
    if not doc:
        return None

    return {
        "id": str(doc.get("_id")),
        "uniqueId": doc.get("uniqueId"),
        "name": doc.get("name", "Ava"),
        "age": doc.get("age", ""),
        "location": doc.get("location", ""),
        "occupation": doc.get("occupation", ""),
        "relationship": doc.get("relationship", "Your girlfriend"),
        "personality": doc.get("personality", ""),
        "hobbies": doc.get("hobbies", ""),
        "description": doc.get("description", ""),
        "language": doc.get("language", "English"),
    }


# -----------------------------------
# GET ALL CHARACTERS
# -----------------------------------
def get_all_characters(limit=20):

    docs = characters_collection.find(
        {},
        {"_id": 1, "name": 1, "uniqueId": 1, "personality": 1}
    ).limit(limit)

    return [serialize_character(doc) for doc in docs]


# -----------------------------------
# GET SINGLE CHARACTER
# -----------------------------------
def get_character_by_id(uniqueId):

    doc = characters_collection.find_one({"uniqueId": uniqueId})

    if not doc:
        # ✅ fallback default girlfriend
        return {
            "id": "default",
            "uniqueId": "gf_default",
            "name": "Ava",
            "age": "23",
            "location": "Mumbai",
            "occupation": "Designer",
            "relationship": "Your caring girlfriend",
            "personality": "Sweet, romantic, playful",
            "hobbies": "Music, movies, chatting",
            "description": "She loves you and always cares about you",
            "language": "English",
        }

    return serialize_character(doc)