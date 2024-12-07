class BaseTrainer:
    def __init__(self, webshop_id):
        self.webshop_id = webshop_id

    def train(self):
        raise NotImplementedError("Subclasses should implement this!")
