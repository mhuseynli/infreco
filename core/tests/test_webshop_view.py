import json
from unittest.mock import patch, MagicMock
from rest_framework.test import APITestCase
from rest_framework import status
from bson import ObjectId
from core.views.webshop import RegisterWebshopView, WebshopView
from core import middleware


class TestWebshopView(APITestCase):
    def setUp(self):
        self.api_key = "test_api_key"
        self.headers = {"HTTP_X_API_KEY": self.api_key}  # Correct format for Django test client

    @patch("core.middleware.db")
    @patch("core.views.webshop.db")
    def test_get_webshop_success(self, mock_view_db, mock_middleware_db):
        # Mock middleware database check
        mock_middleware_db.webshops.find_one.return_value = {
            "id": self.api_key,
            "type_id": ObjectId(),
        }

        # Mock view database call
        mock_view_db.webshops.find_one.return_value = {
            "id": self.api_key,
            "email": "test@example.com",
            "webshop_name": "Test Webshop",
            "type_id": ObjectId(),
        }
        mock_view_db.attributes.find_one.return_value = {"type": "Fashion", "attributes": ["attr1", "attr2"]}

        response = self.client.get("/webshops/", **self.headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("allowed_attributes", response.data)
        self.assertEqual(response.data["allowed_attributes"], ["attr1", "attr2"])
        self.assertEqual(response.data["type"], "Fashion")

    @patch("core.middleware.db")
    @patch("core.views.webshop.db")
    def test_get_webshop_not_found(self, mock_view_db, mock_middleware_db):
        # Mock middleware database check for valid API key
        mock_middleware_db.webshops.find_one.return_value = {
            "id": self.api_key,
            "type_id": ObjectId(),
        }

        # Simulate no webshop found in the view
        mock_view_db.webshops.find_one.return_value = None

        response = self.client.get("/webshops/", **self.headers)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("detail", response.data)
        self.assertEqual(response.data["detail"], "Webshop not found.")
