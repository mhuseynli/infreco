import unittest
from unittest.mock import patch, MagicMock
from bson import ObjectId
from rest_framework.exceptions import ValidationError
from core.serializers.webshop import WebshopSerializer


class TestWebshopSerializer(unittest.TestCase):

    @patch("core.serializers.webshop.db")
    def test_validate_email(self, mock_db):
        mock_db.webshops.find_one.return_value = None  # Simulate no existing webshop with this email
        serializer = WebshopSerializer()
        validated_email = serializer.validate_email("test@example.com")
        self.assertEqual(validated_email, "test@example.com")

        # Test with existing email
        mock_db.webshops.find_one.return_value = {"email": "test@example.com"}
        with self.assertRaises(ValidationError) as context:
            serializer.validate_email("test@example.com")
        self.assertEqual(
            str(context.exception.detail[0]),
            "A user with this email already exists.",
        )

    @patch("core.serializers.webshop.db")
    def test_validate_webshop_name(self, mock_db):
        mock_db.webshops.find_one.return_value = None  # No duplicate names
        serializer = WebshopSerializer()
        validated_name = serializer.validate_webshop_name("Test Webshop")
        self.assertEqual(validated_name, "Test Webshop")

        # Test duplicate name
        mock_db.webshops.find_one.return_value = {"webshop_name": "Test Webshop"}
        with self.assertRaises(ValidationError) as context:
            serializer.validate_webshop_name("Test Webshop")
        self.assertEqual(
            str(context.exception.detail[0]),
            "A webshop with this name already exists.",
        )

    @patch("core.serializers.webshop.db")
    def test_validate_type(self, mock_db):
        mock_db.attributes.find_one.return_value = {"_id": ObjectId(), "type": "retail"}
        serializer = WebshopSerializer()
        validated_type = serializer.validate_type("retail")
        self.assertTrue(ObjectId.is_valid(validated_type))  # Should return a valid ObjectId as string

        # Test invalid type
        mock_db.attributes.find_one.return_value = None
        with self.assertRaises(ValidationError) as context:
            serializer.validate_type("invalid_type")
        self.assertIn("Invalid type: 'invalid_type'", str(context.exception.detail[0]))

    @patch("core.serializers.webshop.db")
    @patch("core.serializers.webshop.bcrypt.hashpw")
    def test_create_webshop(self, mock_hashpw, mock_db):
        # Mock the hashpw function
        mock_hashpw.return_value = b"hashed_password"

        # Mock db.webshops.find_one to simulate no conflicts
        mock_db.webshops.find_one.side_effect = lambda query: None  # No matching email or webshop_name

        # Mock db.attributes.find_one to return a valid type
        mock_db.attributes.find_one.return_value = {"_id": ObjectId(), "type": "retail"}

        # Mock the db.webshops.insert_one method
        mock_db.webshops.insert_one.return_value = MagicMock()

        # Define test data
        data = {
            "email": "test@example.com",
            "password": "password123",
            "webshop_name": "Test Webshop",
            "type": "retail",
        }

        # Initialize the serializer
        serializer = WebshopSerializer(data=data)

        # Validate the data
        serializer.is_valid(raise_exception=True)

        # Save the data
        result = serializer.save()

        # Assertions
        self.assertEqual(result["email"], data["email"])
        self.assertEqual(result["webshop_name"], data["webshop_name"])
        self.assertIn("id", result)  # Check if the unique ID is in the result
        self.assertEqual(result["password"], "hashed_password")
        mock_db.webshops.insert_one.assert_called_once()
