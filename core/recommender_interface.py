from abc import ABC, abstractmethod


class RecommenderInterface(ABC):

    @abstractmethod
    # We removed data because it will get it from rabbitmq
    def train(self, parameters):
        """
        Trains the recommender model.
        """
        pass

    @abstractmethod
    def recommend(self, user_id, num_recommendations=10):
        """
        Generates recommendations for a given user.
        """
        pass

    @abstractmethod
    def subscribe(self, event):
        """
        Subscribes to the queue
        """
        pass
