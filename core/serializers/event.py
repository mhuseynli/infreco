from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from bson import ObjectId
from datetime import datetime, timezone
from core.database import db


class EventSerializer(serializers.Serializer):
    user_external_id = serializers.CharField(required=True)
    product_external_id = serializers.CharField(required=True)
    event_name = serializers.CharField(required=True)  # Resolve event by its name
    timestamp = serializers.DateTimeField(default=datetime.now(timezone.utc))

    def validate(self, data):
        webshop_id = self.context.get("webshop_id")
        if not webshop_id:
            raise ValidationError({"detail": "Webshop ID is required."})

        # Resolve user ID
        user = db.users.find_one({"external_id": data["user_external_id"], "webshop_id": webshop_id})
        if not user:
            raise ValidationError({"detail": f"User with external_id '{data['user_external_id']}' not found."})
        data["user_id"] = user["_id"]

        # Resolve product ID
        product = db.items.find_one({"external_id": data["product_external_id"], "webshop_id": webshop_id})
        if not product:
            raise ValidationError({"detail": f"Product with external_id '{data['product_external_id']}' not found."})
        data["product_id"] = product["_id"]

        # Resolve event type by name
        event_type = db.event_types.find_one({"name": data["event_name"]})
        if not event_type:
            raise ValidationError({"detail": f"Event type with name '{data['event_name']}' not found."})
        data["event_id"] = event_type["_id"]

        return data

    def create(self, validated_data):
        # Insert event into the database
        event_data = {
            "user_id": validated_data["user_id"],
            "product_id": validated_data["product_id"],
            "event_id": validated_data["event_id"],
            "timestamp": validated_data["timestamp"],
        }
        db.events.insert_one(event_data)
        return event_data