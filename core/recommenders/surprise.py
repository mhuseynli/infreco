from .base import BaseRecommender
import os
import pickle

TRAINING_DIR = "training_data"

class SurpriseRecommender(BaseRecommender):
    def __init__(self, webshop_id):
        self.webshop_id = webshop_id
        self.model = None

    def load(self):
        """Load a trained Surprise model."""
        model_path = os.path.join(TRAINING_DIR, self.webshop_id, "surprise_model.pkl")
        with open(model_path, "rb") as f:
            self.model = pickle.load(f)

    def recommend(self, user_id, events, items, n=10):
        """Recommend items based on predicted ratings."""
        if not self.model:
            raise ValueError("Model not loaded. Call `load()` before recommending.")

        # Get items the user has already interacted with
        interacted_items = {str(event["item_id"]) for event in events if str(event["user_id"]) == user_id}
        print(f"Interacted items for user {user_id}: {interacted_items}")

        # Predict ratings for all items the user hasn't interacted with
        recommendations = []
        for item in items:
            item_id = str(item["_id"])
            if item_id not in interacted_items:
                predicted_rating = self.model.predict(user_id, item_id).est
                recommendations.append((item_id, predicted_rating))

        # Sort by predicted rating and return top N
        recommendations.sort(key=lambda x: x[1], reverse=True)
        print(f"Generated recommendations: {recommendations[:n]}")
        return [{"item_id": item_id, "score": score} for item_id, score in recommendations[:n]]