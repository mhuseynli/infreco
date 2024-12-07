import os
import json
from collections import defaultdict

from bson import ObjectId

from infreco.settings import TRAINING_DIR
from .base import BaseTrainer
from core.data_processing import fetch_webshop_data
from core.database import db


def ensure_training_dir(webshop_id):
    """Ensure training directory exists for a webshop."""
    directory = os.path.join(TRAINING_DIR, webshop_id)
    os.makedirs(directory, exist_ok=True)
    return directory


class CollaborativeTrainer(BaseTrainer):
    def __init__(self, webshop_id):
        super().__init__(webshop_id)  # Call the base class constructor

    def train(self):
        """Train collaborative filtering data."""
        users, items, events, attributes = fetch_webshop_data(self.webshop_id)

        # Group events and compute scores
        user_item_matrix = defaultdict(lambda: defaultdict(float))
        for event in events:
            weight = self.get_event_weight(event["event_id"])
            user_id = event["user_id"]
            product_id = event["product_id"]
            user_item_matrix[user_id][product_id] += weight

        # Include user static attributes in training data
        user_profiles = self.build_user_profiles(users, user_item_matrix)

        # Save training data
        directory = ensure_training_dir(self.webshop_id)
        file_path = os.path.join(directory, "collaborative.json")
        with open(file_path, "w") as f:
            json.dump({"user_item_matrix": user_item_matrix, "user_profiles": user_profiles}, f)

        print(f"Collaborative training completed for {self.webshop_id}. Data saved to {file_path}.")

    def get_event_weight(self, event_id):
        """Fetch the weight of an event type by its ID."""
        event_type = db.event_types.find_one({"_id": ObjectId(event_id)})
        if not event_type:
            raise ValueError(f"Event type with ID {event_id} not found.")
        return event_type["weight"]

    def build_user_profiles(self, users, user_item_matrix):
        """Create user profiles with static attributes."""
        user_profiles = {}
        for user in users:
            profile = {
                "age": user.get("age"),
                "gender": user.get("gender"),
                "location": user.get("location", {}),
                "interacted_items": list(user_item_matrix.get(str(user["_id"]), {}).keys()),
            }
            user_profiles[str(user["_id"])] = profile
        return user_profiles
