import os
import json
from abc import ABC, abstractmethod
from infreco.settings import TRAINING_DIR

class DynamicBaseTrainer(ABC):
    def __init__(self, webshop_id):
        self.webshop_id = webshop_id
        self.ensure_training_dir()

    def ensure_training_dir(self):
        """Ensure training directory exists for a webshop."""
        directory = os.path.join(TRAINING_DIR, self.webshop_id)
        os.makedirs(directory, exist_ok=True)
        return directory

    @abstractmethod
    def load_existing_data(self):
        """Load existing model data (like similarity matrix or user-item matrix)."""
        pass

    @abstractmethod
    def save_data(self):
        """Save updated model data."""
        pass

    @abstractmethod
    def process_event(self, event_data):
        """Process an event and update the model dynamically."""
        pass
