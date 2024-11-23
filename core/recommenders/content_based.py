import os
import json
from collections import defaultdict
from .base import BaseRecommender

TRAINING_DIR = "training_data"

class ContentBasedRecommender(BaseRecommender):
    def __init__(self, webshop_id):
        self.webshop_id = webshop_id
        self.item_similarities = {}

    def load(self):
        """Load content-based training data."""
        file_path = os.path.join(TRAINING_DIR, self.webshop_id, "content_based.json")
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Content-based training data not found at {file_path}")
        with open(file_path, "r") as f:
            self.item_similarities = json.load(f)

    def recommend(self, user_id, events, items=None, n=10):
        """Recommend items based on item attributes."""
        # Get items the user has already interacted with
        interacted_items = {str(event["item_id"]) for event in events if str(event["user_id"]) == user_id}
        print(f"Interacted items for user {user_id}: {interacted_items}")

        # Collect recommendations by aggregating similarities for non-interacted items
        recommendations = defaultdict(float)
        for item_id in interacted_items:
            similar_items = self.item_similarities.get(item_id, {})
            print(f"Similar items for {item_id}: {similar_items}")

            for similar_item_id, similarity_score in similar_items.items():
                if similar_item_id not in interacted_items:
                    recommendations[similar_item_id] += similarity_score

        # Sort by aggregated score and return top N
        sorted_recommendations = sorted(recommendations.items(), key=lambda x: x[1], reverse=True)
        print(f"Aggregated recommendations: {sorted_recommendations}")

        return [{"item_id": item_id, "score": score} for item_id, score in sorted_recommendations[:n]]