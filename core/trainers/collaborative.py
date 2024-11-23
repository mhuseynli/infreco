import os
import json
from collections import defaultdict
from .base import BaseTrainer
from ..data_processing import fetch_webshop_data, group_users_by_age

TRAINING_DIR = "training_data"

def ensure_training_dir(webshop_id):
    """Ensure training directory exists for a webshop."""
    directory = os.path.join(TRAINING_DIR, webshop_id)
    os.makedirs(directory, exist_ok=True)
    return directory

class CollaborativeTrainer(BaseTrainer):
    def __init__(self, webshop_id):
        self.webshop_id = webshop_id

    def train(self):
        """Train collaborative filtering data."""
        users, items, events = fetch_webshop_data(self.webshop_id)
        age_groups = group_users_by_age(users)

        # Group purchases by age group
        recommendations = defaultdict(lambda: defaultdict(int))
        for event in events:
            if event["event_type"] == "purchase":
                user_id = event["user_id"]
                item_id = event["item_id"]

                # Find the user's age group
                for age_group, user_ids in age_groups.items():
                    if user_id in user_ids:
                        recommendations[age_group][str(item_id)] += 1

        # Save to file
        directory = ensure_training_dir(self.webshop_id)
        with open(os.path.join(directory, "collaborative.json"), "w") as f:
            json.dump(recommendations, f)
        print(f"Collaborative training completed for {self.webshop_id}.")