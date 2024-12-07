from bson import ObjectId
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from core.database import db
import bcrypt
import uuid
import hashlib


class WebshopSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, style={"input_type": "password"})
    webshop_name = serializers.CharField()
    contact_person = serializers.CharField(required=False, allow_blank=True)
    contact_phone = serializers.CharField(required=False, allow_blank=True)
    is_verified = serializers.BooleanField(default=False, required=False)
    recommendation_engine = serializers.CharField(default="", required=False)
    engine_parameters = serializers.JSONField(default=dict, required=False)
    api_endpoint = serializers.URLField(default="", required=False)
    type = serializers.CharField(required=True)  # Renamed from `category`

    def generate_unique_id(self, webshop_name):
        random_uuid = uuid.uuid4()
        combined_data = f"{webshop_name}{random_uuid}"
        return hashlib.sha256(combined_data.encode()).hexdigest()[:32]

    def validate_email(self, value):
        if db.webshops.find_one({"email": value}):
            raise ValidationError("A user with this email already exists.")
        return value

    def validate_webshop_name(self, value):
        if db.webshops.find_one({"webshop_name": value}):
            raise ValidationError("A webshop with this name already exists.")
        return value

    def validate_contact_phone(self, value):
        if db.webshops.find_one({"contact_phone": value}):
            raise ValidationError("A webshop with this phone number already exists.")
        return value

    def validate_type(self, value):
        """Validate that the type exists in the predefined attributes."""
        type_exists = db.attributes.find_one({"type": value})
        if not type_exists:
            raise ValidationError(f"Invalid type: '{value}'. Supported types are {self.get_supported_types()}.")
        return str(type_exists["_id"])  # Return the ObjectId as a string for storage

    def get_supported_types(self):
        """Fetch supported types dynamically from the database."""
        types = db.attributes.distinct("type")
        return types

    def create(self, validated_data):
        hashed_password = bcrypt.hashpw(validated_data["password"].encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        unique_id = self.generate_unique_id(validated_data["webshop_name"])
        type_id = ObjectId(validated_data["type"])  # Use the validated type ObjectId

        webshop_data = {
            "id": unique_id,
            "email": validated_data["email"],
            "password": hashed_password,
            "webshop_name": validated_data["webshop_name"],
            "contact_person": validated_data.get("contact_person", ""),
            "contact_phone": validated_data.get("contact_phone", ""),
            "is_verified": validated_data.get("is_verified", False),
            "recommendation_engine": validated_data.get("recommendation_engine", ""),
            "engine_parameters": validated_data.get("engine_parameters", {}),
            "api_endpoint": validated_data.get("api_endpoint", ""),
            "type_id": type_id,  # Store the reference
        }
        db.webshops.insert_one(webshop_data)
        return webshop_data
