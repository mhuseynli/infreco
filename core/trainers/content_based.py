import os
import json
from collections import defaultdict
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler
import pandas as pd

from core.data_processing import fetch_webshop_data, preprocess_items, preprocess_events
from core.trainers.base import BaseTrainer
from infreco.settings import TRAINING_DIR


def ensure_training_dir(webshop_id):
    """Ensure training directory exists for a webshop."""
    directory = os.path.join(TRAINING_DIR, webshop_id)
    os.makedirs(directory, exist_ok=True)
    return directory


class ContentBasedTrainer(BaseTrainer):
    def __init__(self, webshop_id):
        super().__init__(webshop_id)  # Call the base class constructor

    def train(self):
        """Train content-based recommendations."""
        users, items, events, attributes = fetch_webshop_data(self.webshop_id)

        if not attributes:
            raise ValueError(f"Attributes not found for webshop ID: {self.webshop_id}")

        # Preprocess items and events
        items_df = preprocess_items(items, attributes)
        events_df = preprocess_events(events)

        # Merge item and event data to include event weights
        event_item_weights = events_df.groupby("product_id")["event_weight"].sum().to_dict()
        items_df["event_weight"] = items_df["_id"].map(event_item_weights).fillna(0)

        # Ensure `_id` and `external_id` are treated as string identifiers
        items_df["_id"] = items_df["_id"].astype(str)
        items_df["external_id"] = items_df["external_id"].astype(str)

        # Separate identifiers and non-numeric columns
        non_feature_columns = ["_id", "external_id", "name", "description", "webshop_id", "created_at", "updated_at"]
        feature_columns = [col for col in items_df.columns if col not in non_feature_columns]

        if not feature_columns:
            raise ValueError("No numeric features found for similarity calculation.")

        # Handle categorical external_id using label encoding or one-hot encoding
        if "external_id" in items_df.columns:
            # Label Encoding (simple and efficient for unique IDs)
            from sklearn.preprocessing import LabelEncoder
            label_encoder = LabelEncoder()
            items_df["external_id_encoded"] = label_encoder.fit_transform(items_df["external_id"])

            # Add the encoded `external_id` to features
            feature_columns.append("external_id_encoded")

        # Normalize the data for numeric features
        scaler = StandardScaler()
        feature_matrix = scaler.fit_transform(items_df[feature_columns].fillna(0))

        # Calculate cosine similarity between items
        similarity_matrix = cosine_similarity(feature_matrix)

        # Convert the similarity matrix into a dictionary for easier storage
        item_similarities = defaultdict(dict)
        for i, item_id in enumerate(items_df["_id"]):
            for j, sim_score in enumerate(similarity_matrix[i]):
                if i != j and sim_score > 0:
                    item_similarities[item_id][items_df["_id"][j]] = sim_score

        # Save training data
        directory = ensure_training_dir(self.webshop_id)
        with open(os.path.join(directory, "content_based.json"), "w") as f:
            json.dump(item_similarities, f)
        print(f"Training completed for webshop ID: {self.webshop_id}")
