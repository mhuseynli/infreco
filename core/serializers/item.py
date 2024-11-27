from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from core.database import db
from bson import ObjectId
from datetime import datetime, timezone
from core.utils.logger import get_logger

# Initialize logger
logger = get_logger()

class ItemSerializer(serializers.Serializer):
    external_id = serializers.CharField(required=True)
    name = serializers.CharField(required=True)
    description = serializers.CharField(required=False, allow_blank=True)
    created_at = serializers.DateTimeField(default=datetime.now(timezone.utc))
    updated_at = serializers.DateTimeField(default=datetime.now(timezone.utc))

    def validate(self, data):
        """Dynamic validation based on the webshop's type."""
        logger.info("Starting validation process...")
        logger.info(f"Received serializer data: {data}")

        # Access the raw request data
        raw_data = self.context.get("request").data
        logger.info(f"Received raw data: {raw_data}")

        webshop_id = self.context.get("webshop_id")
        if not webshop_id:
            logger.error("Webshop ID is missing in the context.")
            raise ValidationError({"detail": "Webshop ID is required."})

        # Fetch the webshop and its type
        webshop = db.webshops.find_one({"id": webshop_id})
        if not webshop:
            logger.error(f"Invalid webshop ID: {webshop_id}")
            raise ValidationError({"detail": "Invalid webshop ID."})

        logger.info(f"Webshop found: {webshop}")

        # Fetch the allowed attributes for the webshop type
        type_id = webshop.get("type_id")
        if not type_id:
            logger.error(f"Webshop type is not associated with webshop ID: {webshop_id}")
            raise ValidationError({"detail": "Webshop type is not associated."})

        type_data = db.attributes.find_one({"_id": ObjectId(type_id)})
        if not type_data:
            logger.error(f"Invalid type data for webshop ID: {webshop_id}")
            raise ValidationError({"detail": "Invalid type data for the webshop."})

        logger.info(f"Type data retrieved: {type_data}")

        # Extract dynamic attributes from raw data
        allowed_attributes = {attr["name"]: attr for attr in type_data.get("attributes", [])}
        dynamic_attributes = {key: value for key, value in raw_data.items() if key in allowed_attributes}

        logger.info(f"Extracted dynamic attributes: {dynamic_attributes}")

        # Validate required attributes
        for attr_name, attr_config in allowed_attributes.items():
            if attr_config.get("required", False) and attr_name not in dynamic_attributes:
                logger.error(f"Missing required attribute: {attr_name}")
                raise ValidationError({"non_field_errors": [f"Missing required attribute: {attr_name}."]})

        # Validate attribute data types
        for attr_name, attr_value in dynamic_attributes.items():
            expected_type = allowed_attributes[attr_name].get("data_type")
            if not self._validate_data_type(attr_value, expected_type):
                logger.error(f"Invalid data type for attribute '{attr_name}'. Expected {expected_type}.")
                raise ValidationError(
                    {"non_field_errors": [f"Invalid data type for attribute '{attr_name}'. Expected {expected_type}."]})

        logger.info("All attributes are valid.")

        # Merge dynamic attributes into the validated data
        data.update(dynamic_attributes)
        logger.info("Validation process completed successfully.")
        return data

    def _validate_data_type(self, value, expected_type):
        """Validate the data type of a value."""
        if expected_type == "string" and not isinstance(value, str):
            return False
        if expected_type == "number" and not isinstance(value, (int, float)):
            return False
        if expected_type == "array" and not isinstance(value, list):
            return False
        return True

    def create(self, validated_data):
        """Create a new item, ensuring no duplicates exist."""
        webshop_id = self.context.get("webshop_id")
        item_data = {
            "webshop_id": webshop_id,
            "external_id": validated_data["external_id"],
            "name": validated_data["name"],
            "description": validated_data.get("description", ""),
            **{key: validated_data[key] for key in validated_data if key not in ["external_id", "name", "description"]},
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }

        # Prevent duplicate creation
        existing_item = db.items.find_one({"webshop_id": webshop_id, "external_id": validated_data["external_id"]})
        if existing_item:
            raise ValidationError({"detail": f"An item with external_id '{validated_data['external_id']}' already exists."})

        result = db.items.insert_one(item_data)
        item_data["_id"] = str(result.inserted_id)  # Convert ObjectId to string
        return item_data

    def update(self, validated_data):
        """Update an item using external_id and webshop_id."""
        webshop_id = self.context.get("webshop_id")
        external_id = validated_data.get("external_id")

        # Find the existing item
        existing_item = db.items.find_one({"webshop_id": webshop_id, "external_id": external_id})
        if not existing_item:
            raise ValidationError({"detail": f"Item with external_id '{external_id}' not found."})

        updates = {
            "name": validated_data.get("name", existing_item.get("name")),
            "description": validated_data.get("description", existing_item.get("description")),
            **{key: validated_data[key] for key in validated_data if key not in ["external_id", "name", "description"]},
            "updated_at": datetime.now(timezone.utc),
        }

        db.items.update_one({"webshop_id": webshop_id, "external_id": external_id}, {"$set": updates})
        updated_instance = {**existing_item, **updates}
        updated_instance["_id"] = str(updated_instance["_id"])  # Convert ObjectId to string
        return updated_instance

    def delete(self, external_id):
        """Delete an item using external_id and webshop_id."""
        webshop_id = self.context.get("webshop_id")

        # Find and delete the item
        result = db.items.delete_one({"webshop_id": webshop_id, "external_id": external_id})
        if result.deleted_count == 0:
            raise ValidationError({"detail": f"Item with external_id '{external_id}' not found."})

        return {"message": f"Item with external_id '{external_id}' deleted successfully."}