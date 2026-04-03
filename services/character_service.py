from database.mongo import characters_collection
from bson import ObjectId


# -----------------------------------
# CLEAN DOCUMENT HELPER
# -----------------------------------
def serialize_character(doc):
    if not doc:
        raise ValueError("Cannot serialize empty character document")

    return {
        "id": str(doc["_id"]), 
        "uniqueId": doc.get("uniqueId"),
        "name": doc.get("name"),
        "age": doc.get("age"),
        "location": doc.get("location"),
        "occupation": doc.get("occupation"),
        "relationship": doc.get("relationship"),
        "personality": doc.get("personality"),
        "hobbies": doc.get("hobbies"),
        "description": doc.get("description"),
        "language": doc.get("language"),
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
def get_character_by_id(character_id):

    try:
        doc = characters_collection.find_one({
            "_id": ObjectId(character_id)
        })
    except Exception as e:
        raise ValueError(f"Invalid character_id: {character_id}")

    if not doc:
        raise ValueError(f"Character not found for id: {character_id}")

    return serialize_character(doc)