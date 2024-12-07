import json
import unittest
from unittest.mock import patch, MagicMock
from bson import ObjectId

from core.services.consume import update_user_preferences, update_dynamic_collaborative, process_event, callback


class TestConsume(unittest.TestCase):

    @patch("core.services.consume.db")
    def test_update_user_preferences(self, mock_db):
        mock_user = {"_id": ObjectId(), "preferences": {"category1": 1.0}}
        mock_product = {"_id": ObjectId(), "categories": ["category1", "category2"], "brand": "brand1"}
        mock_event_type = {"_id": ObjectId(), "weight": 1.5}

        mock_db.users.find_one.return_value = mock_user
        mock_db.items.find_one.return_value = mock_product
        mock_db.event_types.find_one.return_value = mock_event_type

        event_data = {
            "user_id": str(mock_user["_id"]),
            "product_id": str(mock_product["_id"]),
            "event_id": str(mock_event_type["_id"]),
        }

        update_user_preferences(event_data)

        self.assertTrue(mock_db.users.update_one.called)
        mock_db.users.update_one.assert_called_once_with(
            {"_id": mock_user["_id"]},
            {"$set": {"preferences": mock_db.users.update_one.call_args[0][1]["$set"]["preferences"]}},
        )

    @patch("core.services.consume.DynamicCollaborativeTrainer")
    def test_update_dynamic_collaborative(self, MockTrainer):
        event_data = {"webshop_id": "12345"}
        mock_trainer = MockTrainer.return_value

        update_dynamic_collaborative(event_data)

        MockTrainer.assert_called_once_with("12345")
        mock_trainer.process_event.assert_called_once_with(event_data)

    @patch("core.services.consume.db")
    @patch("core.services.consume.update_user_preferences")
    @patch("core.services.consume.update_dynamic_collaborative")
    @patch("core.services.consume.process_event_with_trainer")
    def test_process_event(
            self, mock_process_trainer, mock_update_collab, mock_update_prefs, mock_db
    ):
        event_data = {
            "webshop_id": "12345",
            "user_id": str(ObjectId()),
            "product_id": str(ObjectId()),
            "event_id": str(ObjectId()),
            "timestamp": "2023-10-10T10:00:00",
        }

        process_event(event_data)

        self.assertTrue(mock_db.events.insert_one.called)
        mock_update_prefs.assert_called_once_with(event_data)
        mock_update_collab.assert_called_once_with(event_data)
        mock_process_trainer.assert_called_once_with(event_data)

    @patch("core.services.consume.process_event")
    def test_callback(self, mock_process_event):
        event_data = {"webshop_id": "12345"}
        body = json.dumps(event_data).encode()

        ch = MagicMock()
        method = MagicMock()
        properties = MagicMock()

        callback(ch, method, properties, body)

        mock_process_event.assert_called_once_with(event_data)


if __name__ == "__main__":
    unittest.main()
