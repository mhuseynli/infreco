from abc import ABC, abstractmethod

class BaseRecommender(ABC):
    """Abstract base class for recommenders."""

    @abstractmethod
    def load(self):
        """Load a trained model or data."""
        pass

    @abstractmethod
    def recommend(self, user_id, events, items, n=10):
        """Generate recommendations."""
        pass