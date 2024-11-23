import os
import pickle
import pandas as pd
from surprise import Dataset, Reader, SVD
from .base import BaseTrainer
from ..data_processing import fetch_webshop_data

TRAINING_DIR = "training_data"

def ensure_training_dir(webshop_id):
    """Ensure training directory exists for a webshop."""
    directory = os.path.join(TRAINING_DIR, webshop_id)
    os.makedirs(directory, exist_ok=True)
    return directory

class SurpriseTrainer(BaseTrainer):
    def __init__(self, webshop_id):
        self.webshop_id = webshop_id
        self.model = None

    def train(self):
        """Train a collaborative filtering model using Surprise."""
        users, items, events = fetch_webshop_data(self.webshop_id)

        # Prepare data for Surprise
        interactions = [
            (str(event["user_id"]), str(event["item_id"]), event["event_type"])
            for event in events if event["event_type"] in {"purchase", "like", "click", "add-to-cart"}
        ]
        print(f"Training on {len(interactions)} interactions.")

        # Assign weights to event types
        weight_mapping = {"purchase": 5, "add-to-cart": 3, "like": 2, "click": 1}
        weighted_interactions = [
            (user, item, weight_mapping[event_type])
            for user, item, event_type in interactions
        ]

        # Convert to Surprise dataset
        reader = Reader(rating_scale=(1, 5))
        data = Dataset.load_from_df(
            pd.DataFrame(weighted_interactions, columns=["user", "item", "rating"]),
            reader
        )

        # Train the model
        trainset = data.build_full_trainset()
        self.model = SVD()  # You can replace SVD with other Surprise algorithms like KNN.
        self.model.fit(trainset)

        # Save the model
        directory = ensure_training_dir(self.webshop_id)
        model_path = os.path.join(directory, "surprise_model.pkl")
        with open(model_path, "wb") as f:
            pickle.dump(self.model, f)

        print(f"Surprise training completed for {self.webshop_id}. Model saved to {model_path}.")