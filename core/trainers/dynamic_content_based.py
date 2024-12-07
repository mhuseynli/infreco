import os
import json
from collections import defaultdict
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler
import pandas as pd

from .dynamic_base import DynamicBaseTrainer
from core.data_processing import fetch_webshop_data, preprocess_items
from infreco.settings import TRAINING_DIR


class DynamicContentBasedTrainer(DynamicBaseTrainer):
    def __init__(self, webshop_id):
        super().__init__(webshop_id)
        self.item_similarities = self.load_existing_data()

    def load_existing_data(self):
        """Load existing similarity matrix."""
        file_path = os.path.join(TRAINING_DIR, self.webshop_id, "content_based.json")
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                return json.load(f)
        return defaultdict(dict)

    def save_data(self):
        """Save the similarity matrix."""
        file_path = os.path.join(TRAINING_DIR, self.webshop_id, "content_based.json")
        with open(file_path, "w") as f:
            json.dump(self.item_similarities, f)

    def update_similarity(self, event_data):
        """Update the similarity matrix dynamically."""
        _, items, _, attributes = fetch_webshop_data(self.webshop_id)

        if not attributes:
            raise ValueError(f"Attributes not found for webshop ID: {self.webshop_id}")

        # Preprocess items
        items_df = preprocess_items(items, attributes)

        # Exclude non-numeric columns
        non_feature_columns = ["_id", "name", "description", "webshop_id", "created_at", "updated_at"]
        feature_columns = [col for col in items_df.columns if col not in non_feature_columns]

        if not feature_columns:
            raise ValueError("No numeric features found for similarity calculation.")

        # Normalize the data for numeric features
        scaler = StandardScaler()
        feature_matrix = scaler.fit_transform(items_df[feature_columns].fillna(0))

        # Find the updated item
        updated_item_id = event_data["product_id"]
        updated_index = items_df["_id"].tolist().index(updated_item_id)

        # Calculate cosine similarity for the updated item
        updated_similarities = cosine_similarity(
            feature_matrix[updated_index:updated_index + 1],
            feature_matrix
        )[0]

        # Update similarity matrix
        for i, sim_score in enumerate(updated_similarities):
            if updated_item_id != items_df["_id"][i]:
                self.item_similarities[updated_item_id][items_df["_id"][i]] = sim_score
                self.item_similarities[items_df["_id"][i]][updated_item_id] = sim_score

        # Save updated similarity matrix
        self.save_data()

    def process_event(self, event_data):
        """Process event to dynamically update the model."""
        self.update_similarity(event_data)
        print(f"Updated similarity matrix for webshop {self.webshop_id}.")


def process_event_with_trainer(event_data):
    """Wrapper to dynamically train model using the trainer."""
    webshop_id = event_data["webshop_id"]
    trainer = DynamicContentBasedTrainer(webshop_id)
    trainer.process_event(event_data)
