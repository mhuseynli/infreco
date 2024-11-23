import os
import json
from .base import BaseRecommender

TRAINING_DIR = "training_data"

class CollaborativeRecommender(BaseRecommender):
    def __init__(self, webshop_id):
        self.webshop_id = webshop_id
        self.recommendations = {}

    def load(self):
        """Load collaborative training data."""
        file_path = os.path.join(TRAINING_DIR, self.webshop_id, "collaborative.json")
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Collaborative training data not found at {file_path}")
        with open(file_path, "r") as f:
            self.recommendations = json.load(f)

    def recommend(self, user_id, events=None, items=None, n=10):
        """Recommend items based on user attributes."""
        user_attributes = next((event["user_attributes"] for event in events if str(event["user_id"]) == user_id), None)
        if not user_attributes:
            raise ValueError(f"No user attributes found for user {user_id}.")

        # Determine age group from user attributes
        age = user_attributes.get("age")
        age_group = f"{(age // 5) * 5}-{(age // 5) * 5 + 4}" if age else "Unknown"
        print(f"User belongs to age group: {age_group}")

        # Get recommendations for the user's age group
        group_recommendations = self.recommendations.get(age_group, {})
        if not group_recommendations:
            print(f"No recommendations found for age group {age_group}.")
            return []

        # Sort recommendations by score and return top N
        sorted_recommendations = sorted(group_recommendations.items(), key=lambda x: x[1], reverse=True)
        print(f"Recommendations for age group {age_group}: {sorted_recommendations}")

        return [{"item_id": item_id, "score": score} for item_id, score in sorted_recommendations[:n]]