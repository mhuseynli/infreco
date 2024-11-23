from bson import ObjectId
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from ..database import db
from datetime import datetime, timezone


class UserSerializer(serializers.Serializer):
    external_id = serializers.CharField(required=True)
    name = serializers.CharField(required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    location = serializers.JSONField(required=False)
    age = serializers.IntegerField(required=False, min_value=0)
    gender = serializers.ChoiceField(choices=["male", "female", "other"], required=False)
    preferences = serializers.JSONField(required=False)
    recent_events = serializers.ListField(
        child=serializers.JSONField(), required=False
    )
    created_at = serializers.DateTimeField(default=datetime.now(timezone.utc))
    updated_at = serializers.DateTimeField(default=datetime.now(timezone.utc))

    def validate_external_id(self, value):
        webshop_id = self.context.get("webshop_id")
        if db.users.find_one({"webshop_id": webshop_id, "external_id": value}):
            raise ValidationError("A user with this external_id already exists in this webshop.")
        return value

    def create(self, validated_data):
        webshop_id = self.context.get("webshop_id")
        user_data = {
            "webshop_id": webshop_id,
            "external_id": validated_data["external_id"],
            "name": validated_data.get("name", ""),
            "email": validated_data.get("email", ""),
            "location": validated_data.get("location", {}),
            "age": validated_data.get("age"),
            "gender": validated_data.get("gender", ""),
            "preferences": validated_data.get("preferences", {}),
            "recent_events": validated_data.get("recent_events", []),
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        db.users.insert_one(user_data)
        return user_data

    def update(self, instance, validated_data):
        webshop_id = self.context.get("webshop_id")
        updates = {
            "name": validated_data.get("name", instance.get("name", "")),
            "email": validated_data.get("email", instance.get("email", "")),
            "location": validated_data.get("location", instance.get("location", {})),
            "age": validated_data.get("age", instance.get("age")),
            "gender": validated_data.get("gender", instance.get("gender", "")),
            "preferences": validated_data.get("preferences", instance.get("preferences", {})),
            "recent_events": validated_data.get("recent_events", instance.get("recent_events", [])),
            "updated_at": datetime.now(timezone.utc),
        }
        db.users.update_one({"_id": ObjectId(instance["_id"])}, {"$set": updates})
        return {**instance, **updates}
