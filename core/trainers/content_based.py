import os
import json
from collections import defaultdict
from .base import BaseTrainer
from core.data_processing import fetch_webshop_data, preprocess_items

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
        """Train content-based recommendations."""
        users, items, events, attributes = fetch_webshop_data(self.webshop_id)

        if not attributes:
            raise ValueError(f"Attributes not found for webshop ID: {self.webshop_id}")

        # Process items using attributes
        items_df = preprocess_items(items, attributes)

        # Calculate item similarity
        item_similarities = defaultdict(dict)
        for i, item_a in items_df.iterrows():
            for j, item_b in items_df.iterrows():
                if i == j:
                    continue
                similarity_score = self.calculate_similarity(item_a, item_b, attributes)
                if similarity_score > 0:
                    item_similarities[str(item_a["_id"])][str(item_b["_id"])] = similarity_score

        # Save training data
        directory = ensure_training_dir(self.webshop_id)
        with open(os.path.join(directory, "content_based.json"), "w") as f:
            json.dump(item_similarities, f)

    def calculate_similarity(self, item_a, item_b, attributes):
        """Calculate similarity between two items."""
        score = 0
        for attr in attributes.get("attributes", []):
            name = attr["name"]
            weight = attr["weight"]
            if name in item_a and name in item_b:
                if isinstance(item_a[name], list) and isinstance(item_b[name], list):
                    # Overlap for array attributes
                    score += len(set(item_a[name]) & set(item_b[name])) * weight
                elif isinstance(item_a[name], (int, float)) and isinstance(item_b[name], (int, float)):
                    # Similarity for numeric attributes
                    if 0.8 * item_a[name] <= item_b[name] <= 1.2 * item_a[name]:
                        score += weight
                elif item_a[name] == item_b[name]:
                    # Exact match for categorical/string attributes
                    score += weight
        return score
