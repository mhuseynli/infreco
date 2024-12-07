import os
import json
from collections import defaultdict
from bson import ObjectId

from .dynamic_base import DynamicBaseTrainer
from infreco.settings import TRAINING_DIR
from core.data_processing import fetch_webshop_data
from core.database import db


class DynamicCollaborativeTrainer(DynamicBaseTrainer):
    def __init__(self, webshop_id):
        super().__init__(webshop_id)
        self.user_item_matrix = defaultdict(lambda: defaultdict(float))
        self.user_profiles = {}
        self.load_existing_data()

    def load_existing_data(self):
        """Load existing collaborative data if available."""
        file_path = os.path.join(TRAINING_DIR, self.webshop_id, "collaborative.json")
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                data = json.load(f)
                self.user_item_matrix = defaultdict(
                    lambda: defaultdict(float), data.get("user_item_matrix", {})
                )
                self.user_profiles = data.get("user_profiles", {})
        else:
            print(f"No existing collaborative data found for {self.webshop_id}.")

    def save_data(self):
        """Save updated collaborative data."""
        file_path = os.path.join(TRAINING_DIR, self.webshop_id, "collaborative.json")
        with open(file_path, "w") as f:
            json.dump(
                {"user_item_matrix": self.user_item_matrix, "user_profiles": self.user_profiles}, f
            )

    def process_event(self, event):
        """Update user-item matrix and user profiles dynamically based on an event."""
        try:
            weight = self.get_event_weight(event["event_id"])
            user_id = event["user_id"]
            product_id = event["product_id"]

            # Update user-item matrix
            self.user_item_matrix[user_id][product_id] += weight

            # Update user profiles
            if user_id not in self.user_profiles:
                self.user_profiles[user_id] = self.initialize_user_profile(user_id)

            interacted_items = self.user_profiles[user_id].get("interacted_items", [])
            if product_id not in interacted_items:
                self.user_profiles[user_id]["interacted_items"].append(product_id)

            # Save updated data
            self.save_data()
            print(f"Dynamic update completed for event: {event}.")

        except Exception as e:
            print(f"Error processing event dynamically: {e}")

    def get_event_weight(self, event_id):
        """Fetch the weight of an event type by its ID."""
        event_type = db.event_types.find_one({"_id": ObjectId(event_id)})
        if not event_type:
            raise ValueError(f"Event type with ID {event_id} not found.")
        return event_type["weight"]

    def initialize_user_profile(self, user_id):
        """Initialize a user profile with static attributes."""
        user = db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise ValueError(f"User with ID {user_id} not found.")
        return {
            "age": user.get("age"),
            "gender": user.get("gender"),
            "location": user.get("location", {}),
            "interacted_items": [],
        }
