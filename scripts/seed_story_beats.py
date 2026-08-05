import datetime
from google.cloud import firestore

# Hardcode the project ID string to ensure compatibility on Agent Engine
FIRESTORE_PROJECT = "qwiklabs-gcp-04-b94d5857ae5f"


def seed_story_beats():
    print(f"Connecting to Firestore for project '{FIRESTORE_PROJECT}'...")
    db = firestore.Client(project=FIRESTORE_PROJECT)
    collection_ref = db.collection("story_beats")

    seed_items = [
        {
            "beat_id": "beat_001",
            "title": "The Whispering Well Ambush",
            "act": "Act I: Shadows over Oakhaven",
            "summary": "The party investigates the town well and encounters 3 Ghasts guarding a subterranean iron door.",
            "encounter_type": "Combat",
            "recommended_level": 5,
            "status": "prepped",
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        },
        {
            "beat_id": "beat_002",
            "title": "Audience with Baron Vane",
            "act": "Act I: Shadows over Oakhaven",
            "summary": "The party seeks an audience with Baron Vane to obtain permission to enter the Catacombs.",
            "encounter_type": "Social",
            "recommended_level": 5,
            "status": "prepped",
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        },
        {
            "beat_id": "beat_003",
            "title": "The Crypt of the Sunken Sun",
            "act": "Act II: The Fallen Sanctum",
            "summary": "Exploring the flooded subterranean tomb to recover the Sunstone Amulet.",
            "encounter_type": "Exploration",
            "recommended_level": 6,
            "status": "planned",
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        },
    ]

    for item in seed_items:
        doc_ref = collection_ref.document(item["beat_id"])
        doc_ref.set(item)
        print(f"Seeded Story Beat: {item['beat_id']} - {item['title']}")

    print("Firestore story beats seeding complete!")


if __name__ == "__main__":
    seed_story_beats()
