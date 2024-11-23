import os
import json
from collections import defaultdict
from .base import BaseTrainer
from ..data_processing import fetch_webshop_data

TRAINING_DIR = "training_data"

def ensure_training_dir(webshop_id):
    """Ensure training directory exists for a webshop."""
    directory = os.path.join(TRAINING_DIR, webshop_id)
    os.makedirs(directory, exist_ok=True)
    return directory

class ContentBasedTrainer(BaseTrainer):
    def __init__(self, webshop_id):
        self.webshop_id = webshop_id

    def train(self):
        """Train content-based recommendations based on item attributes."""
        users, items, events = fetch_webshop_data(self.webshop_id)

        # Precompute item similarities
        item_similarities = defaultdict(dict)
        for item_a in items:
            for item_b in items:
                if item_a["_id"] == item_b["_id"]:
                    continue
                similarity_score = self.calculate_similarity(item_a["attributes"], item_b["attributes"])
                if similarity_score > 0:
                    item_similarities[str(item_a["_id"])][str(item_b["_id"])] = similarity_score

        # Save training data
        directory = ensure_training_dir(self.webshop_id)
        file_path = os.path.join(directory, "content_based.json")
        with open(file_path, "w") as f:
            json.dump(item_similarities, f)

        print(f"Content-based training completed for {self.webshop_id}. Data saved to {file_path}.")

    def calculate_similarity(self, item_a, item_b):
        """Calculate similarity between two items based on attributes."""
        score = 0

        # Shared categories
        categories_a = set(item_a.get("categories", []))
        categories_b = set(item_b.get("categories", []))
        score += len(categories_a & categories_b) * 3  # High weight for shared categories

        # Same brand
        if item_a.get("brand") == item_b.get("brand"):
            score += 2  # Medium weight for same brand

        # Price similarity (within 20% range)
        price_a = item_a.get("price", 0)
        price_b = item_b.get("price", 0)
        if 0.8 * price_a <= price_b <= 1.2 * price_a:
            score += 1  # Low weight for similar price

        return score