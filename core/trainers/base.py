from abc import ABC, abstractmethod

class BaseTrainer(ABC):
    """Abstract base class for trainers."""

    @abstractmethod
    def train(self):
        """Train the model."""
        pass