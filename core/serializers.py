from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from .database import db
import bcrypt
import uuid
import hashlib


class WebshopSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    webshop_name = serializers.CharField()
    contact_person = serializers.CharField(required=False, allow_blank=True)
    contact_phone = serializers.CharField(required=False, allow_blank=True)
    is_verified = serializers.BooleanField(default=False, required=False)
    recommendation_engine = serializers.CharField(default="", required=False)
    engine_parameters = serializers.JSONField(default=dict, required=False)
    api_endpoint = serializers.URLField(default="", required=False)

    def generate_unique_id(self, webshop_name):
        # Generate a random UUID
        random_uuid = uuid.uuid4()

        # Combine webshop_name and UUID
        combined_data = f"{webshop_name}{random_uuid}"

        # Hash the combined data for a fixed length and obscure ID
        unique_id = hashlib.sha256(combined_data.encode()).hexdigest()[:32]  # Taking first 32 characters

        return unique_id

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

    def create(self, validated_data):
        hashed_password = bcrypt.hashpw(validated_data['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        unique_id = self.generate_unique_id(validated_data['webshop_name'])
        webshop_data = {
            "id": unique_id,
            "email": validated_data['email'],
            "password": hashed_password,
            "webshop_name": validated_data['webshop_name'],
            "contact_person": validated_data.get('contact_person', ""),
            "contact_phone": validated_data.get('contact_phone', ""),
            "is_verified": validated_data.get('is_verified', False),
            "recommendation_engine": validated_data.get('recommendation_engine', ""),
            "engine_parameters": validated_data.get('engine_parameters', {}),
            "api_endpoint": validated_data.get('api_endpoint', "")
        }
        db.webshops.insert_one(webshop_data)
        return webshop_data


class UserSerializer(serializers.Serializer):
    id = serializers.CharField()
    attributes = serializers.JSONField()

    def create(self, validated_data):
        return validated_data


class ItemSerializer(serializers.Serializer):
    id = serializers.CharField()
    attributes = serializers.JSONField()

    def create(self, validated_data):
        return validated_data


class EventSerializer(serializers.Serializer):
    user = UserSerializer()
    item = ItemSerializer()
    event_type = serializers.CharField()
    timestamp = serializers.DateTimeField()  # This will validate the ISO 8601 format

    def create(self, validated_data):
        return validated_data


