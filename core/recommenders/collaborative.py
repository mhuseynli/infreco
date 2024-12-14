import os
import json
from collections import defaultdict

from bson import ObjectId

from .base import BaseRecommender
from core.database import db

from infreco.settings import TRAINING_DIR

class CollaborativeRecommender(BaseRecommender):
    def __init__(self, webshop_id):
        self.webshop_id = webshop_id
        self.user_item_matrix = {}
        self.user_profiles = {}

    def load(self):
        """Load collaborative training data."""
        file_path = os.path.join(TRAINING_DIR, self.webshop_id, "collaborative.json")
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Collaborative training data not found at {file_path}")
        with open(file_path, "r") as f:
            data = json.load(f)
            self.user_item_matrix = data.get("user_item_matrix", {})
            self.user_profiles = data.get("user_profiles", {})

    def recommend(self, user_id, events=None, items=None, n=10):
        """Recommend items based on collaborative filtering."""
        user_id_str = str(user_id)
        if user_id_str not in self.user_profiles:
            raise ValueError(f"User profile for user {user_id} not found.")

        # Fetch user profile
        user_profile = self.user_profiles[user_id_str]

        # Use static attributes to refine recommendations
        age = user_profile.get("age")
        gender = user_profile.get("gender")
        location = user_profile.get("location", {})

        # Get all items interacted by similar users
        recommendations = defaultdict(float)
        for other_user_id, interactions in self.user_item_matrix.items():
            if other_user_id == user_id_str:
                continue

            # Measure similarity between users
            similarity_score = self.calculate_user_similarity(user_profile, self.user_profiles[other_user_id])

            # Weight recommendations by similarity
            for product_id, score in interactions.items():
                if product_id not in user_profile["interacted_items"]:
                    recommendations[product_id] += score * similarity_score

        # Sort recommendations by score and return top N
        sorted_recommendations = sorted(recommendations.items(), key=lambda x: x[1], reverse=True)
        return self.fetch_item_details(sorted_recommendations[:n])

    def calculate_user_similarity(self, user_a, user_b):
        """Calculate similarity between two users based on static attributes."""
        score = 0

        # Age similarity
        if user_a["age"] and user_b["age"]:
            age_diff = abs(user_a["age"] - user_b["age"])
            score += max(0, 1 - (age_diff / 50))  # Normalize age difference to a range of 0-1

        # Gender match
        if user_a["gender"] == user_b["gender"]:
            score += 0.5

        # Location match
        if user_a["location"].get("country") == user_b["location"].get("country"):
            score += 0.5
        if user_a["location"].get("city") == user_b["location"].get("city"):
            score += 0.5

        return score

    def fetch_item_details(self, recommendations):
        """Fetch item details for the recommendations."""
        item_ids = [item_id for item_id, _ in recommendations]
        items = db.items.find({"_id": {"$in": [ObjectId(item_id) for item_id in item_ids]}})
        item_details = {str(item["_id"]): {k: v for k, v in item.items() if k != "_id"} for item in items}

        # Combine scores with item details
        result = []
        for item_id, score in recommendations:
            if item_id in item_details:
                result.append({"item": item_details[item_id], "score": score})
        return result