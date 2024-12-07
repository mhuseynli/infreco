import os
import json
from collections import defaultdict

from bson import ObjectId

from core.database import db
from core.recommenders.base import BaseRecommender
from infreco.settings import TRAINING_DIR


class ContentBasedRecommender(BaseRecommender):
    def __init__(self, webshop_id):
        self.webshop_id = webshop_id
        self.item_similarities = {}

    def load(self):
        """Load content-based training data."""
        file_path = os.path.join(TRAINING_DIR, self.webshop_id, "content_based.json")
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Content-based training data not found for webshop {self.webshop_id}.")
        with open(file_path, "r") as f:
            self.item_similarities = json.load(f)

    def recommend(self, user_id, events, items, n=50):
        """
        Recommend items based on user interactions and dynamic preferences.

        :param user_id: ID of the user to generate recommendations for.
        :param events: List of events for the webshop.
        :param items: List of items for the webshop.
        :param n: Number of recommendations to return.
        :return: List of recommended items with scores.
        """
        # Load user profile
        user = db.users.find_one({"_id": ObjectId(user_id)})
        preferences = user.get("preferences", {})

        # Get items user interacted with
        interacted_items = {str(event["product_id"]) for event in events if str(event["user_id"]) == user_id}

        # Aggregate recommendations based on similarity scores
        recommendations = defaultdict(float)
        for item_id in interacted_items:
            similar_items = self.item_similarities.get(item_id, {})
            for similar_item_id, similarity_score in similar_items.items():
                if similar_item_id not in interacted_items:
                    # Apply preference weight
                    item = db.items.find_one({"_id": ObjectId(similar_item_id)})
                    if item:
                        for attr, weight in preferences.items():
                            if attr in item.get("categories", []) or attr == item.get("brand"):
                                similarity_score *= weight
                    recommendations[similar_item_id] += similarity_score

        # Sort recommendations by score and return the top N
        sorted_recommendations = sorted(recommendations.items(), key=lambda x: x[1], reverse=True)
        return [
            {"item_id": str(item_id), "score": score} for item_id, score in sorted_recommendations[:n]
        ]
